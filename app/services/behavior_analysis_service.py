"""
Behavior Analysis Service - Complete pipeline for video analysis with behavior classification
"""
import cv2
import pandas as pd
import time
from pathlib import Path
from typing import Dict, Optional
import logging

from app.services.behavior_classifier import HorseBehaviorClassifier
from app.config.settings import settings

logger = logging.getLogger(__name__)


class BehaviorAnalysisService:
    """Service for complete video analysis pipeline with behavior classification"""
    
    def __init__(self, config_path: str, results_folder: str):
        """
        Initialize the behavior analysis service
        
        Args:
            config_path: Path to DeepLabCut config file
            results_folder: Folder to store results
        """
        self.config_path = config_path
        self.results_folder = Path(results_folder)
        self.results_folder.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"BehaviorAnalysisService initialized")
        logger.info(f"Config: {config_path}")
        logger.info(f"Results folder: {results_folder}")
    
    def analyze_video_with_behavior(
        self,
        video_path: str,
        show_keypoints: bool = True,
        lying_height_ratio_threshold: float = 0.6,
        eating_height_ratio_threshold: float = 0.8,
        drinking_height_ratio_threshold: float = 0.6,
        movement_threshold: float = 15.0,
        likelihood_threshold: float = 0.5,
        shuffle: int = 2,
        trainingsetindex: int = 0,
        device: str = "cuda:0"
    ) -> Dict:
        """
        Complete pipeline: Analyze video with DLC → Classify behavior → Create output video
        
        Args:
            video_path: Path to input video
            show_keypoints: Whether to show keypoints on output
            lying_height_ratio_threshold: Threshold for lying detection
            eating_height_ratio_threshold: Threshold for eating detection
            drinking_height_ratio_threshold: Threshold for drinking detection
            movement_threshold: Threshold for movement detection
            likelihood_threshold: Minimum keypoint confidence
            shuffle: DeepLabCut shuffle number
            trainingsetindex: DeepLabCut training set index
            device: Device for inference (cuda:0, cpu, etc.)
            
        Returns:
            Dictionary with analysis results and statistics
        """
        start_time = time.time()
        video_path = Path(video_path)
        
        try:
            logger.info(f"Starting behavior analysis pipeline for: {video_path}")
            
            # Step 1: Run DeepLabCut analysis
            logger.info("Step 1/3: Running DeepLabCut pose estimation...")
            csv_path = self._run_deeplabcut_analysis(
                video_path=str(video_path),
                shuffle=shuffle,
                trainingsetindex=trainingsetindex,
                device=device
            )
            
            if not csv_path or not Path(csv_path).exists():
                return {
                    "status": "error",
                    "message": "DeepLabCut analysis failed - no CSV results generated",
                    "video_name": video_path.name,
                    "error_details": "CSV file not found after analysis"
                }
            
            logger.info(f"DeepLabCut analysis complete. Results: {csv_path}")

            # Step 2: Load CSV and classify behaviors
            logger.info("Step 2/3: Classifying behaviors...")
            behavior_data = self._classify_behaviors(
                csv_path=csv_path,
                video_path=str(video_path),
                lying_threshold=lying_height_ratio_threshold,
                eating_threshold=eating_height_ratio_threshold,
                drinking_threshold=drinking_height_ratio_threshold,
                movement_threshold=movement_threshold,
                likelihood_threshold=likelihood_threshold
            )
            
            logger.info(f"Behavior classification complete. Processed {behavior_data['total_frames']} frames")

            # Step 3: Create output video with behavior overlay
            logger.info("Step 3/3: Creating output video with behavior overlay...")
            output_video_path = self._create_behavior_video(
                video_path=str(video_path),
                csv_path=csv_path,
                behavior_data=behavior_data,
                show_keypoints=show_keypoints,
                lying_threshold=lying_height_ratio_threshold,
                eating_threshold=eating_height_ratio_threshold,
                drinking_threshold=drinking_height_ratio_threshold,
                movement_threshold=movement_threshold
            )
            
            if not output_video_path:
                return {
                    "status": "error",
                    "message": "Failed to create output video",
                    "video_name": video_path.name,
                    "csv_path": csv_path
                }

            logger.info(f"Output video created: {output_video_path}")

            # Calculate processing time
            processing_time = time.time() - start_time

            # Build response
            output_filename = Path(output_video_path).name

            return {
                "status": "success",
                "message": "Video analyzed successfully with behavior classification",
                "video_name": video_path.name,
                "output_video_path": output_video_path,
                "download_url": f"/api/v1/analyze/download/{output_filename}",
                "total_frames": behavior_data['total_frames'],
                "frame_height": behavior_data['frame_height'],
                "frame_width": behavior_data['frame_width'],
                "fps": behavior_data['fps'],
                "behavior_statistics": behavior_data['statistics'],
                "average_confidence": behavior_data['average_confidence'],
                "processing_time_seconds": round(processing_time, 2),
                "csv_path": csv_path
            }
            
        except Exception as e:
            logger.error(f"Error in behavior analysis pipeline: {e}", exc_info=True)
            return {
                "status": "error",
                "message": f"Behavior analysis failed: {str(e)}",
                "video_name": video_path.name,
                "error_details": str(e)
            }
    
    def _run_deeplabcut_analysis(
        self,
        video_path: str,
        shuffle: int,
        trainingsetindex: int,
        device: str
    ) -> Optional[str]:
        """
        Run DeepLabCut analysis on video
        
        Returns:
            Path to CSV results file
        """
        try:
            import deeplabcut
            
            # Run analysis with reduced batch size to prevent queue overflow
            deeplabcut.analyze_videos(
                self.config_path,
                [video_path],
                shuffle=shuffle,
                trainingsetindex=trainingsetindex,
                save_as_csv=True,
                destfolder=str(self.results_folder),
                device=device,
                batchsize=4  # Reduced from default 8 to prevent queue.Full error
            )
            
            # Find the CSV file
            video_name = Path(video_path).stem
            csv_files = list(self.results_folder.glob(f"{video_name}*.csv"))
            
            if csv_files:
                return str(csv_files[0])
            
            return None
            
        except Exception as e:
            logger.error(f"DeepLabCut analysis error: {e}")
            raise
    
    def _classify_behaviors(
        self,
        csv_path: str,
        video_path: str,
        lying_threshold: float,
        eating_threshold: float,
        drinking_threshold: float,
        movement_threshold: float,
        likelihood_threshold: float
    ) -> Dict:
        """
        Load CSV results and classify behaviors for each frame
        
        Returns:
            Dictionary with behaviors, confidences, and statistics
        """
        # Load CSV
        df = pd.read_csv(csv_path, header=[0, 1, 2], index_col=0)
        scorer = df.columns.levels[0][0]
        keypoint_names = list(df[scorer].columns.levels[0])
        
        # Get video properties
        cap = cv2.VideoCapture(video_path)
        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps <= 0 or fps > 120:
            fps = 30.0
        cap.release()
        
        # Initialize classifier
        classifier = HorseBehaviorClassifier(
            lying_height_ratio_threshold=lying_threshold,
            eating_height_ratio_threshold=eating_threshold,
            drinking_height_ratio_threshold=drinking_threshold,
            movement_threshold=movement_threshold,
            likelihood_threshold=likelihood_threshold
        )
        
        # Classify each frame
        behaviors = []
        confidences = []
        prev_keypoints = None
        
        for frame_idx in range(len(df)):
            # Extract keypoints
            current_keypoints = {}
            row = df.iloc[frame_idx]
            
            for keypoint_name in keypoint_names:
                try:
                    x = row[(scorer, keypoint_name, 'x')]
                    y = row[(scorer, keypoint_name, 'y')]
                    likelihood = row[(scorer, keypoint_name, 'likelihood')]
                    current_keypoints[keypoint_name] = (float(x), float(y), float(likelihood))
                except KeyError:
                    continue
            
            # Classify
            behavior = classifier.classify_behavior(
                current_keypoints,
                prev_keypoints,
                frame_height
            )
            confidence = classifier.get_behavior_confidence(current_keypoints)
            
            behaviors.append(behavior)
            confidences.append(confidence)
            prev_keypoints = current_keypoints
        
        # Calculate statistics
        total_frames = len(behaviors)
        behavior_stats = {}
        
        for behavior_type in ["Standing", "Moving", "Lying Down", "Eating", "Drinking", "Unknown"]:
            count = behaviors.count(behavior_type)
            percentage = (count / total_frames * 100) if total_frames > 0 else 0
            behavior_stats[behavior_type] = {
                "frames": count,
                "percentage": round(percentage, 2)
            }
        
        return {
            "behaviors": behaviors,
            "confidences": confidences,
            "statistics": behavior_stats,
            "average_confidence": round(sum(confidences) / len(confidences), 4) if confidences else 0,
            "total_frames": total_frames,
            "frame_height": frame_height,
            "frame_width": frame_width,
            "fps": fps,
            "scorer": scorer,
            "keypoint_names": keypoint_names,
            "df": df
        }
    
    def _create_behavior_video(
        self,
        video_path: str,
        csv_path: str,
        behavior_data: Dict,
        show_keypoints: bool,
        lying_threshold: float,
        eating_threshold: float,
        drinking_threshold: float,
        movement_threshold: float
    ) -> Optional[str]:
        """
        Create output video with behavior overlay using the existing visualize_behavior module
        
        Args:
            video_path: Path to input video
            csv_path: Path to CSV results
            behavior_data: Dictionary with behaviors, confidences, and statistics
            show_keypoints: Whether to show keypoints
            lying_threshold: Threshold for lying detection
            eating_threshold: Threshold for eating detection
            drinking_threshold: Threshold for drinking detection
            movement_threshold: Threshold for movement detection
            
        Returns:
            Path to output video
        """
        try:
            # Import the processor
            import sys
            from pathlib import Path
            
            # Add app directory to path if needed
            app_root = Path(__file__).parent.parent.parent
            if str(app_root) not in sys.path:
                sys.path.insert(0, str(app_root))
            
            from ml_scripts.visualize_behavior import BehaviorVideoProcessor
            
            # Create processor
            processor = BehaviorVideoProcessor(csv_path)
            
            # Output path
            video_name = Path(video_path).stem
            output_path = str(self.results_folder / f"{video_name}_behavior.mp4")
            
            # Process video (no display in API mode). Pass precomputed behaviors and confidences
            # so the visualizer uses the exact labels produced during classification.
            behaviors = behavior_data.get('behaviors')
            confidences = behavior_data.get('confidences')
            
            # Debug logging to trace behavior passing
            logger.info(f"DEBUG: Passing {len(behaviors) if behaviors else 0} precomputed behaviors to renderer")
            if behaviors:
                # Count each behavior type
                from collections import Counter
                behavior_counts = Counter(behaviors)
                logger.info(f"DEBUG: Behavior breakdown being passed: {dict(behavior_counts)}")

            processor.process_video(
                video_path=video_path,
                output_path=output_path,
                show_keypoints=show_keypoints,
                display=False,
                behaviors=behaviors,
                confidences=confidences,
                lying_threshold=lying_threshold,
                eating_threshold=eating_threshold,
                drinking_threshold=drinking_threshold,
                movement_threshold=movement_threshold
            )
            
            return output_path
            
        except Exception as e:
            logger.error(f"Error creating behavior video: {e}", exc_info=True)
            return None

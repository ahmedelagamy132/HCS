"""
Horse Behavior Visualization from DeepLabCut CSV Results
Processes already analyzed videos and adds behavior classification overlay
"""
import cv2
import numpy as np
import pandas as pd
from pathlib import Path
import argparse
import sys
import os
from typing import Dict, Tuple

# Suppress OpenCV codec error messages
os.environ['OPENCV_FFMPEG_LOGLEVEL'] = '-8'
os.environ['OPENCV_LOG_LEVEL'] = 'ERROR'

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.behavior_classifier import HorseBehaviorClassifier


class BehaviorVideoProcessor:
    """Process videos with pre-computed DeepLabCut results"""
    
    # Behavior colors (BGR format for OpenCV)
    BEHAVIOR_COLORS = {
        "Standing": (0, 255, 0),         # Green
        "Moving": (255, 165, 0),         # Orange
        "Lying Down": (0, 0, 255),       # Red
        "Eating": (0, 255, 255),         # Yellow
        "Drinking": (255, 255, 0),       # Cyan
        "Unknown": (128, 128, 128)       # Gray
    }
    
    def __init__(self, csv_path: str):
        """
        Initialize processor with DLC CSV results
        
        Args:
            csv_path: Path to DeepLabCut CSV file
        """
        self.csv_path = csv_path
        self.df = None
        self.keypoint_names = []
        self.scorer = None
        self._load_csv()
        
    def _load_csv(self):
        """Load and parse DeepLabCut CSV file"""
        print(f"Loading CSV: {self.csv_path}")
        
        # Read CSV with multi-level headers
        self.df = pd.read_csv(self.csv_path, header=[0, 1, 2], index_col=0)
        
        # Get scorer name and keypoints
        self.scorer = self.df.columns.levels[0][0]
        self.keypoint_names = list(self.df[self.scorer].columns.levels[0])
        
        print(f"Loaded {len(self.df)} frames")
        print(f"Scorer: {self.scorer}")
        print(f"Keypoints: {self.keypoint_names}")
    
    def get_keypoints_for_frame(self, frame_idx: int) -> Dict[str, Tuple[float, float, float]]:
        """
        Extract keypoints for a specific frame
        
        Args:
            frame_idx: Frame index (0-based)
            
        Returns:
            Dictionary {keypoint_name: (x, y, likelihood)}
        """
        if frame_idx >= len(self.df):
            return {}
        
        keypoints = {}
        row = self.df.iloc[frame_idx]
        
        for keypoint_name in self.keypoint_names:
            try:
                x = row[(self.scorer, keypoint_name, 'x')]
                y = row[(self.scorer, keypoint_name, 'y')]
                likelihood = row[(self.scorer, keypoint_name, 'likelihood')]
                
                keypoints[keypoint_name] = (float(x), float(y), float(likelihood))
            except KeyError:
                continue
        
        return keypoints
    
    def draw_overlay(
        self,
        frame: np.ndarray,
        behavior: str,
        confidence: float,
        frame_number: int,
        total_frames: int,
        fps: float = 30.0,
        show_keypoints: bool = True,
        keypoints: Dict = None
    ) -> np.ndarray:
        """
        Draw behavior overlay and keypoints on frame
        
        Args:
            frame: Video frame
            behavior: Classified behavior
            confidence: Classification confidence
            frame_number: Current frame number
            total_frames: Total number of frames
            fps: Frames per second of the video
            show_keypoints: Whether to draw keypoints
            keypoints: Dictionary of keypoints
            
        Returns:
            Frame with overlay
        """
        height, width = frame.shape[:2]
        output_frame = frame.copy()
        
        # Draw keypoints if requested
        if show_keypoints and keypoints:
            for keypoint_name, (x, y, likelihood) in keypoints.items():
                if likelihood > 0.5:
                    color_intensity = int(255 * likelihood)
                    color = (0, color_intensity, 255)
                    cv2.circle(output_frame, (int(x), int(y)), 4, color, -1)
        
        # Create overlay panel. Ensure panel height does not exceed frame height.
        panel_height = min(140, height)
        panel = np.zeros((panel_height, width, 3), dtype=np.uint8)
        panel[:] = (40, 40, 40)

        # Colored top bar
        color = self.BEHAVIOR_COLORS.get(behavior, (255, 255, 255))
        cv2.rectangle(panel, (0, 0), (width, 12), color, -1)

        # Compute text positions relative to panel height so the overlay adapts to small frames
        y_behavior = int(panel_height * 0.35)
        y_conf = int(panel_height * 0.62)
        y_frame = int(panel_height * 0.9)

        # Behavior text (large)
        cv2.putText(
            panel,
            f"Behavior: {behavior}",
            (20, max(20, y_behavior)),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.0 if panel_height >= 80 else 0.7,
            color,
            2 if panel_height >= 80 else 1,
            cv2.LINE_AA
        )

        # Confidence
        cv2.putText(
            panel,
            f"Confidence: {confidence:.1%}",
            (20, max(30, y_conf)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7 if panel_height >= 80 else 0.55,
            (255, 255, 255),
            1,
            cv2.LINE_AA
        )

        # Frame counter
        cv2.putText(
            panel,
            f"Frame: {frame_number}/{total_frames}",
            (20, max(40, y_frame)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6 if panel_height >= 80 else 0.45,
            (200, 200, 200),
            1,
            cv2.LINE_AA
        )

        # Timestamp
        timestamp = f"{frame_number/fps:.2f}s"
        ts_x = max(width - 150, width - 120)
        cv2.putText(
            panel,
            timestamp,
            (ts_x, max(40, y_frame)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6 if panel_height >= 80 else 0.45,
            (200, 200, 200),
            1,
            cv2.LINE_AA
        )

        # Blend panel with frame
        output_frame[0:panel_height] = cv2.addWeighted(
            output_frame[0:panel_height],
            0.25,
            panel,
            0.75,
            0
        )

        return output_frame
    
    def process_video(
        self,
        video_path: str,
        output_path: str = None,
        show_keypoints: bool = True,
        display: bool = True,
        behaviors: list = None,
        confidences: list = None,
        lying_threshold: float = 0.6,
        eating_threshold: float = 0.8,
        drinking_threshold: float = 0.6,
        movement_threshold: float = 15.0
    ):
        """
        Process video and add behavior classification
        
        Args:
            video_path: Path to input video
            output_path: Path to save output video
            show_keypoints: Whether to visualize keypoints
            display: Whether to display video window
            behaviors: Optional precomputed behavior labels per frame
            confidences: Optional precomputed confidence scores per frame
            lying_threshold: Threshold for lying detection (default: 0.6)
            eating_threshold: Threshold for eating detection (default: 0.8)
            drinking_threshold: Threshold for drinking detection (default: 0.6)
            movement_threshold: Threshold for movement detection (default: 15.0)
        """
        print(f"\nProcessing video: {video_path}")
        
        # Open video
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print(f"ERROR: Could not open video: {video_path}")
            return
        
        # Get video properties
        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)  # Keep as float for accuracy
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # Handle invalid FPS values
        if fps <= 0 or fps > 120:
            print(f"⚠️  Warning: Invalid FPS detected ({fps}), using default 30 FPS")
            fps = 30.0
        
        print(f"Video: {frame_width}x{frame_height} @ {fps:.2f} FPS, {total_frames} frames")
        
        # Setup output video with browser-compatible codec
        if output_path is None:
            output_path = str(Path(video_path).parent / f"{Path(video_path).stem}_behavior.mp4")
        
        # Try multiple codecs in order of browser compatibility
        codecs_to_try = [
            ('X264', 'H.264 (X264) - Best browser compatibility'),
            ('H264', 'H.264 (H264) - Good browser compatibility'),
            ('avc1', 'H.264 (avc1) - Good browser compatibility'),
            ('XVID', 'XVID - Good compatibility'),
            ('mp4v', 'MPEG-4 - Fallback option')
        ]
        
        out = None
        codec_used = None
        
        for codec, description in codecs_to_try:
            try:
                fourcc = cv2.VideoWriter_fourcc(*codec)
                test_out = cv2.VideoWriter(output_path, fourcc, fps, (frame_width, frame_height))
                
                if test_out.isOpened():
                    out = test_out
                    codec_used = codec
                    print(f"✓ Using {description}")
                    break
                else:
                    test_out.release()
            except Exception:
                pass
        
        if out is None or not out.isOpened():
            raise RuntimeError("Failed to initialize video writer with any codec. Install ffmpeg or x264 codec.")
        
        # Initialize classifier with CUSTOM thresholds (passed from API)
        classifier = HorseBehaviorClassifier(
            lying_height_ratio_threshold=lying_threshold,
            eating_height_ratio_threshold=eating_threshold,
            drinking_height_ratio_threshold=drinking_threshold,
            movement_threshold=movement_threshold,
            likelihood_threshold=0.5
        )
        
        # Process frames
        frame_idx = 0
        prev_keypoints = None
        behavior_stats = {"Standing": 0, "Moving": 0, "Lying Down": 0, "Eating": 0, "Drinking": 0, "Unknown": 0}
        
        # Debug: confirm if precomputed behaviors were provided
        if behaviors is not None:
            print(f"\n🔍 DEBUG: Using {len(behaviors)} precomputed behaviors from classifier")
        else:
            print(f"\n⚠️  DEBUG: No precomputed behaviors provided, will classify on-the-fly with hardcoded thresholds")
        
        print("\nProcessing frames... Press 'q' to quit")
        print("-" * 60)
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Get keypoints for this frame
            current_keypoints = self.get_keypoints_for_frame(frame_idx)

            # If the caller provided precomputed behaviors/confidences, use them to ensure
            # the overlay matches the analysis results. Otherwise classify on-the-fly.
            if behaviors is not None and frame_idx < len(behaviors):
                behavior = behaviors[frame_idx]
                confidence = confidences[frame_idx] if confidences and frame_idx < len(confidences) else 0.0
                
                # Debug: log first 5 frames to verify behavior passing
                if frame_idx < 5:
                    print(f"  DEBUG Frame {frame_idx}: Using precomputed behavior='{behavior}', confidence={confidence:.3f}")

                # Update statistics
                if behavior in behavior_stats:
                    behavior_stats[behavior] += 1
                else:
                    behavior_stats.setdefault(behavior, 0)
                    behavior_stats[behavior] += 1

                # Draw overlay (use keypoints if available)
                output_frame = self.draw_overlay(
                    frame,
                    behavior,
                    confidence,
                    frame_idx + 1,
                    total_frames,
                    fps,
                    show_keypoints,
                    current_keypoints if current_keypoints else None
                )
                prev_keypoints = current_keypoints
            else:
                if current_keypoints:
                    # Classify behavior on-the-fly if no precomputed labels were supplied
                    behavior = classifier.classify_behavior(
                        current_keypoints,
                        prev_keypoints,
                        frame_height
                    )
                    confidence = classifier.get_behavior_confidence(current_keypoints)

                    # Update statistics
                    behavior_stats[behavior] += 1

                    # Draw overlay
                    output_frame = self.draw_overlay(
                        frame,
                        behavior,
                        confidence,
                        frame_idx + 1,
                        total_frames,
                        fps,
                        show_keypoints,
                        current_keypoints
                    )

                    prev_keypoints = current_keypoints
                else:
                    output_frame = frame
            
            # Write frame
            out.write(output_frame)
            
            # Display frame
            if display:
                cv2.imshow('Horse Behavior Analysis', output_frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    print("\nStopping...")
                    break
            
            # Progress update
            if (frame_idx + 1) % 30 == 0:
                progress = ((frame_idx + 1) / total_frames) * 100
                print(f"Progress: {progress:.1f}% | Frame {frame_idx + 1}/{total_frames}")
            
            frame_idx += 1
        
        # Cleanup
        cap.release()
        out.release()
        cv2.destroyAllWindows()
        
        # Print statistics
        print("\n" + "=" * 60)
        print("BEHAVIOR STATISTICS")
        print("=" * 60)
        total_classified = sum(behavior_stats.values())
        for behavior, count in sorted(behavior_stats.items(), key=lambda x: x[1], reverse=True):
            if count > 0:
                percentage = (count / total_classified) * 100
                print(f"{behavior:20s}: {count:5d} frames ({percentage:5.1f}%)")
        print("=" * 60)
        print(f"\nOutput saved to: {output_path}")
        print("=" * 60)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Add behavior classification to DeepLabCut analyzed videos"
    )
    parser.add_argument(
        "--video",
        type=str,
        required=True,
        help="Path to input video file"
    )
    parser.add_argument(
        "--csv",
        type=str,
        required=True,
        help="Path to DeepLabCut CSV results file"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Path to save output video (default: input_behavior.mp4)"
    )
    parser.add_argument(
        "--no-keypoints",
        action="store_true",
        help="Don't draw keypoints on video"
    )
    parser.add_argument(
        "--no-display",
        action="store_true",
        help="Don't display video window"
    )
    
    args = parser.parse_args()
    
    # Validate paths
    if not Path(args.video).exists():
        print(f"ERROR: Video file not found: {args.video}")
        sys.exit(1)
    
    if not Path(args.csv).exists():
        print(f"ERROR: CSV file not found: {args.csv}")
        sys.exit(1)
    
    # Process video
    processor = BehaviorVideoProcessor(args.csv)
    processor.process_video(
        video_path=args.video,
        output_path=args.output,
        show_keypoints=not args.no_keypoints,
        display=not args.no_display
    )


if __name__ == "__main__":
    main()

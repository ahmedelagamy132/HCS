"""
VLM Service - Wrapper for HorseStateClassifier with lazy loading
"""
import time
import os
import csv
import cv2
from pathlib import Path
from typing import Dict, List, Optional
import logging

from app.services.horse_state_classifier import HorseStateClassifier

from app.config.settings import settings
logger = logging.getLogger(__name__)


class VlmService:
    """Service for VLM-based horse state classification with lazy loading"""

    def __init__(self):
        self._classifiers = {}
        logger.info("VlmService initialized (models will be loaded on demand)")

    def _get_classifier(self, model_name: str) -> HorseStateClassifier:
        if model_name not in self._classifiers:
            logger.info(f"Loading VLM model: {model_name}")
            self._classifiers[model_name] = HorseStateClassifier(
                model=model_name,
                enable_visualization=False,
                enable_metrics=False,
                keep_alive_duration="30m"
            )
            self._classifiers[model_name].warm_up()
            logger.info(f"VLM model {model_name} loaded and warmed up")

        return self._classifiers[model_name]

    def classify_video(
        self,
        video_path: str,
        output_folder: str,
        model_name: str = settings.DEFAULT_VLM_VIDEO_MODEL,
        frame_interval: int = 1,
        resize: Optional[int] = 412,
        create_annotated_video: bool = True
    ) -> Dict:
        start_time = time.time()
        video_path = Path(video_path)
        output_folder = Path(output_folder)
        output_folder.mkdir(parents=True, exist_ok=True)

        try:
            logger.info(f"Starting VLM classification for: {video_path}")
            logger.info(f"Model: {model_name}, Frame interval: {frame_interval}, Resize: {resize}")

            classifier = self._get_classifier(model_name)

            csv_name = f"{video_path.stem}_vlm_results.csv"
            csv_path = output_folder / csv_name

            output_video_path = None
            output_video_name = None
            if create_annotated_video:
                output_video_name = f"{video_path.stem}_vlm_annotated.mp4"
                output_video_path = output_folder / output_video_name

            results = classifier.process_video(
                video_path=str(video_path),
                frame_interval=frame_interval,
                auto_warmup=False,
                show_visualization=False,
                save_annotated_video=create_annotated_video,
                output_video_path=str(output_video_path) if output_video_path else None,
                resize=resize,
                output_csv=str(csv_path)
            )

            processing_time = time.time() - start_time

            statistics = self._calculate_statistics(results)

            classifications = [
                {
                    "frame_number": r["frame"],
                    "timestamp": r["timestamp_sec"],
                    "state": r["state"],
                    "raw_response": r["state"],
                    "inference_ms": r["inference_ms"]
                }
                for r in results
            ]

            inference_times = [r["inference_ms"] for r in results]
            avg_inference_ms = sum(inference_times) / len(inference_times) if inference_times else 0

            logger.info(f"VLM classification complete in {processing_time:.2f}s")

            return {
                "status": "success",
                "message": f"Video processed successfully with {len(results)} frames analyzed",
                "video_name": video_path.name,
                "output_csv_path": str(csv_path),
                "csv_name": csv_name,
                "output_video_path": str(output_video_path) if output_video_path else None,
                "output_video_name": output_video_name,
                "total_frames_analyzed": len(results),
                "frame_interval": frame_interval,
                "processing_time": round(processing_time, 2),
                "average_inference_ms": round(avg_inference_ms, 1),
                "model_info": {
                    "model_name": model_name,
                    "keep_alive": "30m",
                    "resize": resize
                },
                "statistics": statistics,
                "classifications": classifications
            }

        except Exception as e:
            logger.error(f"VLM classification failed: {e}", exc_info=True)
            return {
                "status": "error",
                "message": f"Classification failed: {str(e)}",
                "video_name": video_path.name,
                "error_details": str(e)
            }

    def classify_image(
        self,
        image_path: str,
        output_folder: Optional[str] = None,
        model_name: str = settings.DEFAULT_VLM_IMAGE_MODEL,
        resize: Optional[int] = None,
        create_annotated_image: bool = True
    ) -> Dict:
        try:
            logger.info(f"Classifying image: {image_path} with model: {model_name}")

            classifier = self._get_classifier(model_name)

            result = classifier.predict(
                image_path=image_path,
                auto_warmup=False,
                show_visualization=False,
                show_metrics=False,
                resize=resize
            )

            logger.info(f"Image classified as: {result['state']}")

            output_image_path = None
            output_image_name = None
            if create_annotated_image and output_folder:
                try:
                    import cv2 as _cv2
                    output_folder_path = Path(output_folder)
                    output_folder_path.mkdir(parents=True, exist_ok=True)

                    output_image_name = f"{Path(image_path).stem}_vlm_annotated{Path(image_path).suffix}"
                    output_image_path = output_folder_path / output_image_name

                    img = _cv2.imread(image_path)
                    if img is not None:
                        classifier._add_annotation_to_frame(
                            img,
                            result["state"],
                            0,
                            result.get("inference_only_ms", result.get("wall_time_ms", 0))
                        )
                        _cv2.imwrite(str(output_image_path), img)
                        logger.info(f"Annotated image saved: {output_image_path}")
                    else:
                        output_image_path = None
                        output_image_name = None

                except Exception as e:
                    logger.error(f"Failed to create annotated image: {e}")
                    output_image_path = None
                    output_image_name = None

            return {
                "status": "success",
                "message": f"Image classified successfully as '{result['state']}'",
                "image_name": Path(image_path).name,
                "output_image_path": str(output_image_path) if output_image_path else None,
                "output_image_name": output_image_name,
                "state": result["state"],
                "raw_response": result.get("raw_response", result["state"]),
                "inference_ms": result.get("inference_only_ms", result.get("wall_time_ms", 0)),
                "model_info": {
                    "model_name": model_name,
                    "keep_alive": "30m",
                    "resize": resize
                }
            }

        except Exception as e:
            logger.error(f"Image classification failed: {e}", exc_info=True)
            return {
                "status": "error",
                "message": f"Classification failed: {str(e)}",
                "image_name": Path(image_path).name,
                "error_details": str(e)
            }

    def _calculate_statistics(self, results: List[Dict]) -> Dict:
        if not results:
            return {
                "total_frames_analyzed": 0,
                "state_counts": {},
                "state_percentages": {},
                "most_common_state": "unknown",
                "state_transitions": 0
            }

        state_counts = {}
        for r in results:
            state = r["state"]
            state_counts[state] = state_counts.get(state, 0) + 1

        total = len(results)
        state_percentages = {
            state: round((count / total) * 100, 1)
            for state, count in state_counts.items()
        }

        most_common_state = max(state_counts.items(), key=lambda x: x[1])[0]

        transitions = 0
        for i in range(1, len(results)):
            if results[i]["state"] != results[i-1]["state"]:
                transitions += 1

        return {
            "total_frames_analyzed": total,
            "state_counts": state_counts,
            "state_percentages": state_percentages,
            "most_common_state": most_common_state,
            "state_transitions": transitions
        }


_vlm_service_instance = None

def get_vlm_service() -> VlmService:
    """Get or create VLM service instance (singleton pattern)"""
    global _vlm_service_instance
    if _vlm_service_instance is None:
        _vlm_service_instance = VlmService()
    return _vlm_service_instance

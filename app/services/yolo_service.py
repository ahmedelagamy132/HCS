"""
YOLO Detection Service - Horse detection and video annotation using YOLOv8
"""
import cv2
import time
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging
import numpy as np

from app.config.settings import settings

logger = logging.getLogger(__name__)


class YoloDetectionService:
    """Service for YOLO-based horse detection in videos"""

    def __init__(self, model_path: str = None):
        if model_path is None:
            model_path = settings.YOLO_MODEL_PATH

        self.model_path = Path(model_path)
        self._model = None

        logger.info(f"YoloDetectionService initialized with model: {self.model_path}")

    def _load_model(self):
        """Lazy load YOLO model (only when first needed)"""
        if self._model is None:
            try:
                from ultralytics import YOLO
                logger.info(f"Loading YOLO model from: {self.model_path}")

                if not self.model_path.exists():
                    raise FileNotFoundError(f"YOLO model not found at: {self.model_path}")

                self._model = YOLO(str(self.model_path))
                logger.info("YOLO model loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load YOLO model: {e}")
                raise

        return self._model

    def _create_video_writer(
        self,
        output_path: str,
        fps: float,
        frame_size: Tuple[int, int]
    ) -> cv2.VideoWriter:
        codecs = [
            ('avc1', cv2.VideoWriter_fourcc(*'avc1')),
            ('XVID', cv2.VideoWriter_fourcc(*'XVID')),
            ('mp4v', cv2.VideoWriter_fourcc(*'mp4v'))
        ]

        import sys

        for codec_name, fourcc in codecs:
            if os.name == 'nt':
                stderr_fileno = sys.stderr.fileno()
                old_stderr = os.dup(stderr_fileno)
                devnull = os.open(os.devnull, os.O_WRONLY)
                os.dup2(devnull, stderr_fileno)
                os.close(devnull)

            try:
                writer = cv2.VideoWriter(output_path, fourcc, fps, frame_size)

                if os.name == 'nt':
                    os.dup2(old_stderr, stderr_fileno)
                    os.close(old_stderr)

                if writer.isOpened():
                    logger.info(f"Video writer created with {codec_name} codec")
                    return writer
                else:
                    logger.debug(f"Codec {codec_name} not available, trying next...")
            except Exception as e:
                if os.name == 'nt':
                    try:
                        os.dup2(old_stderr, stderr_fileno)
                        os.close(old_stderr)
                    except OSError:
                        pass
                logger.debug(f"Error with {codec_name}: {e}")
                continue

        raise RuntimeError(f"Could not create video writer with any codec for {output_path}")

    def detect_horses_in_video(
        self,
        video_path: str,
        output_folder: str,
        confidence_threshold: float = 0.7,
        iou_threshold: float = 0.45,
        show_labels: bool = True,
        show_conf: bool = True,
        line_thickness: int = 2
    ) -> Dict:
        start_time = time.time()
        video_path = Path(video_path)
        output_folder = Path(output_folder)
        output_folder.mkdir(parents=True, exist_ok=True)

        try:
            logger.info(f"Starting YOLO detection for: {video_path}")

            model = self._load_model()

            cap = cv2.VideoCapture(str(video_path))
            if not cap.isOpened():
                raise ValueError(f"Could not open video: {video_path}")

            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

            logger.info(f"Video properties: {total_frames} frames, {fps} fps, {width}x{height}")

            output_name = f"{video_path.stem}_yolo_annotated.mp4"
            output_path = output_folder / output_name

            out = self._create_video_writer(
                output_path=str(output_path),
                fps=fps,
                frame_size=(width, height)
            )

            total_detections = 0
            frames_with_detections = 0
            frames_without_detections = 0
            max_horses_per_frame = 0
            sum_confidence = 0.0
            detections_per_frame = []

            frame_count = 0
            logger.info("Processing frames...")

            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                frame_count += 1

                results = model.predict(
                    source=frame,
                    conf=confidence_threshold,
                    iou=iou_threshold,
                    verbose=False
                )

                frame_detections = 0
                annotated_frame = frame.copy()

                if len(results) > 0 and results[0].boxes is not None:
                    boxes = results[0].boxes

                    for box in boxes:
                        frame_detections += 1
                        total_detections += 1

                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
                        conf = float(box.conf[0].cpu().numpy())
                        sum_confidence += conf

                        cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 255, 0), line_thickness)

                        if show_labels or show_conf:
                            label_parts = []
                            if show_labels:
                                label_parts.append("horse")
                            if show_conf:
                                label_parts.append(f"{conf:.2f}")

                            label = " ".join(label_parts)

                            (text_width, text_height), baseline = cv2.getTextSize(
                                label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1
                            )

                            cv2.rectangle(
                                annotated_frame,
                                (x1, y1 - text_height - baseline - 5),
                                (x1 + text_width, y1),
                                (0, 255, 0),
                                -1
                            )

                            cv2.putText(
                                annotated_frame, label, (x1, y1 - baseline - 2),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1
                            )

                detections_per_frame.append(frame_detections)
                if frame_detections > 0:
                    frames_with_detections += 1
                    max_horses_per_frame = max(max_horses_per_frame, frame_detections)
                else:
                    frames_without_detections += 1

                out.write(annotated_frame)

                if frame_count % 30 == 0:
                    progress = (frame_count / total_frames) * 100 if total_frames > 0 else 0
                    logger.info(f"Progress: {progress:.1f}% ({frame_count}/{total_frames} frames)")

            cap.release()
            out.release()

            processing_time = time.time() - start_time

            avg_confidence = sum_confidence / total_detections if total_detections > 0 else 0.0
            avg_horses_per_frame = total_detections / total_frames if total_frames > 0 else 0.0
            avg_horses_per_detection_frame = (
                total_detections / frames_with_detections
                if frames_with_detections > 0 else 0.0
            )

            logger.info(f"YOLO detection complete in {processing_time:.2f}s")

            return {
                "status": "success",
                "message": f"Video processed successfully with {total_detections} horse detections",
                "video_name": video_path.name,
                "output_video_path": str(output_path),
                "output_video_name": output_name,
                "total_detections": total_detections,
                "detection_statistics": {
                    "total_frames": total_frames,
                    "frames_with_detections": frames_with_detections,
                    "frames_without_detections": frames_without_detections,
                    "max_horses_per_frame": max_horses_per_frame,
                    "avg_horses_per_frame": round(avg_horses_per_frame, 2),
                    "avg_horses_per_detection_frame": round(avg_horses_per_detection_frame, 2)
                },
                "average_confidence": round(avg_confidence, 3),
                "processing_time": round(processing_time, 2),
                "model_info": {
                    "model_name": "YOLOv8",
                    "model_path": str(self.model_path),
                    "confidence_threshold": confidence_threshold,
                    "iou_threshold": iou_threshold
                }
            }

        except Exception as e:
            logger.error(f"YOLO detection failed: {e}", exc_info=True)
            return {
                "status": "error",
                "message": f"Detection failed: {str(e)}",
                "video_name": video_path.name,
                "error_details": str(e)
            }

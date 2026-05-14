"""
YOLO Router - API endpoints for YOLO horse detection
"""
from fastapi import APIRouter, HTTPException, File, UploadFile, Form
from fastapi.responses import FileResponse
from typing import Optional
from pathlib import Path
import shutil
import logging
import os

from app.schemas.yolo import (
    YoloDetectionRequest,
    YoloDetectionResponse
)
from app.services.yolo_service import YoloDetectionService
from app.config.settings import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/yolo", tags=["yolo"])

yolo_service = YoloDetectionService()

# Determine upload/output base directory relative to project root
_BASE_DIR = Path(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
_VIDEOS_BASE = _BASE_DIR / (settings.VIDEOS_FOLDER if settings.VIDEOS_FOLDER else "data/videos")


@router.post("/detect", response_model=YoloDetectionResponse)
async def detect_horses(
    video: UploadFile = File(..., description="Video file to analyze"),
    confidence_threshold: float = Form(0.7, description="Confidence threshold (0.0-1.0)"),
    iou_threshold: float = Form(0.45, description="IoU threshold for NMS (0.0-1.0)"),
    show_labels: bool = Form(True, description="Show class labels on bounding boxes"),
    show_conf: bool = Form(True, description="Show confidence scores on bounding boxes"),
    line_thickness: int = Form(2, description="Thickness of bounding box lines (1-10)")
):
    """Detect horses in uploaded video using YOLOv8"""
    try:
        logger.info(f"Received YOLO detection request for video: {video.filename}")

        allowed_extensions = ['.mp4', '.avi', '.mov', '.mkv']
        file_ext = Path(video.filename).suffix.lower()

        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file format. Allowed: {', '.join(allowed_extensions)}"
            )

        uploads_folder = _VIDEOS_BASE / "yolo_uploads"
        uploads_folder.mkdir(parents=True, exist_ok=True)

        video_path = uploads_folder / video.filename
        with open(video_path, "wb") as buffer:
            shutil.copyfileobj(video.file, buffer)

        logger.info(f"Video saved to: {video_path}")

        output_folder = _VIDEOS_BASE / "yolo_outputs"
        output_folder.mkdir(parents=True, exist_ok=True)

        result = yolo_service.detect_horses_in_video(
            video_path=str(video_path),
            output_folder=str(output_folder),
            confidence_threshold=confidence_threshold,
            iou_threshold=iou_threshold,
            show_labels=show_labels,
            show_conf=show_conf,
            line_thickness=line_thickness
        )

        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result["message"])

        output_video_name = result["output_video_name"]
        result["download_url"] = f"/api/yolo/download/{output_video_name}"

        logger.info(f"YOLO detection successful: {result['total_detections']} detections")

        return YoloDetectionResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"YOLO detection failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Detection failed: {str(e)}")


@router.get("/download/{video_name}")
async def download_annotated_video(video_name: str):
    """Download the annotated video with YOLO detections"""
    try:
        output_folder = _VIDEOS_BASE / "yolo_outputs"
        video_path = output_folder / video_name

        if not video_path.exists():
            raise HTTPException(status_code=404, detail=f"Video not found: {video_name}")

        logger.info(f"Serving annotated video: {video_name}")

        return FileResponse(
            path=str(video_path),
            media_type="video/mp4",
            filename=video_name
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to serve video: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")


@router.get("/health")
async def health_check():
    try:
        model_path = yolo_service.model_path
        model_exists = model_path.exists()

        try:
            from ultralytics import YOLO
            ultralytics_available = True
        except ImportError:
            ultralytics_available = False

        return {
            "status": "healthy" if (model_exists and ultralytics_available) else "degraded",
            "service": "YOLO Detection Service",
            "model_path": str(model_path),
            "model_exists": model_exists,
            "ultralytics_available": ultralytics_available,
            "message": "YOLO service is ready" if (model_exists and ultralytics_available)
                      else "YOLO model or ultralytics not available"
        }

    except Exception as e:
        return {
            "status": "error",
            "service": "YOLO Detection Service",
            "message": f"Health check failed: {str(e)}"
        }

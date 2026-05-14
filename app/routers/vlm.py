"""
VLM Router - API endpoints for Vision-Language Model horse state classification
"""
from fastapi import APIRouter, HTTPException, File, UploadFile, Form
from fastapi.responses import FileResponse
from typing import Optional
from pathlib import Path
import shutil
import logging
import os
import httpx

from app.schemas.vlm import (
    VlmClassificationRequest,
    VlmClassificationResponse,
    VlmImageClassificationRequest,
    VlmImageClassificationResponse
)
from app.services.vlm_service import get_vlm_service
from app.config.settings import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/vlm", tags=["vlm"])

# Determine upload/output base directory relative to project root
_BASE_DIR = Path(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
_VIDEOS_BASE = _BASE_DIR / (settings.VIDEOS_FOLDER if settings.VIDEOS_FOLDER else "data/videos")


@router.post("/classify-video", response_model=VlmClassificationResponse)
async def classify_video(
    video: UploadFile = File(..., description="Video file to analyze"),
    vlm_model: str = Form(settings.DEFAULT_VLM_VIDEO_MODEL, alias="model_name", description="Ollama vision model name"),
    frame_interval: int = Form(1, description="Process every Nth frame (1 = all frames, higher = faster)"),
    resize: Optional[int] = Form(412, description="Resize frames to this size (256-1024)")
):
    """Classify horse states in video frames using Vision-Language Models."""
    try:
        if frame_interval < 1 or frame_interval > 120:
            raise HTTPException(status_code=400, detail="frame_interval must be between 1 and 120")

        if resize and (resize < 256 or resize > 1024):
            raise HTTPException(status_code=400, detail="resize must be between 256 and 1024")

        videos_dir = _VIDEOS_BASE / "vlm_inputs"
        outputs_dir = _VIDEOS_BASE / "vlm_outputs"
        videos_dir.mkdir(parents=True, exist_ok=True)
        outputs_dir.mkdir(parents=True, exist_ok=True)

        video_path = videos_dir / video.filename
        with video_path.open("wb") as buffer:
            shutil.copyfileobj(video.file, buffer)

        logger.info(f"Processing video: {video.filename} with VLM model: {vlm_model}")

        vlm_service = get_vlm_service()

        result = vlm_service.classify_video(
            video_path=str(video_path),
            output_folder=str(outputs_dir),
            model_name=vlm_model,
            frame_interval=frame_interval,
            resize=resize,
            create_annotated_video=True
        )

        if result["status"] == "error":
            raise HTTPException(
                status_code=500,
                detail=result.get("message", "Classification failed")
            )

        result["download_csv_url"] = f"/api/vlm/download/csv/{result['csv_name']}"
        if result.get("output_video_name"):
            result["download_video_url"] = f"/api/vlm/download/video/{result['output_video_name']}"

        return VlmClassificationResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"VLM video classification failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Classification failed: {str(e)}"
        )


@router.post("/classify-image", response_model=VlmImageClassificationResponse)
async def classify_image(
    image: UploadFile = File(..., description="Image file to analyze"),
    vlm_model: str = Form(settings.DEFAULT_VLM_IMAGE_MODEL, alias="model_name", description="Ollama vision model name"),
    resize: Optional[int] = Form(None, description="Resize image to this size (optional)")
):
    """Classify horse state in a single image using Vision-Language Models."""
    try:
        if resize and (resize < 256 or resize > 1024):
            raise HTTPException(status_code=400, detail="resize must be between 256 and 1024")

        images_dir = _VIDEOS_BASE / "vlm_images"
        outputs_dir = _VIDEOS_BASE / "vlm_outputs"
        images_dir.mkdir(parents=True, exist_ok=True)
        outputs_dir.mkdir(parents=True, exist_ok=True)

        image_path = images_dir / image.filename
        with image_path.open("wb") as buffer:
            shutil.copyfileobj(image.file, buffer)

        logger.info(f"Classifying image: {image.filename} with VLM model: {vlm_model}")

        vlm_service = get_vlm_service()

        result = vlm_service.classify_image(
            image_path=str(image_path),
            output_folder=str(outputs_dir),
            model_name=vlm_model,
            resize=resize,
            create_annotated_image=True
        )

        if result["status"] == "error":
            raise HTTPException(
                status_code=500,
                detail=result.get("message", "Classification failed")
            )

        if result.get("output_image_name"):
            result["download_image_url"] = f"/api/vlm/download/image/{result['output_image_name']}"

        return VlmImageClassificationResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"VLM image classification failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Classification failed: {str(e)}"
        )


@router.get("/download/csv/{csv_name}")
async def download_csv(csv_name: str):
    try:
        outputs_dir = _VIDEOS_BASE / "vlm_outputs"
        csv_path = outputs_dir / csv_name

        if not csv_path.exists():
            raise HTTPException(status_code=404, detail="CSV file not found")

        return FileResponse(path=str(csv_path), media_type="text/csv", filename=csv_name)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")


@router.get("/download/video/{video_name}")
async def download_video(video_name: str):
    try:
        outputs_dir = _VIDEOS_BASE / "vlm_outputs"
        video_path = outputs_dir / video_name

        if not video_path.exists():
            raise HTTPException(status_code=404, detail="Video file not found")

        return FileResponse(path=str(video_path), media_type="video/mp4", filename=video_name)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")


@router.get("/download/image/{image_name}")
async def download_image(image_name: str):
    try:
        outputs_dir = _VIDEOS_BASE / "vlm_outputs"
        image_path = outputs_dir / image_name

        if not image_path.exists():
            raise HTTPException(status_code=404, detail="Image file not found")

        ext = image_path.suffix.lower()
        media_types = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".bmp": "image/bmp"}
        media_type = media_types.get(ext, "image/jpeg")

        return FileResponse(path=str(image_path), media_type=media_type, filename=image_name)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")


@router.get("/health")
async def health_check():
    try:
        vlm_service = get_vlm_service()

        vision_models = []
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                res = await client.get("http://127.0.0.1:11434/api/tags")
                if res.status_code == 200:
                    data = res.json()
                    vision_keywords = ("vl", "vision", "llava", "moondream", "gemma3", "phi3", "bakllava")
                    for m in data.get("models", []):
                        name = m["name"]
                        if any(k in name.lower() for k in vision_keywords):
                            vision_models.append(name)
        except Exception:
            vision_models = ["qwen2.5vl:7b", "llava-phi3", "llama3.2-vision", "gemma3:4b"]

        return {
            "status": "healthy",
            "service": "vlm",
            "models_loaded": len(vlm_service._classifiers),
            "available_models": vision_models
        }
    except Exception as e:
        logger.error(f"VLM health check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}

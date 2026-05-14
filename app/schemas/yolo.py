"""
YOLO Detection Schemas - Request and Response models for YOLO horse detection
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class YoloDetectionRequest(BaseModel):
    model_config = {"protected_namespaces": ()}
    confidence_threshold: float = Field(default=0.7, ge=0.0, le=1.0, description="Confidence threshold for detections (0.0-1.0)")
    iou_threshold: float = Field(default=0.45, ge=0.0, le=1.0, description="IoU threshold for NMS (0.0-1.0)")
    show_labels: bool = Field(default=True, description="Whether to display class labels on bounding boxes")
    show_conf: bool = Field(default=True, description="Whether to display confidence scores on bounding boxes")
    line_thickness: int = Field(default=2, ge=1, le=10, description="Thickness of bounding box lines (1-10)")


class DetectionStatistics(BaseModel):
    model_config = {"protected_namespaces": ()}
    total_frames: int = Field(..., description="Total number of frames processed")
    frames_with_detections: int = Field(..., description="Number of frames containing horses")
    frames_without_detections: int = Field(..., description="Number of frames with no horses")
    max_horses_per_frame: int = Field(..., description="Maximum horses detected in a single frame")
    avg_horses_per_frame: float = Field(..., description="Average horses per frame (across all frames)")
    avg_horses_per_detection_frame: float = Field(..., description="Average horses per frame (only frames with detections)")


class BoundingBox(BaseModel):
    x1: int
    y1: int
    x2: int
    y2: int


class HorseDetection(BaseModel):
    model_config = {"protected_namespaces": ()}
    bbox: BoundingBox
    confidence: float
    class_name: str = "horse"


class FrameDetections(BaseModel):
    model_config = {"protected_namespaces": ()}
    frame_number: int
    detections: List[HorseDetection]


class YoloDetectionResponse(BaseModel):
    model_config = {"protected_namespaces": ()}
    status: str = Field(..., description="Status of the detection (success/error)")
    message: str = Field(..., description="Description of the result")
    video_name: str = Field(..., description="Name of the uploaded video")
    output_video_path: str = Field(..., description="Path to the annotated output video")
    download_url: str = Field(..., description="URL to download the annotated video")
    total_detections: int = Field(..., description="Total number of horse detections across all frames")
    detection_statistics: DetectionStatistics = Field(..., description="Detailed detection statistics")
    average_confidence: float = Field(..., description="Average confidence score across all detections")
    processing_time: float = Field(..., description="Time taken to process video (seconds)")
    model_info: Dict[str, Any] = Field(..., description="Information about the YOLO model used")
    sample_detections: Optional[List[FrameDetections]] = Field(default=None, description="Sample detections from key frames")

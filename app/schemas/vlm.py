"""
VLM Schemas - Request and Response models for Vision-Language Model horse state classification
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class VlmClassificationRequest(BaseModel):
    model_config = {"protected_namespaces": ()}
    model_name: str = Field(default="qwen2.5vl:7b", description="Ollama vision model to use")
    frame_interval: int = Field(default=30, ge=1, le=120, description="Process every Nth frame (1-120)")
    resize: Optional[int] = Field(default=412, ge=256, le=1024, description="Resize frames to this size (256-1024)")


class FrameClassification(BaseModel):
    model_config = {"protected_namespaces": ()}
    frame_number: int = Field(..., description="Frame number in video")
    timestamp: float = Field(..., description="Timestamp in video (seconds)")
    state: str = Field(..., description="Predicted horse state")
    raw_response: str = Field(..., description="Raw model response")
    inference_ms: int = Field(..., description="Inference time in milliseconds")


class StateStatistics(BaseModel):
    model_config = {"protected_namespaces": ()}
    total_frames_analyzed: int = Field(..., description="Total frames processed")
    state_counts: Dict[str, int] = Field(..., description="Count of each state")
    state_percentages: Dict[str, float] = Field(..., description="Percentage of each state")
    most_common_state: str = Field(..., description="Most frequently detected state")
    state_transitions: int = Field(..., description="Number of state changes")


class VlmClassificationResponse(BaseModel):
    model_config = {"protected_namespaces": ()}
    status: str = Field(..., description="Status of the classification (success/error)")
    message: str = Field(..., description="Description of the result")
    video_name: str = Field(..., description="Name of the uploaded video")
    output_csv_path: Optional[str] = Field(None, description="Path to CSV results file")
    csv_name: Optional[str] = Field(None, description="Name of CSV results file")
    download_csv_url: Optional[str] = Field(None, description="URL to download CSV results")
    output_video_path: Optional[str] = Field(None, description="Path to annotated video file")
    output_video_name: Optional[str] = Field(None, description="Name of annotated video file")
    download_video_url: Optional[str] = Field(None, description="URL to download annotated video")
    total_frames_analyzed: int = Field(..., description="Total frames processed")
    frame_interval: int = Field(..., description="Frame interval used")
    processing_time: float = Field(..., description="Time taken to process video (seconds)")
    average_inference_ms: float = Field(..., description="Average inference time per frame (ms)")
    model_info: Dict[str, Any] = Field(..., description="Information about the VLM model used")
    statistics: StateStatistics = Field(..., description="State distribution statistics")
    classifications: List[FrameClassification] = Field(..., description="Classification results for each analyzed frame")


class VlmImageClassificationRequest(BaseModel):
    model_config = {"protected_namespaces": ()}
    model_name: str = Field(default="qwen2.5vl:7b", description="Ollama vision model to use")
    resize: Optional[int] = Field(default=None, ge=256, le=1024, description="Resize image to this size (optional)")


class VlmImageClassificationResponse(BaseModel):
    model_config = {"protected_namespaces": ()}
    status: str = Field(..., description="Status of the classification")
    message: str = Field(..., description="Description of the result")
    image_name: str = Field(..., description="Name of the uploaded image")
    output_image_path: Optional[str] = Field(None, description="Path to annotated image file")
    output_image_name: Optional[str] = Field(None, description="Name of annotated image file")
    download_image_url: Optional[str] = Field(None, description="URL to download annotated image")
    state: str = Field(..., description="Predicted horse state")
    raw_response: str = Field(..., description="Raw model response")
    inference_ms: int = Field(..., description="Inference time in milliseconds")
    model_info: Dict[str, Any] = Field(..., description="Model information")

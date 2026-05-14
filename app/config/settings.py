"""
Settings - Application configuration
Compatible with Pydantic v2+
"""
try:
    # Pydantic v2+
    from pydantic_settings import BaseSettings
except ImportError:
    # Pydantic v1 (fallback)
    from pydantic import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings and configuration"""
    
    # Application settings
    APP_NAME: str = "HCS - Horse Care System"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = False
    
    # API settings
    API_V1_PREFIX: str = "/api/v1"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # DeepLabCut Configuration (Defaults to relative paths/empty, override via .env)
    DLC_CONDA_ENV: str = ""         # Path to DEEPLABCUT2 conda env
    CONFIG_PATH: str = ""
    VIDEOS_FOLDER: str = ""
    RESULTS_FOLDER: str = ""

    # Default analysis parameters
    DEFAULT_VIDEOTYPE: str = "avi"
    DEFAULT_SHUFFLE: int = 2
    DEFAULT_TRAININGSETINDEX: int = 0
    DEFAULT_DEVICE: str = "cuda:0"
    DEFAULT_SAVE_AS_CSV: bool = True
    DEFAULT_DYNAMIC: tuple = (True, 0.5, 10)
    DEFAULT_IN_RANDOM_ORDER: bool = True

    # Optional AI features
    YOLO_MODEL_PATH: str = "models/yolo/cls1s.pt"
    VLM_DEFAULT_MODEL: str = "qwen2.5vl:7b"
    VLM_MODEL_NAMES: str = "qwen2.5vl:7b,llava-phi3,llama3.2-vision,moondream:latest"
    DEFAULT_VLM_VIDEO_MODEL: str = "qwen2.5vl:7b"
    DEFAULT_VLM_IMAGE_MODEL: str = "qwen2.5vl:7b"
    CHATBOT_MODEL: str = "llama3.1:8b-instruct-q4_K_S"
    DEFAULT_CHATBOT_MODEL_NAME: str = "llama3.1:8b-instruct-q4_K_S"

    # Qdrant vector database (for RAG)
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_COLLECTION: str = "equine_database"

    # RTSP cameras (format: "Name|rtsp://url", comma-separated)
    RTSP_CAMERAS: str = ""

    # Anomaly detection thresholds
    ANOMALY_THRESHOLD_RATIO: float = 0.3
    ANOMALY_MIN_WINDOWS: int = 3

    class Config:
        env_file = ".env"
        case_sensitive = True


# Create settings instance
settings = Settings()

"""
Configuration dataclass for the real-time monitoring pipeline.

The CLI entry point builds this object; the worker only sees it.
This fully decouples argparse from the processing logic.
"""
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class MonitoringConfig:
    """Immutable configuration for a single monitoring run."""

    video_path: Path
    model_path: Path
    output_path: Optional[Path] = None
    display: bool = True
    save_video: bool = False

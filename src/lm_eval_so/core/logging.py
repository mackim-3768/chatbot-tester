from __future__ import annotations

import logging
import sys
from typing import Any, Dict

import json


class JsonFormatter(logging.Formatter):
    """Simple JSON log formatter."""

    def format(self, record: logging.LogRecord) -> str:
        data: Dict[str, Any] = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            data["exc_info"] = self.formatException(record.exc_info)
        if hasattr(record, "sample_id"):
            data["sample_id"] = getattr(record, "sample_id")
        return json.dumps(data)


def configure_logging(level: str | int = logging.INFO, json_format: bool = False) -> None:
    """Configure root logger with consistent formatting."""
    root = logging.getLogger()
    root.setLevel(level)

    # Remove existing handlers
    for h in root.handlers[:]:
        root.removeHandler(h)

    handler = logging.StreamHandler(sys.stdout)
    if json_format:
        formatter = JsonFormatter()
    else:
        formatter = logging.Formatter(
            fmt="[%(asctime)s] %(levelname)s [%(name)s] %(message)s",
            datefmt="%H:%M:%S",
        )
    handler.setFormatter(formatter)
    root.addHandler(handler)
    
    # Silence noisy libs
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

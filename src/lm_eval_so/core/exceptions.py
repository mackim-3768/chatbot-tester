from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass(slots=True)
class BackendError(Exception):
    message: str
    error_type: Optional[str] = None
    status_code: Optional[int] = None
    retryable: bool = False
    details: Optional[Dict[str, Any]] = None

    def __str__(self) -> str:
        return self.message

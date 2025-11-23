from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List

from ..domain import EvaluationResult


class Reporter(ABC):
    @abstractmethod
    def write(self, result: EvaluationResult, output_dir: Path) -> List[Path]:
        """Write report files under the given directory and return created paths."""


def ensure_output_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


__all__ = ["Reporter", "ensure_output_dir"]

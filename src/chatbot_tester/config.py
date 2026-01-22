from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from pydantic import BaseModel, Field

# Import existing EvaluatorConfig
# We assume this is available; if not, we will need to refactor evaluator/config.py first.
# Using relative import since this file is in src/chatbot_tester/config.py
from .evaluator.config import EvaluatorConfig


class StructureConfig(BaseModel):
    """Configuration for synthetic sample structure."""
    id: str = "custom"
    turns: int = 1
    include_system: bool = True
    include_expected: bool = True
    min_user_len: int = 10
    max_user_len: int = 200
    min_expected_len: int = 20
    max_expected_len: int = 400


class GeneratorConfig(BaseModel):
    """Configuration for dataset generation."""
    dataset_id: str = "dataset"
    name: str = "My Dataset"
    version: str = "v1"
    topic_prompt: str
    language_code: str = "en"
    sample_count: int = 10
    output_dir: Path = Path("./output")
    backend: str = "openai"
    backend_options: Dict[str, Any] = Field(default_factory=dict)
    structure: StructureConfig = Field(default_factory=StructureConfig)
    seed: Optional[int] = None
    cache_strategy: str = "default"  # default, overwrite, ignore


class RunnerConfig(BaseModel):
    """Configuration for the execution runner."""
    max_concurrency: int = 2
    timeout_seconds: float = 60.0
    max_retries: int = 2
    retry_backoff_factor: float = 2.0
    retry_backoff_jitter: float = 0.5
    rate_limit_per_second: Optional[float] = None
    trace_prefix: str = "run"
    output_dir: Optional[Path] = None


class TesterConfig(BaseModel):
    """Root configuration for Chatbot Tester."""
    generator: Optional[GeneratorConfig] = None
    runner: Optional[RunnerConfig] = None
    evaluator: Optional[EvaluatorConfig] = None

    @classmethod
    def load(cls, path: Path | str) -> "TesterConfig":
        """Load configuration from a YAML or JSON file."""
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"Configuration file not found: {p}")

        text = p.read_text(encoding="utf-8")
        if p.suffix.lower() in {".yml", ".yaml"}:
            data = yaml.safe_load(text) or {}
        else:
            data = json.loads(text)
        
        return cls(**data)


__all__ = [
    "TesterConfig",
    "GeneratorConfig",
    "StructureConfig",
    "RunnerConfig",
]

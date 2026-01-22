"""Chatbot runner package.

Provides dataset loading helpers, runner orchestration utilities, and backend adapters
for executing chatbot evaluation datasets against heterogeneous targets (API, ADB,
etc.).
"""

from .runner_core import RunnerConfig, run_async_job, run_job
from .dataset import load_dataset
from .backends.base import backend_registry, ChatBackend, register_backend
from . import backends as _backends  # noqa: F401  # ensure built-in backends register

__all__ = [
    "RunnerConfig",
    "run_job",
    "run_async_job",
    "load_dataset",
    "backend_registry",
    "ChatBackend",
    "register_backend",
]

__version__ = "0.1.0"

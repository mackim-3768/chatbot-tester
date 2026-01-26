"""Chatbot runner package.

Provides dataset loading helpers, runner orchestration utilities, and backend adapters
for executing chatbot evaluation datasets against heterogeneous targets (API, ADB,
etc.).
"""

from .runner_core import RunnerConfig, run_async_job, run_job
from .dataset import load_dataset
from lm_eval_so.core.backends.base import backend_registry, ChatBackend, register_backend

# ensure built-in backends register
import lm_eval_so.core.backends.openai_backend
import lm_eval_so.core.backends.adb_cli_backend

__all__ = [
    "RunnerConfig",
    "run_job",
    "run_async_job",
    "load_dataset",
    "backend_registry",
    "ChatBackend",
    "register_backend",
]

__version__ = "0.2.0"

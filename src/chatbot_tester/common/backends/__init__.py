from __future__ import annotations

from .base import ChatBackend, backend_registry, register_backend

# Register built-in backends
from . import openai_backend as _openai_backend  # noqa: F401
from . import adb_cli_backend as _adb_cli_backend  # noqa: F401

__all__ = ["ChatBackend", "backend_registry", "register_backend"]

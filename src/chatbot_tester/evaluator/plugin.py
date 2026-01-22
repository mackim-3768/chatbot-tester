from __future__ import annotations

import importlib.util
import logging
import sys
from pathlib import Path
from typing import List

from .registry import MetricRegistry

logger = logging.getLogger(__name__)


class PluginLoader:
    def __init__(self, registry: MetricRegistry) -> None:
        self._registry = registry

    def load_plugins(self, paths: List[str]) -> None:
        """Load plugins from the given list of file paths or module names."""
        for path in paths:
            try:
                # Try loading as file first
                p = Path(path)
                if p.exists() and p.suffix == ".py":
                    self._load_from_file(p)
                else:
                    # Fallback to module import
                    self._load_from_module(path)
            except Exception as e:
                logger.warning(f"Failed to load plugin '{path}': {e}")

    def _load_from_file(self, path: Path) -> None:
        module_name = path.stem
        spec = importlib.util.spec_from_file_location(module_name, path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not load spec from file: {path}")

        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        self._register_metrics_from_module(module)

    def _load_from_module(self, module_name: str) -> None:
        module = importlib.import_module(module_name)
        self._register_metrics_from_module(module)

    def _register_metrics_from_module(self, module) -> None:
        if not hasattr(module, "register_metrics"):
            logger.debug(f"Module {module.__name__} has no 'register_metrics' function. Skipping.")
            return

        register_func = getattr(module, "register_metrics")
        if not callable(register_func):
            logger.warning(f"Attributes 'register_metrics' in {module.__name__} is not callable.")
            return

        logger.info(f"Registering metrics from plugin: {module.__name__}")
        register_func(self._registry)

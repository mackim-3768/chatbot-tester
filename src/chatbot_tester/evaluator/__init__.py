from .config import EvaluatorConfig
from .orchestrator import EvaluationOrchestrator
from .plugin import PluginLoader
from .registry import metric_registry
from .metrics import register_default_metrics

# Register built-in metrics
register_default_metrics(metric_registry)

# Load discovered plugins
loader = PluginLoader(metric_registry)
loader.load_from_entry_points()

__version__ = "0.2.0"

__all__ = [
    "EvaluatorConfig",
    "EvaluationOrchestrator",
    "PluginLoader",
    "metric_registry",
    "__version__",
]

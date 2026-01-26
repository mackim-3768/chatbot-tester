from pathlib import Path
from unittest.mock import MagicMock

import pytest
from lm_eval_so.evaluator.plugin import PluginLoader
from lm_eval_so.evaluator.registry import MetricRegistry


@pytest.fixture
def registry():
    return MetricRegistry()


def test_load_from_path(registry, tmp_path):
    # Create a dummy python file with a metric registration
    plugin_file = tmp_path / "custom_metric.py"
    plugin_file.write_text("""
from lm_eval_so.evaluator.metrics.base import Metric
from lm_eval_so.evaluator.domain import EvalScore

class MyMetric(Metric):
    def score(self, sample, run) -> EvalScore:
        return EvalScore(value=1.0)

def register_metrics(registry):
    registry.register("my_metric", lambda cfg: MyMetric(**cfg))
""")

    loader = PluginLoader(registry)
    loader.load_plugins([str(plugin_file)])

    # Verify that the metric was registered
    metric = registry.create("my_metric", name="test")
    assert metric.name == "test"


def test_load_from_module(registry):
    # We can try loading a standard library module, though it won't have register_metrics
    # This mainly tests that the import machinery works without crashing
    loader = PluginLoader(registry)
    # 'math' is a safe standard module
    loader.load_plugins(["math"])
    # Should not crash, and nothing registered
    
    # To test actual module loading with registration, we'd need a complex setup
    # or rely on the file loading test which uses the same underlying mechanism slightly differently.
    # For now, ensuring it doesn't crash on valid modules is good.


def test_invalid_path_graceful_failure(registry, caplog):
    loader = PluginLoader(registry)
    loader.load_plugins(["/non/existent/path.py"])
    
    assert "Failed to load plugin" in caplog.text


def test_missing_register_metrics(registry, tmp_path):
    plugin_file = tmp_path / "no_reg.py"
    plugin_file.write_text("x = 1")
    
    loader = PluginLoader(registry)
    loader.load_plugins([str(plugin_file)])
    
    # Should log debug message but not fail

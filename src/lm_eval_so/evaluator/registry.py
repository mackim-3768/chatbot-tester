from __future__ import annotations

from typing import Any, Callable, Dict, Mapping

from .metrics.base import Metric

MetricFactory = Callable[[Mapping[str, Any]], Metric]


class MetricRegistry:
    def __init__(self) -> None:
        self._factories: Dict[str, MetricFactory] = {}

    def register(self, metric_type: str, factory: MetricFactory) -> None:
        if metric_type in self._factories:
            raise ValueError(f"metric '{metric_type}' already registered")
        self._factories[metric_type] = factory

    def create(self, metric_type: str, *, name: str | None = None, parameters: Mapping[str, Any] | None = None) -> Metric:
        factory = self._factories.get(metric_type)
        if factory is None:
            raise KeyError(f"metric '{metric_type}' is not registered")
        metric_name = name or metric_type
        return factory({"name": metric_name, "parameters": dict(parameters or {})})


metric_registry = MetricRegistry()


__all__ = [
    "Metric",
    "MetricRegistry",
    "metric_registry",
]

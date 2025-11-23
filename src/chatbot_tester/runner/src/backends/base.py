from __future__ import annotations

import abc
from typing import Any, Mapping

from ..runner_context import RunnerContext
from ..models import ChatResponse, RunRequest


class ChatBackend(abc.ABC):
    """Base adapter for chatbot providers."""

    name: str

    def __init__(self, context: RunnerContext | None = None) -> None:
        self.context = context or RunnerContext()

    @abc.abstractmethod
    async def send(self, request: RunRequest) -> ChatResponse:
        """Send messages to backend and return response."""

    def configure(self, **options: Any) -> None:
        if options:
            self.context.options.update(options)


class BackendRegistry:
    def __init__(self) -> None:
        self._registry: dict[str, type[ChatBackend]] = {}

    def register(self, name: str, backend_cls: type[ChatBackend]) -> None:
        self._registry[name] = backend_cls

    def create(self, name: str, context: RunnerContext | None = None, **opts: Any) -> ChatBackend:
        backend_cls = self._registry.get(name)
        if backend_cls is None:
            raise ValueError(f"Backend '{name}' is not registered")
        backend = backend_cls(context=context)
        if opts:
            backend.configure(**opts)
        return backend

    def names(self) -> list[str]:
        return sorted(self._registry.keys())


backend_registry = BackendRegistry()


def register_backend(name: str):
    def decorator(cls: type[ChatBackend]) -> type[ChatBackend]:
        backend_registry.register(name, cls)
        return cls

    return decorator

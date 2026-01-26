from __future__ import annotations

import abc
from typing import Any, Dict, List, Optional, Type

from ..context import RunnerContext
from ..models import ChatResponse, RunRequest


class ChatBackend(abc.ABC):
    """Base adapter for chatbot providers.
    
    This class defines the interface that all chatbot backends must implement.
    It handles configuration and context management, delegating the actual
    generation logic to the abstract `send` method.

    Description:
        Base class for integrating different LLM providers (e.g., OpenAI, Anthropic, Local)
        into the LM-Eval-SO runner.

    When to use:
        Inherit from this class when you want to add support for a new model provider
        or a custom inference endpoint.

    Example:
        ```python
        class MyCustomBackend(ChatBackend):
            name = "my_custom"

            async def send(self, request: RunRequest) -> ChatResponse:
                # helper logic to call API
                response_text = await call_my_api(request.messages)
                return ChatResponse(content=response_text)
        ```
    """

    name: str
    """Unique identifier for the backend (e.g. 'openai', 'anthropic')."""

    def __init__(self, context: Optional[RunnerContext] = None) -> None:
        """Initialize the backend.

        Args:
            context: Shared runner context containing cancellation tokens and other shared state.
        """
        self.context = context or RunnerContext()
        self.backend_options: Dict[str, Any] = {}

    @abc.abstractmethod
    async def send(self, request: RunRequest) -> ChatResponse:
        """Send messages to backend and return response.
        
        @extension-point: Must override this method to implement provider-specific logic.

        Args:
            request: The run request containing messages and parameters.

        Returns:
            ChatResponse: The model's response.
        """

    def configure(self, **options: Any) -> None:
        """Configure backend-specific options.

        Args:
            **options: Key-value pairs for configuration (e.g. api_key, temperature).
        """
        if options:
            self.backend_options.update(options)


class BackendRegistry:
    """Registry for discovering and instantiating backends.
    
    Description:
        Manages registration of backend classes to allow instantiation by name string.
    """
    def __init__(self) -> None:
        self._registry: Dict[str, Type[ChatBackend]] = {}

    def register(self, name: str, backend_cls: Type[ChatBackend]) -> None:
        """Register a new backend class.

        Args:
            name: Unique name for the backend.
            backend_cls: The Backend class to register.
        """
        self._registry[name] = backend_cls

    def create(self, name: str, context: Optional[RunnerContext] = None, **opts: Any) -> ChatBackend:
        """Create a backend instance by name.

        Args:
            name: Registered backend name.
            context: Runner context.
            **opts: Configuration options passed to `configure`.

        Returns:
            ChatBackend: Configured backend instance.

        Raises:
            ValueError: If backend name is not found.
        """
        backend_cls = self._registry.get(name)
        if backend_cls is None:
            raise ValueError(f"Backend '{name}' is not registered")
        backend = backend_cls(context=context)
        if opts:
            backend.configure(**opts)
        return backend

    def names(self) -> List[str]:
        """List all registered backend names."""
        return sorted(self._registry.keys())


backend_registry = BackendRegistry()


def register_backend(name: str):
    """Decorator to register a backend class.

    Args:
        name: Name to register the backend under.

    Example:
        ```python
        @register_backend("my_backend")
        class MyBackend(ChatBackend):
            ...
        ```
    """
    def decorator(cls: Type[ChatBackend]) -> Type[ChatBackend]:
        backend_registry.register(name, cls)
        return cls

    return decorator

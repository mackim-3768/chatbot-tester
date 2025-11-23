from __future__ import annotations

import os
from typing import Any, Dict, List

from openai import AsyncOpenAI
from openai import APIConnectionError, APIError, RateLimitError, BadRequestError, AuthenticationError

from ..models import ChatResponse, Message, RunRequest, TokenUsage
from ..exceptions import BackendError
from .base import ChatBackend, register_backend


def _build_messages(messages: List[Message]) -> List[Dict[str, Any]]:
    payload = []
    for msg in messages:
        entry: Dict[str, Any] = {"role": msg.role, "content": msg.content}
        if msg.name:
            entry["name"] = msg.name
        payload.append(entry)
    return payload


@register_backend("openai")
class OpenAIChatBackend(ChatBackend):
    """Adapter that calls OpenAI-compatible chat completion endpoints."""

    def __init__(self, context=None) -> None:
        super().__init__(context=context)
        self._client: AsyncOpenAI | None = None

    def _get_client(self) -> AsyncOpenAI:
        if self._client is not None:
            return self._client
        api_key = self.backend_options.get("api_key") or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise BackendError("OPENAI_API_KEY is not set", error_type="auth", retryable=False)
        base_url = self.backend_options.get("base_url") or os.getenv("OPENAI_BASE_URL")
        self._client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        return self._client

    async def send(self, request: RunRequest) -> ChatResponse:
        client = self._get_client()
        model = request.run_config.model or self.backend_options.get("model")
        if not model:
            raise BackendError("RunConfig.model is required for OpenAI backend", error_type="config", retryable=False)

        params = {
            "model": model,
            "messages": _build_messages(request.messages),
        }
        params.update(self.backend_options.get("request_defaults", {}))
        params.update(request.run_config.parameters)

        try:
            resp = await client.chat.completions.create(**params)  # type: ignore[arg-type]
        except RateLimitError as exc:
            raise BackendError(str(exc), error_type="rate_limit", status_code=429, retryable=True)
        except (APIConnectionError, APIError) as exc:
            retryable = getattr(exc, "status_code", 500) >= 500
            raise BackendError(str(exc), error_type="api_error", status_code=getattr(exc, "status_code", None), retryable=retryable)
        except (BadRequestError, AuthenticationError) as exc:
            raise BackendError(str(exc), error_type="request_error", status_code=getattr(exc, "status_code", None), retryable=False)
        except Exception as exc:  # pragma: no cover
            raise BackendError(str(exc), error_type="unknown", retryable=False)

        choice = resp.choices[0]
        text = choice.message.content or ""
        usage = None
        if resp.usage is not None:
            usage = TokenUsage(
                input_tokens=resp.usage.prompt_tokens,
                output_tokens=resp.usage.completion_tokens,
                total_tokens=resp.usage.total_tokens,
            )

        return ChatResponse(
            text=text,
            raw=resp.model_dump(mode="python"),
            usage=usage,
            finish_reason=choice.finish_reason,
            status_code=200,
        )

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Mapping, MutableMapping, Optional

# Import and re-export common models
from chatbot_tester.common.models import (
    DatasetInfo,
    Message,
    RunResultStatus,
    TestSample,
    ensure_messages,
)


@dataclass(slots=True)
class TokenUsage:
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    total_tokens: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "input": self.input_tokens,
            "output": self.output_tokens,
            "total": self.total_tokens,
        }


@dataclass(slots=True)
class ChatResponse:
    text: str
    raw: Optional[MutableMapping[str, Any]] = None
    usage: Optional[TokenUsage] = None
    finish_reason: Optional[str] = None
    status_code: Optional[int] = None
    headers: Optional[Mapping[str, str]] = None

    def to_dict(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {"text": self.text}
        if self.finish_reason is not None:
            payload["finish_reason"] = self.finish_reason
        if self.status_code is not None:
            payload["status_code"] = self.status_code
        if self.usage is not None:
            payload["tokens"] = self.usage.to_dict()
        if self.headers is not None:
            payload["headers"] = dict(self.headers)
        if self.raw is not None:
            payload["raw"] = self.raw
        return payload


@dataclass(slots=True)
class RunConfig:
    backend: str
    model: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    backend_options: Dict[str, Any] = field(default_factory=dict)
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {"backend": self.backend}
        if self.model is not None:
            payload["model"] = self.model
        if self.parameters:
            payload["parameters"] = self.parameters
        if self.backend_options:
            payload["backend_options"] = self.backend_options
        if self.metadata is not None:
            payload["metadata"] = self.metadata
        return payload


@dataclass(slots=True)
class RunRequest:
    sample: TestSample
    run_config: RunConfig
    dataset_info: DatasetInfo
    trace_id: str
    attempt: int
    timeout_seconds: Optional[float]

    @property
    def messages(self) -> List[Message]:
        return self.sample.messages


@dataclass(slots=True)
class RunError:
    message: str
    error_type: Optional[str] = None
    status_code: Optional[int] = None
    retryable: bool = False
    details: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {"message": self.message, "retryable": self.retryable}
        if self.error_type is not None:
            payload["type"] = self.error_type
        if self.status_code is not None:
            payload["status_code"] = self.status_code
        if self.details is not None:
            payload["details"] = self.details
        return payload


@dataclass(slots=True)
class RunResult:
    sample_id: str
    dataset_id: Optional[str]
    backend: str
    run_config: RunConfig
    request_messages: List[Message]
    request_context: Dict[str, Any]
    response: Optional[ChatResponse]
    status: RunResultStatus
    latency_ms: Optional[float]
    started_at: datetime
    completed_at: datetime
    attempts: int
    trace_id: str
    error: Optional[RunError] = None

    def to_record(self) -> Dict[str, Any]:
        return {
            "sample_id": self.sample_id,
            "dataset_id": self.dataset_id,
            "backend": self.backend,
            "trace_id": self.trace_id,
            "status": self.status.value,
            "attempts": self.attempts,
            "latency_ms": self.latency_ms,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat(),
            "run_config": self.run_config.to_dict(),
            "request": {
                "messages": [m.to_dict() for m in self.request_messages],
                "context": self.request_context,
            },
            "response": self.response.to_dict() if self.response else None,
            "error": self.error.to_dict() if self.error else None,
        }


__all__ = [
    "ChatResponse",
    "DatasetInfo",
    "Message",
    "RunConfig",
    "RunError",
    "RunRequest",
    "RunResult",
    "RunResultStatus",
    "TestSample",
    "TokenUsage",
    "ensure_messages",
]

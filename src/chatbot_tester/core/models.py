from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Optional, Union


@dataclass(slots=True)
class Message:
    role: str
    content: str
    name: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "Message":
        return cls(
            role=str(data["role"]),
            content=str(data.get("content", "")),
            name=data.get("name"),
            metadata=dict(data.get("metadata", {})) if data.get("metadata") else None,
        )

    def to_dict(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {"role": self.role, "content": self.content}
        if self.name is not None:
            payload["name"] = self.name
        if self.metadata is not None:
            payload["metadata"] = self.metadata
        return payload


@dataclass(slots=True)
class TestSample:
    __test__ = False  # valid for pytest to ignore this class

    id: str
    messages: List[Message]
    expected: Optional[Union[str, Dict[str, Any], List[Any]]] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "TestSample":
        msgs = [Message.from_dict(m) for m in data.get("messages", [])]
        return cls(
            id=str(data["id"]),
            messages=msgs,
            expected=data.get("expected"),
            tags=list(data.get("tags", [])) or None,
            metadata=dict(data.get("metadata", {})) if data.get("metadata") else None,
        )

    def to_dict(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "id": self.id,
            "messages": [m.to_dict() for m in self.messages],
        }
        if self.expected is not None:
            payload["expected"] = self.expected
        if self.tags is not None:
            payload["tags"] = self.tags
        if self.metadata is not None:
            payload["metadata"] = self.metadata
        return payload


# -----------------------------------------------------------------------------
# Execution Models (Moved from runner)
# -----------------------------------------------------------------------------

from datetime import datetime
from enum import Enum


class RunResultStatus(str, Enum):
    """Execution status persisted with each sample."""

    OK = "ok"
    RETRY = "retry"
    TIMEOUT = "timeout"
    ERROR = "error"


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
    raw: Optional[Mapping[str, Any]] = None
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
class DatasetInfo:
    dataset_id: Optional[str]
    name: Optional[str]
    version: Optional[str]
    source: Optional[Any]
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "dataset_id": self.dataset_id,
            "name": self.name,
            "version": self.version,
            "source": self.source,
            "metadata": self.metadata,
        }


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

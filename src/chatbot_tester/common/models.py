from __future__ import annotations

from typing import Any, Dict, List, Optional, Union, Mapping, MutableMapping
from enum import Enum
from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict


class Message(BaseModel):
    """A message in a conversation."""

    model_config = ConfigDict(populate_by_name=True)

    role: str
    content: str
    name: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "Message":
        # Handle cases where input might be a dict but keys are slightly different?
        # For now, rely on Pydantic's validation but wrap it for compatibility.
        # Ensure we handle missing optional keys gracefully if they are not in data.
        return cls.model_validate(data)

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump(exclude_none=True)


class TestSample(BaseModel):
    """A test sample containing messages and expectations."""

    model_config = ConfigDict(populate_by_name=True)

    id: str
    messages: List[Message]
    expected: Optional[Union[str, Dict[str, Any], List[Any]]] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "TestSample":
        return cls.model_validate(data)

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump(exclude_none=True)


class TokenUsage(BaseModel):
    """Token usage statistics."""

    model_config = ConfigDict(populate_by_name=True)

    input_tokens: Optional[int] = Field(None, alias="input")
    output_tokens: Optional[int] = Field(None, alias="output")
    total_tokens: Optional[int] = Field(None, alias="total")

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump(by_alias=True, exclude_none=True)


class ChatResponse(BaseModel):
    """Response from a chat backend."""

    model_config = ConfigDict(populate_by_name=True)

    text: str
    raw: Optional[MutableMapping[str, Any]] = None
    usage: Optional[TokenUsage] = Field(None, alias="tokens")
    finish_reason: Optional[str] = None
    status_code: Optional[int] = None
    headers: Optional[Mapping[str, str]] = None

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump(by_alias=True, exclude_none=True)


class RunConfig(BaseModel):
    """Configuration for a run."""

    model_config = ConfigDict(populate_by_name=True)

    backend: str
    model: Optional[str] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)
    backend_options: Dict[str, Any] = Field(default_factory=dict)
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump(exclude_none=True)


class DatasetInfo(BaseModel):
    """Information about the dataset."""

    model_config = ConfigDict(populate_by_name=True)

    dataset_id: Optional[str] = None
    name: Optional[str] = None
    version: Optional[str] = None
    source: Optional[Any] = None
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump(exclude_none=True)


class RunResultStatus(str, Enum):
    """Execution status persisted with each sample."""
    OK = "ok"
    RETRY = "retry"
    TIMEOUT = "timeout"
    ERROR = "error"


class RunError(BaseModel):
    """Error information."""

    model_config = ConfigDict(populate_by_name=True)

    message: str
    error_type: Optional[str] = Field(None, alias="type")
    status_code: Optional[int] = None
    retryable: bool = False
    details: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump(by_alias=True, exclude_none=True)


class RunResult(BaseModel):
    """Result of a single run."""

    model_config = ConfigDict(populate_by_name=True)

    sample_id: str
    dataset_id: Optional[str] = None
    backend: str
    run_config: RunConfig
    request_messages: List[Message]
    request_context: Dict[str, Any]
    response: Optional[ChatResponse] = None
    status: RunResultStatus
    latency_ms: Optional[float] = None
    started_at: datetime
    completed_at: datetime
    attempts: int
    trace_id: str
    error: Optional[RunError] = None

    def to_record(self) -> Dict[str, Any]:
        # Custom serialization to match existing format exactly
        data = self.model_dump(exclude_none=True)
        # Ensure status is string
        data["status"] = self.status.value
        # Ensure datetimes are isoformat strings (Pydantic does this by default usually, but let's check)
        # Pydantic v2 model_dump returns datetime objects unless mode='json'

        # We can use mode='json' to get isoformatted strings
        data_json = self.model_dump(mode='json', exclude_none=True)

        # Re-structure to match `to_record` output from runner/models.py
        # Runner output structure:
        # {
        #     "sample_id": ...,
        #     "dataset_id": ...,
        #     "backend": ...,
        #     "trace_id": ...,
        #     "status": ...,
        #     "attempts": ...,
        #     "latency_ms": ...,
        #     "started_at": ...,
        #     "completed_at": ...,
        #     "run_config": ...,
        #     "request": {
        #         "messages": ...,
        #         "context": ...
        #     },
        #     "response": ...,
        #     "error": ...
        # }

        record = {
            "sample_id": data_json["sample_id"],
            "dataset_id": data_json.get("dataset_id"),
            "backend": data_json["backend"],
            "trace_id": data_json["trace_id"],
            "status": data_json["status"],
            "attempts": data_json["attempts"],
            "latency_ms": data_json.get("latency_ms"),
            "started_at": data_json["started_at"],
            "completed_at": data_json["completed_at"],
            "run_config": self.run_config.to_dict(),
            "request": {
                "messages": [m.to_dict() for m in self.request_messages],
                "context": data_json.get("request_context", {}),
            },
            "response": self.response.to_dict() if self.response else None,
            "error": self.error.to_dict() if self.error else None,
        }
        return record


class RunRequest(BaseModel):
    """A request to run a sample."""

    model_config = ConfigDict(populate_by_name=True)

    sample: TestSample
    run_config: RunConfig
    dataset_info: DatasetInfo
    trace_id: str
    attempt: int
    timeout_seconds: Optional[float]

    @property
    def messages(self) -> List[Message]:
        return self.sample.messages


def ensure_messages(value: Union[List[Message], List[Dict[str, Any]]]) -> List[Message]:
    """Ensure that the input is a list of Message objects."""
    if not value:
        return []

    result = []
    for v in value:
        if isinstance(v, Message):
            result.append(v)
        elif isinstance(v, dict):
            result.append(Message.model_validate(v))
        else:
            raise ValueError(f"Invalid message type: {type(v)}")
    return result

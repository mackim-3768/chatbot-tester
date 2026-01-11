from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Optional

class RunResultStatus(str, Enum):
    """Execution status persisted with each sample."""
    OK = "ok"
    RETRY = "retry"
    TIMEOUT = "timeout"
    ERROR = "error"

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
    id: str
    messages: List[Message]
    expected: Optional[Any] = None
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

def ensure_messages(value: Iterable[Mapping[str, Any]]) -> List[Message]:
    return [Message.from_dict(v) for v in value]

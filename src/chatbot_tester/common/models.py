from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Optional

__all__ = ["Message", "TestSample", "ensure_messages"]


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


def ensure_messages(value: List[Mapping[str, Any]]) -> List[Message]:
    return [Message.from_dict(v) for v in value]

from dataclasses import dataclass
from typing import List, Optional, Union, Dict, Any


@dataclass
class Message:
    role: str
    content: str
    name: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {"role": self.role, "content": self.content}
        if self.name is not None:
            d["name"] = self.name
        if self.metadata is not None:
            d["metadata"] = self.metadata
        return d


@dataclass
class TestSample:
    id: str
    messages: List[Message]
    expected: Optional[Union[str, Dict[str, Any], List[Any]]] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "id": self.id,
            "messages": [m.to_dict() for m in self.messages],
        }
        if self.expected is not None:
            d["expected"] = self.expected
        if self.tags is not None:
            d["tags"] = self.tags
        if self.metadata is not None:
            d["metadata"] = self.metadata
        return d

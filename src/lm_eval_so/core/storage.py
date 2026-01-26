from __future__ import annotations

import abc
import json
import os
from pathlib import Path
from typing import Any, Iterable, Optional, Union

class StorageBackend(abc.ABC):
    """Abstract base class for storage backends."""

    @abc.abstractmethod
    def save_json(self, key: str, data: Any, **kwargs) -> str:
        """Save data as JSON."""
        pass

    @abc.abstractmethod
    def save_jsonl(self, key: str, data: Iterable[Any], **kwargs) -> str:
        """Save data as JSONL (line-delimited JSON)."""
        pass

    @abc.abstractmethod
    def load_json(self, key: str, **kwargs) -> Any:
        """Load JSON data from storage."""
        pass
    
    @abc.abstractmethod
    def exists(self, key: str) -> bool:
        """Check if a key exists in storage."""
        pass

    @abc.abstractmethod
    def make_dir(self, key: str) -> None:
        """Ensure a directory exists (for hierarchical storage)."""
        pass
    
    @abc.abstractmethod
    def get_path(self, key: str) -> str:
        """Get the full path or URI for a key."""
        pass


class LocalFileSystemStorage(StorageBackend):
    """Storage backend that uses the local file system."""

    def __init__(self, base_path: Union[str, Path]):
        self.base_path = Path(base_path).resolve()
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _resolve_path(self, key: str) -> Path:
        # Prevent traversal attacks conceptually, though typically key is respected as relative
        return self.base_path / key

    def save_json(self, key: str, data: Any, **kwargs) -> str:
        path = self._resolve_path(key)
        self.make_dir(str(path.parent.relative_to(self.base_path)))
        
        encoding = kwargs.get("encoding", "utf-8")
        indent = kwargs.get("indent", 2)
        ensure_ascii = kwargs.get("ensure_ascii", False)
        
        with path.open("w", encoding=encoding) as f:
            json.dump(data, f, indent=indent, ensure_ascii=ensure_ascii)
        
        return str(path)

    def save_jsonl(self, key: str, data: Iterable[Any], **kwargs) -> str:
        path = self._resolve_path(key)
        self.make_dir(str(path.parent.relative_to(self.base_path)))
        
        encoding = kwargs.get("encoding", "utf-8")
        ensure_ascii = kwargs.get("ensure_ascii", False)
        
        with path.open("w", encoding=encoding) as f:
            for item in data:
                f.write(json.dumps(item, ensure_ascii=ensure_ascii) + "\n")
        
        return str(path)

    def load_json(self, key: str, **kwargs) -> Any:
        path = self._resolve_path(key)
        if not path.exists():
            raise FileNotFoundError(f"Key not found: {key}")
            
        encoding = kwargs.get("encoding", "utf-8")
        with path.open("r", encoding=encoding) as f:
            return json.load(f)

    def exists(self, key: str) -> bool:
        return self._resolve_path(key).exists()

    def make_dir(self, key: str) -> None:
        path = self._resolve_path(key)
        path.mkdir(parents=True, exist_ok=True)

    def get_path(self, key: str) -> str:
        return str(self._resolve_path(key))

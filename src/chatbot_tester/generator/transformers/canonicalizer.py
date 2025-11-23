from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional

from ..types import Message, TestSample
from ..utils import gen_id_from_messages


def _as_messages(obj: Any) -> Optional[List[Dict[str, Any]]]:
    if isinstance(obj, list) and all(isinstance(x, dict) for x in obj):
        return obj  # assume already [{role, content, ...}]
    return None


def canonicalize_rows(
    rows: Iterable[Dict[str, Any]],
    *,
    id_col: Optional[str] = None,
    user_col: Optional[str] = None,
    expected_col: Optional[str] = None,
    system_col: Optional[str] = None,
    tags_col: Optional[str] = None,
    tags_sep: str = "|",
    language_col: Optional[str] = None,
) -> List[TestSample]:
    samples: List[TestSample] = []

    for row in rows:
        msgs = _as_messages(row.get("messages"))
        if msgs is None and "input" in row and isinstance(row.get("input"), list):
            msgs = _as_messages(row.get("input"))

        if msgs is not None:
            messages = [
                Message(
                    role=str(m.get("role", "user")),
                    content=str(m.get("content", "")),
                    name=(None if m.get("name") is None else str(m.get("name"))),
                    metadata=(m.get("metadata") if isinstance(m.get("metadata"), dict) else None),
                )
                for m in msgs
            ]
            sample_id = str(row.get("id") or gen_id_from_messages([m for m in msgs]))
            expected = row.get("expected")
            tags = row.get("tags") if isinstance(row.get("tags"), list) else None
            md = row.get("metadata") if isinstance(row.get("metadata"), dict) else None
            samples.append(TestSample(id=sample_id, messages=messages, expected=expected, tags=tags, metadata=md))
            continue

        user_text = str(row.get(user_col, "")) if user_col else str(row.get("user", row.get("question", "")))
        expected = row.get(expected_col) if expected_col else row.get("expected") or row.get("answer")
        system_text = str(row.get(system_col, "")) if system_col else str(row.get("system", ""))

        messages: List[Message] = []
        if system_text:
            messages.append(Message(role="system", content=system_text))
        messages.append(Message(role="user", content=user_text))

        sample_id = str(row.get(id_col)) if id_col and row.get(id_col) else gen_id_from_messages([m.to_dict() for m in messages])

        tags = None
        if tags_col and row.get(tags_col):
            tags = [t.strip() for t in str(row.get(tags_col)).split(tags_sep) if t.strip()]

        metadata = None
        if language_col and row.get(language_col):
            metadata = {"language": str(row.get(language_col))}

        samples.append(
            TestSample(
                id=sample_id,
                messages=messages,
                expected=expected,
                tags=tags,
                metadata=metadata,
            )
        )

    return samples

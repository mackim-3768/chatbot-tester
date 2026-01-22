from __future__ import annotations

from typing import Iterable, List, Optional

from chatbot_tester.core.models import TestSample


def _user_text_length(sample: TestSample) -> int:
    return sum(len(m.content) for m in sample.messages if m.role == "user")


def filter_by_length(
    samples: Iterable[TestSample],
    *,
    min_len: Optional[int] = None,
    max_len: Optional[int] = None,
) -> List[TestSample]:
    out: List[TestSample] = []
    for s in samples:
        L = _user_text_length(s)
        if min_len is not None and L < min_len:
            continue
        if max_len is not None and L > max_len:
            continue
        out.append(s)
    return out

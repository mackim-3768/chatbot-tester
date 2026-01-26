from __future__ import annotations

import random
from typing import Iterable, List, Sequence, TypeVar

T = TypeVar("T")


def sample_list(items: Sequence[T], n: int, *, randomize: bool = False, seed: int = 42) -> List[T]:
    if n <= 0 or n >= len(items):
        return list(items)
    if randomize:
        rnd = random.Random(seed)
        return rnd.sample(list(items), n)
    return list(items)[:n]

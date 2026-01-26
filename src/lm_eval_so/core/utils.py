from __future__ import annotations

import asyncio
import functools
from typing import Any, Callable


async def run_in_thread(func: Callable[..., Any], /, *args: Any, **kwargs: Any) -> Any:
    """Execute blocking function in a background thread (Py3.8 compatible)."""

    if hasattr(asyncio, "to_thread"):
        return await asyncio.to_thread(func, *args, **kwargs)  # type: ignore[attr-defined]

    loop = asyncio.get_running_loop()
    bound = functools.partial(func, *args, **kwargs)
    return await loop.run_in_executor(None, bound)

__all__ = ["run_in_thread"]

from __future__ import annotations

import asyncio
import logging
import random
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, AsyncIterator, Iterator, List, Optional, Sequence

from chatbot_tester.core.backends.base import backend_registry
from .exceptions import BackendError
from .models import (
    DatasetInfo,
    RunConfig,
    RunError,
    RunRequest,
    RunResult,
    RunResultStatus,
    TestSample,
)
from chatbot_tester.core.context import RunnerContext
from ..config import RunnerConfig


# RunnerConfig is replaced by RunnerConfig in ..config


class _RateLimiter:
    def __init__(self, rate_per_sec: Optional[float]) -> None:
        self._min_interval = 1.0 / rate_per_sec if rate_per_sec and rate_per_sec > 0 else None
        self._lock = asyncio.Lock()
        self._last_call: float = 0.0

    async def acquire(self) -> None:
        if self._min_interval is None:
            return
        async with self._lock:
            now = time.monotonic()
            wait_for = self._min_interval - (now - self._last_call)
            if wait_for > 0:
                await asyncio.sleep(wait_for)
            self._last_call = time.monotonic()


async def run_async_stream_job(
    dataset: DatasetInfo,
    samples: Sequence[TestSample],
    backend_name: str,
    run_config: RunConfig,
    options: RunnerConfig,
    logger: Optional[logging.Logger] = None,
) -> AsyncIterator[RunResult]:
    """
    Run a job and yield results as they complete.
    """
    logger = logger or logging.getLogger("chatbot_tester.runner")
    total = len(samples)
    completed = 0
    progress_lock = asyncio.Lock()
    
    context = RunnerContext(
        options={"backend": backend_name, "run_config": run_config.to_dict()},
        logger=logger,
        trace_prefix=options.trace_prefix,
    )
    backend = backend_registry.create(backend_name, context=context, **run_config.backend_options)
    semaphore = asyncio.Semaphore(max(1, options.max_concurrency))
    rate_limiter = _RateLimiter(options.rate_limit_per_second)
    
    tasks = []
    for sample in samples:
        # Create a coroutine for each sample
        coro = _run_single_sample(
            sample=sample,
            dataset=dataset,
            backend=backend,
            backend_name=backend_name,
            run_config=run_config,
            options=options,
            semaphore=semaphore,
            rate_limiter=rate_limiter,
            logger=logger,
        )
        # Wrap it to update progress before returning
        async def _progress_wrapper(c):
            res = await c
            nonlocal completed
            async with progress_lock:
                completed += 1
                logger.info(
                    "progress %d/%d sample=%s status=%s",
                    completed,
                    total,
                    res.sample_id,
                    res.status.value,
                )
            return res
            
        tasks.append(asyncio.create_task(_progress_wrapper(coro)))
    
    for future in asyncio.as_completed(tasks):
        result = await future
        yield result


async def run_async_job(
    dataset: DatasetInfo,
    samples: Sequence[TestSample],
    backend_name: str,
    run_config: RunConfig,
    options: RunnerConfig,
    logger: Optional[logging.Logger] = None,
) -> List[RunResult]:
    """
    Run a job and return all results as a list.
    """
    results = []
    async for result in run_async_stream_job(
        dataset=dataset,
        samples=samples,
        backend_name=backend_name,
        run_config=run_config,
        options=options,
        logger=logger,
    ):
        results.append(result)
    return results


def run_stream_job(
    dataset: DatasetInfo,
    samples: Sequence[TestSample],
    backend_name: str,
    run_config: RunConfig,
    options: RunnerConfig,
    logger: Optional[logging.Logger] = None,
) -> Iterator[RunResult]:
    """
    Sync wrapper for run_async_stream_job.
    WARNING: This creates a new event loop for each iteration or manages the loop manually.
    """
    async_gen = run_async_stream_job(
        dataset=dataset,
        samples=samples,
        backend_name=backend_name,
        run_config=run_config,
        options=options,
        logger=logger,
    )
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        while True:
            try:
                yield loop.run_until_complete(async_gen.__anext__())
            except StopAsyncIteration:
                break
    finally:
        loop.close()


def run_job(
    dataset: DatasetInfo,
    samples: Sequence[TestSample],
    backend_name: str,
    run_config: RunConfig,
    options: RunnerConfig,
    logger: Optional[logging.Logger] = None,
) -> List[RunResult]:
    """
    Run a job synchronously and return all results.
    """
    return list(run_stream_job(
        dataset=dataset,
        samples=samples,
        backend_name=backend_name,
        run_config=run_config,
        options=options,
        logger=logger,
    ))


async def _run_single_sample(
    sample: TestSample,
    dataset: DatasetInfo,
    backend: Any,
    backend_name: str,
    run_config: RunConfig,
    options: RunnerConfig,
    semaphore: asyncio.Semaphore,
    rate_limiter: _RateLimiter,
    logger: logging.Logger,
) -> RunResult:
    trace_id = _build_trace_id(options.trace_prefix, sample.id)
    max_attempts = max(1, options.max_retries + 1)
    attempt = 0
    last_error: Optional[RunError] = None

    while attempt < max_attempts:
        attempt += 1
        started_at = datetime.now(timezone.utc)
        perf_start = time.perf_counter()
        request = RunRequest(
            sample=sample,
            run_config=run_config,
            dataset_info=dataset,
            trace_id=trace_id,
            attempt=attempt,
            timeout_seconds=options.timeout_seconds,
        )

        try:
            await rate_limiter.acquire()
            async with semaphore:
                response = await asyncio.wait_for(
                    backend.send(request), timeout=options.timeout_seconds
                )
            latency_ms = (time.perf_counter() - perf_start) * 1000.0
            completed_at = datetime.now(timezone.utc)
            logger.debug("sample=%s status=ok attempts=%d", sample.id, attempt)
            return RunResult(
                sample_id=sample.id,
                dataset_id=dataset.dataset_id,
                backend=backend_name,
                run_config=run_config,
                request_messages=sample.messages,
                request_context={
                    "sample_tags": sample.tags,
                    "sample_metadata": sample.metadata,
                    "attempt": attempt,
                },
                response=response,
                status=RunResultStatus.OK,
                latency_ms=latency_ms,
                started_at=started_at,
                completed_at=completed_at,
                attempts=attempt,
                trace_id=trace_id,
            )
        except asyncio.TimeoutError:
            logger.warning("sample=%s attempt=%d timeout", sample.id, attempt)
            last_error = RunError(
                message="Request timed out",
                error_type="timeout",
                retryable=True,
            )
        except BackendError as exc:
            logger.warning(
                "sample=%s attempt=%d backend_error type=%s retryable=%s",
                sample.id,
                attempt,
                exc.error_type,
                exc.retryable,
            )
            last_error = RunError(
                message=exc.message,
                error_type=exc.error_type,
                status_code=exc.status_code,
                retryable=exc.retryable,
                details=exc.details,
            )
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.exception("sample=%s unexpected error", sample.id)
            last_error = RunError(
                message=str(exc) or exc.__class__.__name__,
                error_type="exception",
                retryable=False,
            )

        latency_ms = (time.perf_counter() - perf_start) * 1000.0
        completed_at = datetime.now(timezone.utc)
        should_retry = bool(last_error and last_error.retryable and attempt < max_attempts)
        if should_retry:
            await asyncio.sleep(_calc_backoff(attempt, options))
            continue

        status = _infer_status(last_error)
        return RunResult(
            sample_id=sample.id,
            dataset_id=dataset.dataset_id,
            backend=backend_name,
            run_config=run_config,
            request_messages=sample.messages,
            request_context={
                "sample_tags": sample.tags,
                "sample_metadata": sample.metadata,
                "attempt": attempt,
            },
            response=None,
            status=status,
            latency_ms=latency_ms,
            started_at=started_at,
            completed_at=completed_at,
            attempts=attempt,
            trace_id=trace_id,
            error=last_error,
        )

    # Should never reach here
    raise RuntimeError("Execution loop exited unexpectedly")


def _calc_backoff(attempt: int, options: RunnerConfig) -> float:
    base = options.retry_backoff_factor ** max(0, attempt - 1)
    jitter = random.random() * options.retry_backoff_jitter
    return base + jitter


def _infer_status(error: Optional[RunError]) -> RunResultStatus:
    if error is None:
        return RunResultStatus.OK
    if error.error_type == "timeout":
        return RunResultStatus.TIMEOUT
    if error.retryable:
        return RunResultStatus.RETRY
    return RunResultStatus.ERROR


def _build_trace_id(prefix: str, sample_id: str) -> str:
    safe_prefix = prefix or "run"
    return f"{safe_prefix}-{sample_id}-{uuid.uuid4().hex[:8]}"


__all__ = ["RunnerConfig", "run_async_job", "run_job"]


import asyncio
import time

import sys
from unittest.mock import MagicMock

# Mock openai module before importing runner code
sys.modules["openai"] = MagicMock()

from typing import List, AsyncIterator
from chatbot_tester.runner.runner_core import run_async_stream_job, run_job, RunnerOptions
from chatbot_tester.runner.models import DatasetInfo, RunConfig, TestSample, RunResultStatus, RunResult, RunRequest, ChatResponse
from chatbot_tester.runner.backends.base import ChatBackend, backend_registry
from chatbot_tester.runner.runner_context import RunnerContext

class MockStreamingBackend(ChatBackend):
    def __init__(self, context: RunnerContext, delay: float = 0.1):
        super().__init__(context)
        self.delay = delay

    async def send(self, request: RunRequest) -> ChatResponse:
        # Simulate delay
        await asyncio.sleep(self.delay)
        return ChatResponse(text=f"Response for {request.sample.id}")

backend_registry.register("mock_streaming", MockStreamingBackend)

async def test_run_async_stream_job_yields_results():
    dataset = DatasetInfo(dataset_id="test_ds", name="Test Dataset", version="1.0", source="test")
    samples = [
        TestSample(id=f"s{i}", messages=[{"role": "user", "content": "hello"}]) 
        for i in range(5)
    ]
    run_config = RunConfig(
        backend="mock_streaming",
        backend_options={"delay": 0.1}
    )
    options = RunnerOptions(max_concurrency=2, timeout_seconds=2.0)

    results = []
    start_time = time.time()
    
    # We expect results to come in chunks due to concurrency limit
    async for result in run_async_stream_job(dataset, samples, "mock_streaming", run_config, options):
        results.append(result)
        print(f"Received result for {result.sample_id} at {time.time() - start_time:.2f}s")
    
    assert len(results) == 5
    assert all(r.status == RunResultStatus.OK for r in results)
    assert all(r.response.text.startswith("Response for") for r in results)

def test_run_job_sync_wrapper():
    dataset = DatasetInfo(dataset_id="test_ds_sync", name="Test Dataset Sync", version="1.0", source="test")
    samples = [
        TestSample(id=f"s{i}", messages=[{"role": "user", "content": "hello"}]) 
        for i in range(3)
    ]
    run_config = RunConfig(
        backend="mock_streaming",
        backend_options={"delay": 0.05}
    )
    options = RunnerOptions(max_concurrency=3)

    results = run_job(dataset, samples, "mock_streaming", run_config, options)
    
    assert len(results) == 3
    assert all(r.status == RunResultStatus.OK for r in results)

if __name__ == "__main__":
    # Allow running this file directly for manual verification
    asyncio.run(test_run_async_stream_job_yields_results())
    test_run_job_sync_wrapper()
    print("All tests passed!")

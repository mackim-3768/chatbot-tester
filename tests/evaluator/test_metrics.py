
import json
from unittest.mock import MagicMock, patch

import pytest
from lm_eval_so.evaluator.domain import RunRecord, TestSampleRecord
from lm_eval_so.evaluator.metrics import ActiveLLMJudgeMetric, EmbeddingSimilarityMetric

@pytest.fixture
def sample_record():
    return TestSampleRecord(
        id="s1",
        messages=[{"role": "user", "content": "Hello"}],
        expected="Hi there",
        tags=[],
        metadata={}
    )

@pytest.fixture
def run_record():
    return RunRecord(
        sample_id="s1",
        dataset_id="d1",
        backend="openai",
        run_config={},
        response_text="Hello!",
        status="ok",
        latency_ms=100.0,
        trace_id="t1",
        attempts=1
    )

def test_active_llm_judge(sample_record, run_record):
    metric = ActiveLLMJudgeMetric(name="judge", parameters={"api_key": "dummy"})

    with patch("lm_eval_so.evaluator.metrics.active_llm_judge.OpenAI") as MockOpenAI:
        mock_resp = MagicMock()
        mock_resp.choices[0].message.content = '{"score": 5, "reason": "Perfect"}'
        MockOpenAI.return_value.chat.completions.create.return_value = mock_resp

        score = metric.score(sample_record, run_record)
        assert score.value == 1.0  # 5/5
        assert score.detail["reason"] == "Perfect"

def test_embedding_similarity(sample_record, run_record):
    metric = EmbeddingSimilarityMetric(name="emb", parameters={"api_key": "dummy"})

    with patch("lm_eval_so.evaluator.metrics.embedding_similarity.OpenAI") as MockOpenAI:
        mock_emb = MagicMock()
        mock_emb.data[0].embedding = [1.0, 0.0, 0.0]
        MockOpenAI.return_value.embeddings.create.return_value = mock_emb

        score = metric.score(sample_record, run_record)
        # dot([1,0,0], [1,0,0]) = 1.0
        assert score.value == 1.0

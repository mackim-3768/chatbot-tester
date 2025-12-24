
import shutil
from pathlib import Path
from unittest.mock import MagicMock

from chatbot_tester.evaluator.domain import EvaluationReport, EvaluationResult, ExperimentMetadata, MetricSummary
from chatbot_tester.evaluator.report.html_reporter import HtmlReporter

def test_html_reporter_generation(tmp_path):
    report = EvaluationReport(
        experiment=ExperimentMetadata(
            dataset=MagicMock(dataset_id="test_ds", version="v1"),
            run_config={"backend": "mock", "model": "mock-v1"},
            evaluator_config={}
        ),
        summaries=[
            MetricSummary(metric="active_llm_judge", mean=0.8, std=0.1, sample_count=10)
        ],
        breakdowns=[],
        error_cases=[],
        llm_judge_details=[]
    )
    result = EvaluationResult(scores=[], report=report)

    out_dir = tmp_path / "html_report"
    reporter = HtmlReporter()
    reporter.write(result, out_dir)

    assert (out_dir / "report.html").exists()
    content = (out_dir / "report.html").read_text(encoding="utf-8")
    assert "Evaluation Report" in content
    assert "active_llm_judge" in content

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Iterable, List, Optional, Sequence

from ..domain import EvalScore, LLMJudgeDetail, RunRecord, TestSampleRecord


class Metric(ABC):
    """Base metric abstraction.

    Description:
        Base class for implementing evaluation logic. Metrics take a test sample and 
        a run record (run result) and produce a numerical score and metadata.

    When to use:
        Inherit from this class to define custom evaluation logic, whether it's a 
        simple deterministic function (e.g. length check) or a complex LLM-based 
        judgement.

    Example:
        ```python
        class MyLengthMetric(Metric):
            def score(self, sample: TestSampleRecord, run: RunRecord) -> EvalScore:
                 val = len(run.response_content)
                 return self.make_score(sample, value=val)
        ```
    """

    requires_reference: bool = False
    """Whether this metric needs the reference/expected answer to compute."""

    def __init__(self, *, name: str, parameters: Optional[Dict[str, Any]] = None) -> None:
        """Initialize the metric.

        Args:
            name: Display name of the metric.
            parameters: Optional configuration parameters for the metric.
        """
        self.name = name
        self.parameters = dict(parameters or {})

    @abstractmethod
    def score(self, sample: TestSampleRecord, run: RunRecord) -> EvalScore:
        """Compute the score for a single sample.
        
        @extension-point: Must override this method to calculate the score.

        Args:
            sample: The test sample input.
            run: The result of running the model on the sample.

        Returns:
            EvalScore: The computed score object.
        """
        raise NotImplementedError

    def make_score(self, sample: TestSampleRecord, *, value: float, detail: Optional[Dict[str, Any]] = None) -> EvalScore:
        """Factory method to create a standardized EvalScore.

        Args:
            sample: The test sample record.
            value: The numeric value of the metric.
            detail: Optional dictionary of extra details (e.g. reasoning).

        Returns:
            EvalScore: Populated score object.
        """
        return EvalScore(
            sample_id=sample.id,
            metric=self.name,
            value=float(value),
            tags=list(sample.tags),
            language=sample.language,
            length_bucket=sample.length_bucket,
            detail=detail or {},
        )

    def build_llm_judge_details(self, scores: Sequence[EvalScore]) -> List[LLMJudgeDetail]:
        """Convert scores into detailed LLM judge reports if applicable.
        
        @extension-point: Override this if your metric produces complex LLM-based reasoning 
        that should be displayed in a specialized UI view.

        Args:
            scores: A list of scores produced by this metric.

        Returns:
            List[LLMJudgeDetail]: A list of detailed objects for reporting.
        """
        return []


__all__ = ["Metric"]

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import List

from .base import Reporter, ensure_output_dir
from ..domain import EvaluationResult


class JsonReporter(Reporter):
    def write(self, result: EvaluationResult, output_dir: Path) -> List[Path]:
        out_dir = ensure_output_dir(output_dir)

        summary_path = out_dir / "summary.json"
        scores_path = out_dir / "scores.jsonl"

        report = result.report
        payload = {
            "experiment": asdict(report.experiment),
            "overall_metrics": [asdict(s) for s in report.summaries],
            "breakdown": [asdict(b) for b in report.breakdowns],
            "error_cases": [asdict(e) for e in report.error_cases],
            "llm_judge_details": [asdict(d) for d in report.llm_judge_details],
        }

        with summary_path.open("w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

        with scores_path.open("w", encoding="utf-8") as f:
            for score in result.scores:
                json.dump(asdict(score), f, ensure_ascii=False)
                f.write("\n")

        return [summary_path, scores_path]


__all__ = ["JsonReporter"]

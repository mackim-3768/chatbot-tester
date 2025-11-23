from __future__ import annotations

from pathlib import Path
from typing import Dict, List

from .base import Reporter, ensure_output_dir
from ..domain import EvaluationResult


class MarkdownReporter(Reporter):
    def write(self, result: EvaluationResult, output_dir: Path) -> List[Path]:
        out_dir = ensure_output_dir(output_dir)
        md_path = out_dir / "report.md"

        report = result.report
        exp = report.experiment

        lines: List[str] = []
        lines.append("# Experiment metadata")
        lines.append("")
        lines.append(f"- dataset_id: `{exp.dataset.dataset_id}`")
        lines.append(f"- name: `{exp.dataset.name}`")
        lines.append(f"- version: `{exp.dataset.version}`")
        lines.append(f"- source: `{exp.dataset.source}`")
        lines.append("")

        lines.append("## Overall metrics summary")
        lines.append("")
        lines.append("| metric | mean | std | sample_count |")
        lines.append("| --- | ---: | ---: | ---: |")
        for s in report.summaries:
            lines.append(f"| {s.metric} | {s.mean:.4f} | {s.std:.4f} | {s.sample_count} |")
        if not report.summaries:
            lines.append("(no metrics computed)")
        lines.append("")

        lines.append("## Breakdown")
        lines.append("")
        if not report.breakdowns:
            lines.append("(no breakdowns)")
        else:
            # Group by dimension.
            by_dim: Dict[str, List] = {}
            for b in report.breakdowns:
                by_dim.setdefault(b.dimension, []).append(b)
            for dim, rows in by_dim.items():
                lines.append(f"### {dim}")
                lines.append("")
                lines.append("| metric | bucket | mean | std | sample_count |")
                lines.append("| --- | --- | ---: | ---: | ---: |")
                for b in rows:
                    lines.append(
                        f"| {b.metric} | {b.bucket} | {b.mean:.4f} | {b.std:.4f} | {b.sample_count} |"
                    )
                lines.append("")

        lines.append("## Error cases / Low-score samples")
        lines.append("")
        if not report.error_cases:
            lines.append("(no error cases)")
        else:
            for e in report.error_cases:
                lines.append(
                    f"- sample_id=`{e.sample_id}` status=`{e.status}` "
                    f"trace_id=`{e.trace_id}` latency_ms={e.latency_ms} backend={e.backend}"
                )
        lines.append("")

        lines.append("## LLM Judge details")
        lines.append("")
        if not report.llm_judge_details:
            lines.append("(no LLM-judge metrics)")
        else:
            for d in report.llm_judge_details:
                lines.append("- metric: `{}`".format(d.metric))
                lines.append(
                    f"  - prompt_id: `{d.prompt_id}` version: `{d.prompt_version}` language: `{d.language}`"
                )
                lines.append(f"  - criteria: {', '.join(d.criteria)}")
                lines.append(f"  - sample_count: {d.sample_count}")
        lines.append("")

        with md_path.open("w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        return [md_path]


__all__ = ["MarkdownReporter"]

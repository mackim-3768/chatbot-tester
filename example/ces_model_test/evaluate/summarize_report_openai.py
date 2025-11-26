from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from openai import OpenAI


SYSTEM_PROMPT = """You are an expert analyst of model evaluation reports.\nYou receive a JSON summary of an experiment (dataset, run_config, metrics, breakdowns).\nWrite concise but information-dense qualitative assessments.\nUse the provided structure exactly.\n"""


SUMMARY_INSTRUCTIONS = """Using the JSON report below, write three sections:\n\n# Overall qualitative assessment\n- Summarize overall performance across all topics and languages.\n- Mention key strengths and weaknesses.\n- Highlight notable metric patterns (including LLM-judge metrics).\n\n# Per-topic qualitative assessment\nFor each topic (e.g., 번역, 문체 변환, 요약):\n- Summarize performance.\n- Describe typical errors or failure modes.\n- Give concrete improvement suggestions.\n\n# Topic-language qualitative assessment\nFor each (topic, language) bucket that appears in the breakdowns:\n- Summarize how the model performs for that (topic, language).\n- Compare with other languages for the same topic when relevant.\n- Point out language-specific issues or strengths.\n\nConstraints:\n- Base your analysis only on the metrics and breakdowns in the JSON.\n- Be honest when information is insufficient (e.g., "no data").\n- Write in Markdown.\n"""


def summarize_report(summary_path: Path, output_path: Path, model: str) -> None:
    with summary_path.open("r", encoding="utf-8") as f:
        summary_obj = json.load(f)

    client = OpenAI()
    completion = client.chat.completions.create(
        model=model,
        temperature=0.2,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": SUMMARY_INSTRUCTIONS
                + "\n\n===== REPORT JSON START =====\n"
                + json.dumps(summary_obj, ensure_ascii=False, indent=2)
                + "\n===== REPORT JSON END =====\n",
            },
        ],
    )

    content = completion.choices[0].message.content or ""
    with output_path.open("w", encoding="utf-8") as f:
        f.write(content)


def main() -> None:
    base_dir = Path(__file__).resolve().parents[1]
    default_summary = base_dir / "reports" / "adb_cli" / "summary.json"
    default_output = base_dir / "reports" / "adb_cli" / "qualitative_summary.md"

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--summary",
        type=str,
        default=str(default_summary),
        help="Path to summary.json produced by JsonReporter.",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(default_output),
        help="Path to write Markdown qualitative summary.",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=os.environ.get("OPENAI_SUMMARY_MODEL", "gpt-4o-mini"),
        help="OpenAI model name to use for summarization.",
    )
    args = parser.parse_args()

    summarize_report(Path(args.summary), Path(args.output), args.model)


if __name__ == "__main__":  # pragma: no cover
    main()

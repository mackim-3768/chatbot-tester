from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Optional

from .pipeline import PipelineOptions, run_pipeline


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="gen-dataset", description="Chatbot dataset generator")
    p.add_argument("--input", required=True, help="Input file path (csv/jsonl)")
    p.add_argument("--input-format", choices=["csv", "jsonl"], default=None)
    p.add_argument("--output-dir", required=True, help="Output directory")

    p.add_argument("--dataset-id", required=True)
    p.add_argument("--name", required=True)
    p.add_argument("--version", required=True)
    p.add_argument("--source", default=None, help="Free-form source info (string or JSON)")

    # mapping
    p.add_argument("--id-col", default=None)
    p.add_argument("--csv-user-col", dest="user_col", default=None)
    p.add_argument("--csv-expected-col", dest="expected_col", default=None)
    p.add_argument("--csv-system-col", dest="system_col", default=None)
    p.add_argument("--csv-tags-col", dest="tags_col", default=None)
    p.add_argument("--csv-tags-sep", dest="tags_sep", default="|")
    p.add_argument("--csv-language-col", dest="language_col", default=None)

    # filters
    p.add_argument("--min-len", type=int, default=None)
    p.add_argument("--max-len", type=int, default=None)

    # sampling
    p.add_argument("--sample-size", type=int, default=0)
    p.add_argument("--sample-random", action="store_true")

    return p


def main(argv: Optional[list[str]] = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)

    # try to parse --source as JSON if looks like JSON; else keep string
    source_obj = args.source
    if isinstance(source_obj, str):
        s = source_obj.strip()
        if s.startswith("{") or s.startswith("["):
            try:
                source_obj = json.loads(s)
            except Exception:
                source_obj = args.source

    opts = PipelineOptions(
        input_path=Path(args.input),
        input_format=args.input_format,
        output_dir=Path(args.output_dir),
        dataset_id=args.dataset_id,
        name=args.name,
        version=args.version,
        source=source_obj,
        id_col=args.id_col,
        user_col=args.user_col,
        expected_col=args.expected_col,
        system_col=args.system_col,
        tags_col=args.tags_col,
        tags_sep=args.tags_sep,
        language_col=args.language_col,
        min_len=args.min_len,
        max_len=args.max_len,
        sample_size=int(args.sample_size or 0),
        sample_random=bool(args.sample_random),
    )

    out_dir = run_pipeline(opts)
    print(str(out_dir))


if __name__ == "__main__":
    main()

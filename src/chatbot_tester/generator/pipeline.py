from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from .loaders import load_csv, load_jsonl
from .transformers import canonicalize_rows, filter_by_length, sample_list
from .writers import write_jsonl, build_metadata, write_metadata
from .schema import sample_schema
from .types import TestSample
from .utils import ensure_dir


@dataclass
class PipelineOptions:
    input_path: Path
    input_format: Optional[str]  # "csv" | "jsonl" | None(auto)
    output_dir: Path
    dataset_id: str
    name: str
    version: str
    source: Optional[Any]
    id_col: Optional[str]
    user_col: Optional[str]
    expected_col: Optional[str]
    system_col: Optional[str]
    tags_col: Optional[str]
    tags_sep: str
    language_col: Optional[str]
    min_len: Optional[int]
    max_len: Optional[int]
    sample_size: int
    sample_random: bool


def _load_rows(opts: PipelineOptions):
    fmt = (opts.input_format or opts.input_path.suffix.lstrip(".").lower())
    if fmt == "csv":
        return list(load_csv(opts.input_path))
    if fmt == "jsonl":
        return list(load_jsonl(opts.input_path))
    raise ValueError(f"Unsupported input format: {fmt}")


def _canonicalize(rows: Sequence[Dict[str, Any]], opts: PipelineOptions) -> List[TestSample]:
    return canonicalize_rows(
        rows,
        id_col=opts.id_col,
        user_col=opts.user_col,
        expected_col=opts.expected_col,
        system_col=opts.system_col,
        tags_col=opts.tags_col,
        tags_sep=opts.tags_sep,
        language_col=opts.language_col,
    )


def _to_dicts(samples: Sequence[TestSample]):
    return [s.to_dict() for s in samples]


def run_pipeline(opts: PipelineOptions) -> Path:
    rows = _load_rows(opts)
    samples = _canonicalize(rows, opts)

    if opts.min_len is not None or opts.max_len is not None:
        samples = filter_by_length(samples, min_len=opts.min_len, max_len=opts.max_len)

    if opts.sample_size and opts.sample_size > 0:
        samples = sample_list(samples, opts.sample_size, randomize=opts.sample_random)

    records = _to_dicts(samples)

    out_root = opts.output_dir / f"{opts.dataset_id}_{opts.version}"
    ensure_dir(out_root)

    write_jsonl(records, out_root / "test.jsonl")

    meta = build_metadata(
        dataset_id=opts.dataset_id,
        name=opts.name,
        version=opts.version,
        source=opts.source,
        samples=records,
        filters={k: v for k, v in {
            "min_len": opts.min_len,
            "max_len": opts.max_len,
        }.items() if v is not None},
        sampling={
            "sample_size": opts.sample_size,
            "sample_random": opts.sample_random,
        },
        repo_dir=Path(__file__).resolve().parents[2],
    )
    write_metadata(meta, out_root / "metadata.json")

    # schema
    from json import dump
    with (out_root / "schema.json").open("w", encoding="utf-8") as f:
        dump(sample_schema(), f, ensure_ascii=False, indent=2)

    return out_root

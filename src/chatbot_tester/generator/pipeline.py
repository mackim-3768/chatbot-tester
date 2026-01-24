from __future__ import annotations

import abc
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from .loaders import load_csv, load_jsonl
from .transformers import canonicalize_rows, filter_by_length, sample_list
from .writers import build_metadata
from .schema import sample_schema
from chatbot_tester.core.models import TestSample
from chatbot_tester.core.storage import LocalFileSystemStorage


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


class PipelineStep(abc.ABC):
    """Abstract base class for pipeline steps."""
    @abc.abstractmethod
    def process(self, data: Any) -> Any:
        pass


class LoadRowsStep(PipelineStep):
    def __init__(self, opts: PipelineOptions):
        self.opts = opts

    def process(self, _=None) -> List[Dict[str, Any]]:
        fmt = (self.opts.input_format or self.opts.input_path.suffix.lstrip(".").lower())
        if fmt == "csv":
            return list(load_csv(self.opts.input_path))
        if fmt == "jsonl":
            return list(load_jsonl(self.opts.input_path))
        raise ValueError(f"Unsupported input format: {fmt}")


class CanonicalizeStep(PipelineStep):
    def __init__(self, opts: PipelineOptions):
        self.opts = opts

    def process(self, rows: Sequence[Dict[str, Any]]) -> List[TestSample]:
        return canonicalize_rows(
            rows,
            id_col=self.opts.id_col,
            user_col=self.opts.user_col,
            expected_col=self.opts.expected_col,
            system_col=self.opts.system_col,
            tags_col=self.opts.tags_col,
            tags_sep=self.opts.tags_sep,
            language_col=self.opts.language_col,
        )


class FilterStep(PipelineStep):
    def __init__(self, opts: PipelineOptions):
        self.opts = opts

    def process(self, samples: List[TestSample]) -> List[TestSample]:
        if self.opts.min_len is not None or self.opts.max_len is not None:
            return filter_by_length(samples, min_len=self.opts.min_len, max_len=self.opts.max_len)
        return samples


class SampleStep(PipelineStep):
    def __init__(self, opts: PipelineOptions):
        self.opts = opts

    def process(self, samples: List[TestSample]) -> List[TestSample]:
        if self.opts.sample_size and self.opts.sample_size > 0:
            return sample_list(samples, self.opts.sample_size, randomize=self.opts.sample_random)
        return samples


class SaveStep(PipelineStep):
    def __init__(self, opts: PipelineOptions):
        self.opts = opts

    def process(self, samples: List[TestSample]) -> Path:
        records = [s.to_dict() for s in samples]

        storage = LocalFileSystemStorage(self.opts.output_dir)

        dataset_dir = f"{self.opts.dataset_id}_{self.opts.version}"
        jsonl_key = f"{dataset_dir}/test.jsonl"
        meta_key = f"{dataset_dir}/metadata.json"
        schema_key = f"{dataset_dir}/schema.json"

        # Save test samples
        storage.save_jsonl(jsonl_key, records)

        # Build and save metadata
        meta = build_metadata(
            dataset_id=self.opts.dataset_id,
            name=self.opts.name,
            version=self.opts.version,
            source=self.opts.source,
            samples=records,
            filters={k: v for k, v in {
                "min_len": self.opts.min_len,
                "max_len": self.opts.max_len,
            }.items() if v is not None},
            sampling={
                "sample_size": self.opts.sample_size,
                "sample_random": self.opts.sample_random,
            },
            repo_dir=Path(__file__).resolve().parents[2],
        )
        storage.save_json(meta_key, meta)

        # Save schema
        storage.save_json(schema_key, sample_schema())

        return Path(storage.get_path(dataset_dir))


class GeneratorPipeline:
    def __init__(self, steps: List[PipelineStep]):
        self.steps = steps

    def run(self, initial_input: Any = None) -> Any:
        data = initial_input
        for step in self.steps:
            data = step.process(data)
        return data


def run_pipeline(opts: PipelineOptions) -> Path:
    pipeline = GeneratorPipeline([
        LoadRowsStep(opts),
        CanonicalizeStep(opts),
        FilterStep(opts),
        SampleStep(opts),
        SaveStep(opts),
    ])
    return pipeline.run()

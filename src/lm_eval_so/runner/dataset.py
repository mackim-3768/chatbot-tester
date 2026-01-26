from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any

from .models import DatasetInfo, TestSample, ensure_messages


def _resolve_dataset_paths(dataset: Path, metadata: Optional[Path]) -> Tuple[Path, Optional[Path]]:
    if dataset.is_dir():
        jsonl_path = dataset / "test.jsonl"
        meta_path = metadata or dataset / "metadata.json"
    else:
        jsonl_path = dataset
        meta_path = metadata
    return jsonl_path, meta_path


def _load_metadata(meta_path: Optional[Path]) -> Optional[Dict[str, Any]]:
    if meta_path is None or not meta_path.exists():
        return None
    with meta_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _build_dataset_info(meta: Optional[Dict[str, Any]]) -> DatasetInfo:
    if not meta:
        return DatasetInfo(dataset_id=None, name=None, version=None, source=None, metadata=None)
    return DatasetInfo(
        dataset_id=meta.get("dataset_id"),
        name=meta.get("name"),
        version=meta.get("version"),
        source=meta.get("source"),
        metadata=meta,
    )


def load_dataset(dataset_path: Path, metadata_path: Optional[Path] = None) -> Tuple[DatasetInfo, List[TestSample]]:
    jsonl_path, meta_path = _resolve_dataset_paths(dataset_path, metadata_path)

    if not jsonl_path.exists():
        raise FileNotFoundError(f"Dataset samples file not found: {jsonl_path}")

    samples: List[TestSample] = []
    with jsonl_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            record["messages"] = [m.to_dict() for m in ensure_messages(record.get("messages", []))]
            samples.append(TestSample.from_dict(record))

    meta = _load_metadata(meta_path)
    dataset_info = _build_dataset_info(meta)
    return dataset_info, samples


__all__ = ["load_dataset"]

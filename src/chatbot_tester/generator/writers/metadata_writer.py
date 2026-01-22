from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional
import json

from ..utils import now_iso, get_pkg_version, get_git_commit


def _collect_tag_stats(samples: Iterable[Dict[str, Any]]) -> Dict[str, int]:
    c: Counter[str] = Counter()
    for s in samples:
        tags = s.get("tags")
        if isinstance(tags, list):
            c.update([str(t) for t in tags])
    return dict(c)


def _collect_language_stats(samples: Iterable[Dict[str, Any]]) -> Dict[str, int]:
    c: Counter[str] = Counter()
    for s in samples:
        md = s.get("metadata")
        if isinstance(md, dict):
            lang = md.get("language")
            if lang:
                c.update([str(lang)])
    return dict(c)


def build_metadata(
    *,
    dataset_id: str,
    name: str,
    version: str,
    source: Optional[Any],
    samples: List[Dict[str, Any]],
    filters: Optional[Dict[str, Any]] = None,
    sampling: Optional[Dict[str, Any]] = None,
    repo_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    commit = get_git_commit(repo_dir)
    return {
        "dataset_id": dataset_id,
        "name": name,
        "version": version,
        "created_at": now_iso(),
        "source": source,
        "generator_version": get_pkg_version(),
        "generator_commit": commit,
        "generator_code_commit": commit,
        "sample_count": len(samples),
        "filters": filters or {},
        "sampling": sampling or {},
        "tag_stats": _collect_tag_stats(samples),
        "language_stats": _collect_language_stats(samples),
    }



from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, Mapping, Any


def write_jsonl(records: Iterable[Mapping[str, Any]], path: str | Path, encoding: str = "utf-8") -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding=encoding) as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

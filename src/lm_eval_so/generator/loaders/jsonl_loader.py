from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Iterable, Any


def load_jsonl(path: str | Path, encoding: str = "utf-8") -> Iterable[Dict[str, Any]]:
    p = Path(path)
    with p.open("r", encoding=encoding) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)

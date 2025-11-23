from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, Iterable


def load_csv(path: str | Path, encoding: str = "utf-8") -> Iterable[Dict[str, str]]:
    p = Path(path)
    with p.open("r", encoding=encoding, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            yield {k: (v if v is not None else "") for k, v in row.items()}

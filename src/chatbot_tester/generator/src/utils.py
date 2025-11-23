from __future__ import annotations

import datetime as _dt
import hashlib
import json
import os
import subprocess
from pathlib import Path
from typing import Iterable, List, Optional


def now_iso() -> str:
    return _dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def gen_id_from_messages(messages: List[dict]) -> str:
    payload = "\n".join(f"{m.get('role','')}::{m.get('content','')}" for m in messages)
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()  # nosec - non-crypto id


def get_pkg_version() -> str:
    try:
        from . import __version__
        return __version__
    except Exception:
        return "unknown"


def get_git_commit(repo_dir: Optional[Path] = None) -> Optional[str]:
    try:
        cwd = str(repo_dir) if repo_dir is not None else None
        out = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=cwd)
        return out.decode("utf-8").strip()
    except Exception:
        return os.environ.get("GENERATOR_CODE_COMMIT")


def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)

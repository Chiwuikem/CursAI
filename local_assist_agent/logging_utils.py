import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from .config import LOG_FILE, LOG_JSONL

def new_run_id() -> str:
    """Short stable ID per CLI run (used to correlate events)."""
    return uuid.uuid4().hex[:8]

def _json_default(o: Any):
    if isinstance(o, Path):
        return str(o)
    return str(o)

def log_line(msg: str, run_id: Optional[str] = None, level: str = "INFO"):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    rid = f" [run:{run_id}]" if run_id else ""
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(f"[{ts}] {level}{rid} {msg}\n")

def log_event(run_id: str, event: str, data: dict | None = None, level: str = "INFO"):
    """Write a structured JSONL event (one JSON per line)."""
    ts = datetime.now().isoformat(timespec="seconds")
    payload = {
        "ts": ts,
        "run_id": run_id,
        "level": level,
        "event": event,
        "data": data or {},
    }
    LOG_JSONL.parent.mkdir(parents=True, exist_ok=True)
    with LOG_JSONL.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, default=_json_default) + "\n")

from pathlib import Path
import sys
import pytest

# Make the project importable
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import local_assist_agent.logging_utils as lu  # the module we monkeypatch

@pytest.fixture
def temp_logs(tmp_path, monkeypatch):
    log_dir = tmp_path / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "agent.log"
    jsonl = log_dir / "agent.jsonl"

    # Redirect logging destinations to temp files
    monkeypatch.setattr(lu, "LOG_FILE", log_file, raising=False)
    monkeypatch.setattr(lu, "LOG_JSONL", jsonl, raising=False)

    # Make executor use THIS monkeypatched module
    import local_assist_agent.executor as ex
    monkeypatch.setattr(ex, "L", lu, raising=False)

    return log_file, jsonl

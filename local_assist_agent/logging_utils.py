from datetime import datetime
from .config import LOG_FILE

def log_line(msg: str):
    ts = datetime.now().strftime("%%Y-%%m-%%d %%H:%%M:%%S")
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(f"[{ts}] {msg}\n")


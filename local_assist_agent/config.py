from pathlib import Path

# Operate only within these roots by default
DEFAULT_SCOPES = [
    str(Path.home() / "Downloads"),
    str(Path.home() / "Desktop"),
    str(Path.home() / "Documents"),
]

# Logs
LOG_DIR = Path.home() / ".local_assist_agent" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "agent.log"
LOG_JSONL = LOG_DIR / "agent.jsonl"  # NEW: structured events

# Paths that require extra confirmation (prevent accidents)
RISKY_PATTERNS = [
    ".ssh", "AppData", "Library", "Program Files", "Windows", "System32",
    "/bin", "/sbin", "/usr", "/etc"
]

# Safety thresholds & confirmation phrases
MAX_DELETE_COUNT = 50               # files
MAX_TOTAL_DELETE_MB = 1024          # 1 GB

EXTRA_CONFIRM_PHRASE = "I UNDERSTAND"       # risky/system-like paths
BULK_CONFIRM_PHRASE  = "I ACCEPT THE RISK"  # large selections
# Max number of preview windows to open automatically (per run)
PREVIEW_MAX_WINDOWS = 10

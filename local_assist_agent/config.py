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

# Paths that require extra confirmation (prevent accidents)
RISKY_PATTERNS = [
    ".ssh", "AppData", "Library", "Program Files", "Windows", "System32",
    "/bin", "/sbin", "/usr", "/etc"
]

# --- NEW: Safety thresholds & confirmation phrases ---
# If user selects more than this many files OR the total size exceeds this limit,
# require an extra typed confirmation before proceeding.
MAX_DELETE_COUNT = 50               # files
MAX_TOTAL_DELETE_MB = 1024          # 1 GB

# Unified confirm phrases (change here if you want different wording)
EXTRA_CONFIRM_PHRASE = "I UNDERSTAND"        # for risky/system-like paths
BULK_CONFIRM_PHRASE  = "I ACCEPT THE RISK"   # for large selections

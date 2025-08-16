from pathlib import Path

DEFAULT_SCOPES = [str(Path.home() / "Downloads"), str(Path.home() / "Desktop"), str(Path.home() / "Documents")]
LOG_DIR = Path.home() / ".local_assist_agent" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "agent.log"
RISKY_PATTERNS = [".ssh","AppData","Library","Program Files","Windows","System32","/bin","/sbin","/usr","/etc"]
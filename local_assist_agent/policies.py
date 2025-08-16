from pathlib import Path
from .config import DEFAULT_SCOPES, RISKY_PATTERNS
def in_allowed_scopes(path: Path, scopes = DEFAULT_SCOPES) -> bool:
   p = path.resolve()
   for root in scopes:
       try:
           if p.is_relative_to(Path(root).resolve()): return True
       except Exception:
           if str(p).startswith(str(Path(root).resolve())): return True
   return False
def requires_extra_confirmation(path: Path) -> bool:
   s = str(path).lower()
   return any(pat.lower() in s for pat in RISKY_PATTERNS)
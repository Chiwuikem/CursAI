import time
from pathlib import Path
from typing import Iterable, Optional, List, Tuple, Dict, Any

from send2trash import send2trash
from ..schemas import FileHit

def find_recent(
    roots: Iterable[str],
    patterns: Iterable[str] = ("*.exe",),
    days: Optional[int] = 14,
    name_hint: Optional[str] = None,
    newer_than_days: Optional[int] = None,
    older_than_days: Optional[int] = None,
    min_size_kb: Optional[int] = None,
    max_size_kb: Optional[int] = None,
) -> List[FileHit]:
    """Files only (ignore dirs); sorted newest-first; optional time/size filters."""
    now = time.time()

    if newer_than_days is None and older_than_days is None and days is not None:
        newer_than_days = days  # legacy behavior

    newer_cutoff = None if newer_than_days is None else now - newer_than_days * 86400
    older_cutoff = None if older_than_days is None else now - older_than_days * 86400

    hits: List[FileHit] = []
    for root in roots:
        rp = Path(root).expanduser()
        if not rp.exists():
            continue
        for pat in patterns:
            for p in rp.rglob(pat):
                try:
                    if not p.is_file():
                        continue
                except Exception:
                    continue
                try:
                    st = p.stat()
                except Exception:
                    continue
                mtime = st.st_mtime
                size_bytes = st.st_size

                if newer_cutoff is not None and not (mtime >= newer_cutoff):
                    continue
                if older_cutoff is not None and not (mtime <= older_cutoff):
                    continue
                if min_size_kb is not None and not (size_bytes >= min_size_kb * 1024):
                    continue
                if max_size_kb is not None and not (size_bytes <= max_size_kb * 1024):
                    continue
                if name_hint and name_hint.lower() not in p.name.lower():
                    continue

                hits.append(FileHit(path=p, mtime=mtime, size=size_bytes))

    hits.sort(key=lambda h: h.mtime, reverse=True)
    return hits

def move_to_trash(paths: Iterable[Path]) -> Tuple[int, List[str], List[Dict[str, Any]]]:
    """
    Send paths to Recycle Bin. Returns:
      ok_count, list_of_error_strings, detailed_outcomes[{path, ok, error}]
    """
    ok = 0
    errs: List[str] = []
    outcomes: List[Dict[str, Any]] = []

    for p in paths:
        try:
            send2trash(str(p))
            outcomes.append({"path": str(p), "ok": True, "error": None})
            ok += 1
        except Exception as e:
            msg = f"{p}: {e}"
            errs.append(msg)
            outcomes.append({"path": str(p), "ok": False, "error": str(e)})

    return ok, errs, outcomes

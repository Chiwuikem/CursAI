import time
from pathlib import Path
from typing import Iterable, Optional, List, Tuple

from send2trash import send2trash
from ..schemas import FileHit


def find_recent(
    roots: Iterable[str],
    patterns: Iterable[str] = ("*.exe",),
    days: Optional[int] = 14,
    name_hint: Optional[str] = None,
    # NEW filters (all optional; function stays backward-compatible)
    newer_than_days: Optional[int] = None,   # modified within the last N days
    older_than_days: Optional[int] = None,   # modified before N days ago
    min_size_kb: Optional[int] = None,
    max_size_kb: Optional[int] = None,
) -> List[FileHit]:
    """
    Find files inside given roots that match glob `patterns` with optional time/size filters.
    Results are sorted newest-first.

    Compatibility:
      - If only `days` is supplied (legacy), it's treated like `newer_than_days=days`.
    """
    now = time.time()

    if newer_than_days is None and older_than_days is None and days is not None:
        newer_than_days = days  # legacy behavior

    newer_cutoff = None
    older_cutoff = None

    if newer_than_days is not None:
        newer_cutoff = now - newer_than_days * 86400
    if older_than_days is not None:
        older_cutoff = now - older_than_days * 86400

    hits: List[FileHit] = []

    for root in roots:
        rp = Path(root).expanduser()
        if not rp.exists():
            continue

        for pat in patterns:
            for p in rp.rglob(pat):
                try:
                    st = p.stat()
                    mtime = st.st_mtime
                    size_bytes = st.st_size
                except Exception:
                    # permissions / transient errors
                    continue

                # Time filters
                if newer_cutoff is not None and not (mtime >= newer_cutoff):
                    continue
                if older_cutoff is not None and not (mtime <= older_cutoff):
                    continue

                # Size filters (KB)
                if min_size_kb is not None and not (size_bytes >= min_size_kb * 1024):
                    continue
                if max_size_kb is not None and not (size_bytes <= max_size_kb * 1024):
                    continue

                # Name hint (substring)
                if name_hint and name_hint.lower() not in p.name.lower():
                    continue

                hits.append(FileHit(path=p, mtime=mtime, size=size_bytes))

    # newest first
    hits.sort(key=lambda h: h.mtime, reverse=True)
    return hits


def move_to_trash(paths: Iterable[Path]) -> Tuple[int, List[str]]:
    """
    Send the provided paths to the OS Recycle Bin (safe, undoable).
    Returns (count_success, list_of_error_messages).
    """
    ok = 0
    errs: List[str] = []

    for p in paths:
        try:
            send2trash(str(p))
            ok += 1
        except Exception as e:
            errs.append(f"{p}: {e}")

    return ok, errs

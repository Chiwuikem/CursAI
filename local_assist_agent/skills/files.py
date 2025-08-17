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
    # Optional filters (compatible with previous steps)
    newer_than_days: Optional[int] = None,
    older_than_days: Optional[int] = None,
    min_size_kb: Optional[int] = None,
    max_size_kb: Optional[int] = None,
) -> List[FileHit]:
    """
    Find files (files only, not directories) in roots matching glob patterns with optional time/size filters.
    Results are sorted newest-first.
    """
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
                # Safety: only consider files
                try:
                    if not p.is_file():
                        continue
                except Exception:
                    continue

                try:
                    st = p.stat()
                    mtime = st.st_mtime
                    size_bytes = st.st_size
                except Exception:
                    continue  # permissions/transient errors

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

                # Name hint
                if name_hint and name_hint.lower() not in p.name.lower():
                    continue

                hits.append(FileHit(path=p, mtime=mtime, size=size_bytes))

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

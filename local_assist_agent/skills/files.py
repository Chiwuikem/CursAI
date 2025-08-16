import time
from pathlib import Path
from typing import Iterable, Optional, List, Tuple

from send2trash import send2trash

from ..schemas import FileHit


def find_recent(
    roots: Iterable[str],
    patterns: Iterable[str] = ("*.exe",),
    days: int = 14,
    name_hint: Optional[str] = None,
) -> List[FileHit]:
    """
    Find files inside the given root folders that match the glob `patterns`
    and were modified within the last `days`. Results are sorted newest-first.

    roots: e.g., ["C:/Users/you/Downloads", "C:/Users/you/Desktop"]
    patterns: e.g., ["*.exe", "*.zip"]
    days: look-back window
    name_hint: optional substring to filter by filename
    """
    cutoff = time.time() - days * 86400
    hits: List[FileHit] = []

    for root in roots:
        rp = Path(root).expanduser()
        if not rp.exists():
            continue

        for pat in patterns:
            for p in rp.rglob(pat):
                try:
                    st = p.stat()
                except Exception:
                    # permissions / transient errors
                    continue

                if st.st_mtime >= cutoff:
                    if not name_hint or name_hint.lower() in p.name.lower():
                        hits.append(FileHit(path=p, mtime=st.st_mtime, size=st.st_size))

    # newest first
    hits.sort(key=lambda h: h.mtime, reverse=True)
    return hits


def move_to_trash(paths: Iterable[Path]) -> Tuple[int, List[str]]:
    """
    Send the provided paths to the OS Trash / Recycle Bin (safe, undoable).
    Returns a tuple: (count_success, list_of_error_messages).
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

import sys, subprocess, time, re
from pathlib import Path
from collections import defaultdict
from typing import Iterable, Tuple, Optional

from ..config import PREVIEW_MAX_WINDOWS, LOG_DIR

_INVALID = re.compile(r'[<>:"/\\|?*]')

def _safe_name(name: str) -> str:
    # Make a filename that's Windows-safe
    n = _INVALID.sub("_", name)
    return n[:200]

def _win_select(path: Path):
    try:
        subprocess.Popen(["explorer.exe", "/select,", str(path)])
    except Exception:
        subprocess.Popen(["explorer.exe", str(path.parent)])

def _open_folder(folder: Path):
    if sys.platform.startswith("win"):
        subprocess.Popen(["explorer.exe", str(folder)])
    elif sys.platform == "darwin":
        subprocess.Popen(["open", str(folder)])
    else:
        subprocess.Popen(["xdg-open", str(folder)])

def _mac_reveal(path: Path):
    subprocess.Popen(["open", "-R", str(path)])

def _linux_open_folder(path: Path):
    subprocess.Popen(["xdg-open", str(path.parent)])

def _make_shelf(paths: Iterable[Path], run_id: Optional[str]) -> Path:
    """
    Create a 'preview shelf' folder containing .url shortcuts to each file.
    Works without admin. Returns the shelf folder path.
    """
    shelf = LOG_DIR / f"preview_shelf_{run_id or int(time.time())}"
    shelf.mkdir(parents=True, exist_ok=True)
    for p in paths:
        p = Path(p).resolve()
        uri = p.as_uri()
        doturl = shelf / (_safe_name(p.name) + ".url")
        with open(doturl, "w", encoding="utf-8") as f:
            f.write("[InternetShortcut]\n")
            f.write(f"URL={uri}\n")
    return shelf

def preview_paths(paths: Iterable[Path], mode: str = "perfile", run_id: Optional[str] = None) -> Tuple[int, int, Optional[Path]]:
    """
    Open OS file browser to reveal selected files.

    Modes:
      - 'perfile' : highlight each file (Windows/macOS), parent on Linux (may be many windows)
      - 'grouped' : open one window per parent directory
      - 'shelf'   : create a temporary folder with .url shortcuts; open it once (single window)

    Returns (opened_count, skipped_count, shelf_path_or_None).
    """
    ps = [Path(p).resolve() for p in paths if Path(p).exists()]
    if not ps:
        return 0, 0, None

    opened = 0
    skipped = 0

    if mode == "shelf":
        shelf = _make_shelf(ps, run_id)
        _open_folder(shelf)
        return 1, max(0, len(ps) - 1), shelf

    # non-shelf modes
    by_parent = defaultdict(list)
    for p in ps:
        by_parent[p.parent].append(p)

    if mode == "grouped":
        # Open one window per parent folder, capped
        for parent in by_parent.keys():
            if opened >= PREVIEW_MAX_WINDOWS:
                skipped = len(by_parent) - opened
                break
            _open_folder(parent)
            opened += 1
        return opened, skipped, None

    # perfile (default)
    if sys.platform.startswith("win"):
        for p in ps:
            if opened >= PREVIEW_MAX_WINDOWS:
                skipped = len(ps) - opened
                break
            _win_select(p)
            opened += 1
        return opened, skipped, None
    elif sys.platform == "darwin":
        for p in ps:
            if opened >= PREVIEW_MAX_WINDOWS:
                skipped = len(ps) - opened
                break
            _mac_reveal(p)
            opened += 1
        return opened, skipped, None
    else:
        # linux fallback: one window per parent
        for parent in by_parent.keys():
            if opened >= PREVIEW_MAX_WINDOWS:
                skipped = len(by_parent) - opened
                break
            _linux_open_folder(parent / "dummy")  # function expects a path; we pass a child
            opened += 1
        return opened, skipped, None

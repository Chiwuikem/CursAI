import sys
import subprocess
from pathlib import Path
from collections import defaultdict
from typing import Iterable, Tuple

from ..config import PREVIEW_MAX_WINDOWS

def _win_select(path: Path):
    # explorer.exe /select,"C:\path\to\file.ext"
    try:
        subprocess.Popen(["explorer.exe", "/select,", str(path)])
    except Exception:
        # fall back to opening folder
        subprocess.Popen(["explorer.exe", str(path.parent)])

def _mac_reveal(path: Path):
    # open -R path
    subprocess.Popen(["open", "-R", str(path)])

def _linux_open_folder(path: Path):
    # Not all DEs support highlighting; open the parent folder
    subprocess.Popen(["xdg-open", str(path.parent)])

def preview_paths(paths: Iterable[Path]) -> Tuple[int, int]:
    """
    Open OS file browser to reveal the selected files.
    Returns (opened_count, skipped_count).
    Caps the number of windows to PREVIEW_MAX_WINDOWS.
    """
    paths = [Path(p).resolve() for p in paths]
    opened = 0
    skipped = 0

    # Group by parent to avoid too many windows (still 1 per file for Windows highlight)
    by_parent = defaultdict(list)
    for p in paths:
        by_parent[p.parent].append(p)

    # Strategy:
    # - Windows: open /select, for up to PREVIEW_MAX_WINDOWS files
    # - macOS: open -R file for up to PREVIEW_MAX_WINDOWS files
    # - Linux: open parent folder (one per parent) until cap
    if sys.platform.startswith("win"):
        for p in paths:
            if opened >= PREVIEW_MAX_WINDOWS:
                skipped = len(paths) - opened
                break
            _win_select(p)
            opened += 1
    elif sys.platform == "darwin":
        for p in paths:
            if opened >= PREVIEW_MAX_WINDOWS:
                skipped = len(paths) - opened
                break
            _mac_reveal(p)
            opened += 1
    else:
        # linux: one window per parent
        for parent, group in by_parent.items():
            if opened >= PREVIEW_MAX_WINDOWS:
                # skipped = total parents remaining (approximate using group count)
                skipped = sum(len(g) for g in by_parent.values()) - opened
                break
            _linux_open_folder(group[0])
            opened += 1

    return opened, skipped

import re
from .schemas import Plan, PlanStep

# Small helpers to parse human phrases
_SIZE_UNITS = {
    "kb": 1_000,
    "kib": 1_024,
    "mb": 1_000_000,
    "mib": 1_048_576,
    "gb": 1_000_000_000,
    "gib": 1_073_741_824,
}

_FILETYPE_TO_PATTERNS = {
    "exe": ["*.exe"],
    "zip": ["*.zip"],
    "msi": ["*.msi"],
    "pdf": ["*.pdf"],
    "doc": ["*.doc", "*.docx"],
    "ppt": ["*.ppt", "*.pptx"],
    "xls": ["*.xls", "*.xlsx"],
}

def _parse_size_kb(text: str):
    """
    Parse 'greater than 500 MB', 'over 1gb', 'less than 200kb' into (min_kb, max_kb).
    Returns (min_kb, max_kb) or (None, None) if no size found.
    """
    t = text.lower()
    # greater than / over / at least
    gt = re.search(r"(greater than|over|at least|>=?)\s+(\d+(?:\.\d+)?)\s*(kib|kb|mib|mb|gib|gb)\b", t)
    lt = re.search(r"(less than|under|at most|<=?)\s+(\d+(?:\.\d+)?)\s*(kib|kb|mib|mb|gib|gb)\b", t)

    min_kb = max_kb = None
    if gt:
        val = float(gt.group(2))
        unit = gt.group(3)
        bytes_val = val * _SIZE_UNITS[unit]
        min_kb = int(bytes_val / 1024)

    if lt:
        val = float(lt.group(2))
        unit = lt.group(3)
        bytes_val = val * _SIZE_UNITS[unit]
        max_kb = int(bytes_val / 1024)

    return min_kb, max_kb


def _parse_age_days(text: str):
    """
    Understand 'today', 'yesterday', 'last week', 'older than 30 days', 'within 7 days'
    Returns (newer_than_days, older_than_days) where:
      - newer_than_days = modified within N days (i.e., more recent than N-day cutoff)
      - older_than_days = modified before N days ago
    """
    t = text.lower()

    # Explicit older/within
    m_older = re.search(r"older than\s+(\d+)\s+(day|days|week|weeks|month|months|year|years)", t)
    m_within = re.search(r"(within|in the last|in last|last)\s+(\d+)\s+(day|days|week|weeks|month|months|year|years)", t)

    def to_days(num: int, unit: str):
        if unit.startswith("day"):
            return num
        if unit.startswith("week"):
            return num * 7
        if unit.startswith("month"):
            return num * 30
        if unit.startswith("year"):
            return num * 365
        return num

    newer_than_days = None
    older_than_days = None

    if "today" in t:
        newer_than_days = 1
    elif "yesterday" in t:
        newer_than_days = 2  # include yesterday back to now-2d

    if "last week" in t and newer_than_days is None:
        newer_than_days = 7

    if m_within:
        newer_than_days = to_days(int(m_within.group(2)), m_within.group(3))

    if m_older:
        older_than_days = to_days(int(m_older.group(1)), m_older.group(2))

    return newer_than_days, older_than_days


def _infer_patterns(text: str):
    t = text.lower()
    pats = []
    # look for explicit extensions first like ".zip", ".msi"
    ext_hits = re.findall(r"\.(exe|zip|msi|pdf|docx?|pptx?|xlsx?)\b", t)
    for ext in ext_hits:
        pats.append(f"*.{ext}")

    # also check type keywords
    for k, v in _FILETYPE_TO_PATTERNS.items():
        if re.search(rf"\b{k}\b", t):
            pats.extend(v)

    # default if nothing found
    if not pats:
        pats = ["*"]

    # de-dupe, keep order
    seen = set()
    out = []
    for p in pats:
        if p not in seen:
            out.append(p); seen.add(p)
    return out


def plan_from_prompt(prompt: str) -> Plan:
    """
    Smarter heuristic planner:
      - understands file types (zip/msi/pdf/exe)
      - understands ages (today, yesterday, older than N days, within N days)
      - understands sizes (greater than/less than N KB/MB/GB)
    """
    p = prompt.lower()
    steps = []
    rationale = "Heuristic plan with type/age/size parsing; swap with LLM later."

    # intent: delete / remove / trash
    if any(word in p for word in ("delete", "remove", "trash", "clean up", "cleanup", "clean")):
        patterns = _infer_patterns(p)
        newer_days, older_days = _parse_age_days(p)
        min_kb, max_kb = _parse_size_kb(p)

        # if no explicit age hints and it mentions "today"/"yesterday", handled above; else default to last 14 days
        if newer_days is None and older_days is None and "older than" not in p and "within" not in p and "last week" not in p and "today" not in p and "yesterday" not in p:
            newer_days = 14

        steps.append(PlanStep(
            "search_files",
            f"Search {', '.join(patterns)} with filters",
            {
                "patterns": patterns,
                # legacy 'days' not used when smarter filters exist
                "days": None,
                "name_hint": None,
                "newer_than_days": newer_days,
                "older_than_days": older_days,
                "min_size_kb": min_kb,
                "max_size_kb": max_kb,
            }
        ))
        steps.append(PlanStep("select_targets", "Ask user to choose which file(s) to delete", {}))
        steps.append(PlanStep("move_to_trash", "Move selected file(s) to the Recycle Bin", {}))
    else:
        steps.append(PlanStep("noop", "No recognized action. Try: delete zip files older than 30 days", {}))

    return Plan(steps=steps, rationale=rationale)

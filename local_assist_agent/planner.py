import re
from .schemas import Plan, PlanStep

# ----- helpers -----
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

    Conventions:
      - KB / MB / GB  use decimal: 1 MB = 1000 KB
      - KiB / MiB / GiB use binary: 1 MiB = 1024 KiB
    """
    t = text.lower()

    def to_kb(val: float, unit: str) -> int:
        if unit == "kb":
            return int(round(val))
        if unit == "mb":
            return int(round(val * 1000))
        if unit == "gb":
            return int(round(val * 1_000_000))
        if unit == "kib":
            # 1 KiB = 1024 bytes ≈ 1.024 KB
            return int(round(val * 1024 / 1000))
        if unit == "mib":
            # 1 MiB = 1024 KiB ≈ 1024 * 1024 bytes ≈ 1_048_576 bytes ≈ 1024 KB
            return int(round(val * 1024))
        if unit == "gib":
            # 1 GiB ≈ 1024 MiB ≈ 1024 * 1024 KB
            return int(round(val * 1024 * 1024))
        return int(round(val))

    gt = re.search(r"(greater than|over|at least|>=?)\s+(\d+(?:\.\d+)?)\s*(kib|kb|mib|mb|gib|gb)\b", t)
    lt = re.search(r"(less than|under|at most|<=?)\s+(\d+(?:\.\d+)?)\s*(kib|kb|mib|mb|gib|gb)\b", t)

    min_kb = max_kb = None
    if gt:
        val = float(gt.group(2)); unit = gt.group(3)
        min_kb = to_kb(val, unit)
    if lt:
        val = float(lt.group(2)); unit = lt.group(3)
        max_kb = to_kb(val, unit)

    return min_kb, max_kb


def _parse_age_days(text: str):
    """
    Understand:
      - today, yesterday, last week
      - older than 30 days
      - within 7 days / in the last 7 days
    -> returns (newer_than_days, older_than_days)
    """
    t = text.lower()
    m_older  = re.search(r"older than\s+(\d+)\s+(day|days|week|weeks|month|months|year|years)", t)
    m_within = re.search(r"(within|in the last|in last|last)\s+(\d+)\s+(day|days|week|weeks|month|months|year|years)", t)

    def to_days(num: int, unit: str):
        if unit.startswith("day"): return num
        if unit.startswith("week"): return num * 7
        if unit.startswith("month"): return num * 30
        if unit.startswith("year"): return num * 365
        return num

    newer_than_days = None
    older_than_days = None

    if "today" in t: newer_than_days = 1
    elif "yesterday" in t: newer_than_days = 2
    if "last week" in t and newer_than_days is None: newer_than_days = 7
    if m_within: newer_than_days = to_days(int(m_within.group(2)), m_within.group(3))
    if m_older:  older_than_days = to_days(int(m_older.group(1)), m_older.group(2))

    return newer_than_days, older_than_days

def _infer_patterns(text: str):
    t = text.lower()
    pats = []
    # explicit extensions like ".zip"
    for ext in re.findall(r"\.(exe|zip|msi|pdf|docx?|pptx?|xlsx?)\b", t):
        pats.append(f"*.{ext}")
    # type keywords
    for k, v in _FILETYPE_TO_PATTERNS.items():
        if re.search(rf"\b{k}\b", t):
            pats.extend(v)
    if not pats:
        pats = ["*"]
    # de-dupe
    seen = set(); out = []
    for p in pats:
        if p not in seen:
            out.append(p); seen.add(p)
    return out

def _parse_name_hint(text: str):
    """
    Extract a filename substring hint from:
      - quoted phrases: "report", 'invoice'
      - phrases: containing X / named X / with name X
    Returns a lowercase string or None.
    """
    t = text.strip()
    q = re.search(r"[\"']([^\"']+)[\"']", t)
    if q:
        return q.group(1).strip().lower()

    m = re.search(r"\b(containing|named|with name|with)\s+([A-Za-z0-9_\-\.\s]+)", t, re.IGNORECASE)
    if m:
        raw = m.group(2)
        # stop at common keywords
        raw = re.split(r"\b(older|within|last|greater|less|over|under|today|yesterday)\b", raw, maxsplit=1, flags=re.IGNORECASE)[0]
        hint = raw.strip().strip(",.;").lower()
        return hint if hint else None
    return None

# ----- planner -----
def plan_from_prompt(prompt: str) -> Plan:
    """
    Heuristic planner with type/age/size + name parsing.
    """
    p = prompt.lower()
    steps = []
    rationale = "Heuristic plan with type/age/size/name parsing; swap with LLM later."

    if any(w in p for w in ("delete", "remove", "trash", "clean up", "cleanup", "clean")):
        patterns = _infer_patterns(p)
        newer_days, older_days = _parse_age_days(p)
        min_kb, max_kb = _parse_size_kb(p)
        name_hint = _parse_name_hint(prompt)

        # default look-back if no age hinted
        if all(x is None for x in (newer_days, older_days)) and not any(s in p for s in ("older than", "within", "last week", "today", "yesterday")):
            newer_days = 14

        steps.append(PlanStep(
            "search_files",
            f"Search {', '.join(patterns)} with filters",
            {
                "patterns": patterns,
                "days": None,
                "name_hint": name_hint,
                "newer_than_days": newer_days,
                "older_than_days": older_days,
                "min_size_kb": min_kb,
                "max_size_kb": max_kb,
            }
        ))
        steps.append(PlanStep("select_targets", "Ask user to choose which file(s) to delete", {}))
        steps.append(PlanStep("move_to_trash", "Move selected file(s) to the Recycle Bin", {}))
    else:
        steps.append(PlanStep("noop", "Try: delete zip files older than 30 days containing \"report\"", {}))

    return Plan(steps=steps, rationale=rationale)

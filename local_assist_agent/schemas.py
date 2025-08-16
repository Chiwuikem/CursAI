from dataclasses import dataclass, field
from pathlib import Path
from typing import List
@dataclass
class FileHit:
    path: Path; mtime: float; size: int
@dataclass
class PlanStep:
    action: str; description: str; params: dict = field(default_factory=dict)
@dataclass
class Plan:
    steps: List[PlanStep] = field(default_factory=list); rationale: str = ""


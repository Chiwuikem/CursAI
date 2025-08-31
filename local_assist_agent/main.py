from typing import List

from .config import DEFAULT_SCOPES
from .planner import plan_from_prompt
from .executor import execute as exec_plan  # avoid name collision
from .logging_utils import log_line, log_event, new_run_id

def run(prompt: str, execute: bool = False, scopes: List[str] = None, preview: bool = False):
    scopes = scopes or DEFAULT_SCOPES
    run_id = new_run_id()
    log_event(run_id, "input.prompt", {"prompt": prompt})
    log_line(f"Prompt: {prompt}", run_id=run_id)
    plan = plan_from_prompt(prompt)
    return exec_plan(plan, execute, scopes, run_id=run_id, preview=preview)

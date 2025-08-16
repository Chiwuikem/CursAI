from .schemas import Plan, PlanStep

def plan_from_prompt(prompt: str) -> Plan:
    """
    Heuristic planner: map simple English to a sequence of safe actions.
    Swap with an LLM later; keep the executor unchanged.
    """
    p = prompt.lower()
    steps = []
    rationale = "Heuristic plan from keywords; swap with LLM later."

    if "delete" in p and ".exe" in p:
        days = 2 if ("today" in p or "yesterday" in p) else 14
        steps.append(PlanStep("search_files", f"Search recent .exe in last {days} day(s)",
                              {"patterns": ["*.exe"], "days": days, "name_hint": None}))
        steps.append(PlanStep("select_targets", "Ask user to choose which file(s) to delete", {}))
        steps.append(PlanStep("move_to_trash", "Move selected file(s) to the Recycle Bin", {}))
    elif "delete" in p:
        steps.append(PlanStep("search_files", "Search recent files",
                              {"patterns": ["*"], "days": 14, "name_hint": None}))
        steps.append(PlanStep("select_targets", "Ask user to choose which file(s) to delete", {}))
        steps.append(PlanStep("move_to_trash", "Move selected file(s) to the Recycle Bin", {}))
    else:
        steps.append(PlanStep("noop", "No recognized action. Try: delete the exe I downloaded yesterday", {}))

    return Plan(steps=steps, rationale=rationale)

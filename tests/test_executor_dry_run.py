import builtins, json
from local_assist_agent.schemas import Plan, PlanStep
from local_assist_agent import executor as ex

def test_executor_dry_run_selection(tmp_path, monkeypatch, temp_logs):
    # One candidate file
    f = tmp_path / "pickme.zip"
    f.write_text("x")

    # Plan: search -> select -> move (but dry-run so no actual delete)
    plan = Plan(
        steps=[
            PlanStep("search_files", "search", {
                "patterns": ["*.zip"],
                "days": None,
                "name_hint": None,
                "newer_than_days": 7,
                "older_than_days": None,
                "min_size_kb": None,
                "max_size_kb": None,
            }),
            PlanStep("select_targets", "pick", {}),
            PlanStep("move_to_trash", "trash", {}),
        ],
        rationale="test"
    )

    # Auto-answer prompts:
    # 1) selection -> "1"
    # 2) risky-path confirm (temp path lives under AppData) -> "I UNDERSTAND"
    answers = iter(["1", "I UNDERSTAND"])
    monkeypatch.setattr(builtins, "input", lambda: next(answers))

    # Stub move_to_trash (shouldn't be called in dry-run, but safe anyway)
    monkeypatch.setattr(ex, "move_to_trash", lambda paths: (len(list(paths)), [], []), raising=True)

    # Run executor (dry-run)
    ex.execute(plan, do_execute=False, scopes=[str(tmp_path)], run_id="testrun")

    # Check events were recorded in JSONL
    log_file, jsonl = temp_logs
    lines = [ln for ln in jsonl.read_text(encoding="utf-8").splitlines() if ln.strip()]
    records = [json.loads(ln) for ln in lines]

    events = {r.get("event") for r in records}
    # Prefer plan.built; accept search.results + execute.dry_run as proof of the flow
    assert ("plan.built" in events) or ({"search.results", "execute.dry_run"} <= events)

from local_assist_agent.planner import plan_from_prompt

def _search_params(plan):
    for s in plan.steps:
        if s.action == "search_files":
            return s.params
    raise AssertionError("No search_files step found")

def test_planner_types_age_size_name():
    plan = plan_from_prompt('delete zip files older than 30 days containing "report" greater than 1 mb')
    params = _search_params(plan)
    assert "*.zip" in params["patterns"]
    assert params["older_than_days"] >= 30
    assert params["min_size_kb"] >= 1000
    assert params["name_hint"] == "report"

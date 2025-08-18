from pathlib import Path
from local_assist_agent.policies import in_allowed_scopes, requires_extra_confirmation

def test_in_allowed_scopes(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    f = root / "a.txt"
    f.write_text("x")
    assert in_allowed_scopes(f, scopes=[str(root)]) is True

    out = tmp_path / "outside.txt"
    out.write_text("y")
    assert in_allowed_scopes(out, scopes=[str(root)]) is False

def test_requires_extra_confirmation():
    assert requires_extra_confirmation(Path(r"C:\Windows\System32\drivers\etc\hosts")) is True
    assert requires_extra_confirmation(Path(r"C:\Users\me\Downloads\file.txt")) is False

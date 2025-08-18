import os, time
from local_assist_agent.skills.files import find_recent

def test_find_recent_filters(tmp_path):
    root = tmp_path
    a = root / "a.zip"; a.write_bytes(b"x")
    b = root / "b.zip"; b.write_bytes(b"x" * 2048)  # ~2KB
    old = root / "old.zip"; old.write_bytes(b"x")

    # Make "old.zip" older than 30 days
    t_old = time.time() - 31 * 86400
    os.utime(old, (t_old, t_old))

    # Newer-than window should include a, b but not old
    hits = find_recent([str(root)], patterns=["*.zip"], newer_than_days=7)
    names = [h.path.name for h in hits]
    assert "a.zip" in names and "b.zip" in names and "old.zip" not in names

    # Size filter: only b (>=2KB)
    hits2 = find_recent([str(root)], patterns=["*.zip"], min_size_kb=2)
    names2 = [h.path.name for h in hits2]
    assert "b.zip" in names2 and "a.zip" not in names2

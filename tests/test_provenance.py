import json
import subprocess

from openlux.provenance import code_version, write_json


def test_write_json_is_deterministic_and_sorted(tmp_path):
    rec = {"b": 1, "a": {"z": [1, 2], "y": "x"}}
    p1, p2 = tmp_path / "1.json", tmp_path / "2.json"
    write_json(p1, rec)
    write_json(p2, dict(reversed(list(rec.items()))))
    assert p1.read_bytes() == p2.read_bytes()
    assert json.loads(p1.read_text()) == rec


def test_code_version_reports_commit_and_dirty_flag(tmp_path):
    def git(*a):
        subprocess.run(["git", "-C", str(tmp_path), *a], check=True, capture_output=True)
    git("init", "-q")
    git("config", "user.email", "t@example.org")
    git("config", "user.name", "t")
    (tmp_path / "a.txt").write_text("1")
    git("add", "a.txt")
    git("commit", "-qm", "x")
    v = code_version(tmp_path)
    assert len(v["commit"]) == 40 and v["dirty"] is False
    (tmp_path / "a.txt").write_text("2")
    assert code_version(tmp_path)["dirty"] is True


def test_code_version_outside_git_is_unknown(tmp_path):
    v = code_version(tmp_path / "nao_existe")
    assert v == {"commit": None, "dirty": None}

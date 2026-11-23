"""Log estruturado: uma linha JSON valida por evento."""
import io
import json

from openlux.log import JsonLogger


def test_each_event_is_one_json_line_with_fields_and_levels(tmp_path):
    buf, path = io.StringIO(), tmp_path / "sub" / "run.jsonl"
    lg = JsonLogger(path, stream=buf)
    lg.log("start", n=3, name="ação")
    lg.warn("careful", reason="x")
    lines = path.read_text(encoding="utf-8").splitlines()
    assert lines == buf.getvalue().splitlines() and len(lines) == 2
    a, b = (json.loads(x) for x in lines)
    assert a["event"] == "start" and a["level"] == "INFO" and a["n"] == 3 and a["name"] == "ação"
    assert b["level"] == "WARNING" and b["reason"] == "x" and a["ts"].endswith("+00:00")


def test_non_serializable_values_do_not_crash_and_file_is_reset(tmp_path):
    path = tmp_path / "r.jsonl"
    path.write_text("lixo antigo\n")
    lg = JsonLogger(path, stream=io.StringIO())
    lg.log("p", where=tmp_path)
    assert len(path.read_text().splitlines()) == 1 and json.loads(path.read_text())["event"] == "p"

"""tester_cli 的协议测试：成员2 的 tools.test() 只认这几个字段和退出码。"""
import csv
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "gen"))

import make_example_package          # noqa: E402
import tester_cli                    # noqa: E402


def _task_card(tmp_path, task="P03"):
    fx = json.loads((HERE / "cases" / "_fixtures" / ("%s.io.json" % task))
                    .read_text(encoding="utf-8"))
    io_table = [{"name": r["name"], "direction": r["direction"],
                 "data_type": r["type"]} for r in fx["io"]]
    p = tmp_path / ("%s.task_card.json" % task)
    p.write_text(json.dumps({"task_id": task, "io_table": io_table},
                            ensure_ascii=False), encoding="utf-8")
    return p


def _run(tmp_path, source, task_card, extra=()):
    result = tmp_path / "out" / "result.json"
    rc = tester_cli.main([
        "--source", str(source),
        "--task-card", str(task_card),
        "--cases-dir", str(HERE / "cases"),
        "--result", str(result),
        *extra,
    ])
    return rc, json.loads(result.read_text(encoding="utf-8"))


def _example_run(tmp_path):
    run = make_example_package.build(tmp_path / "pkg")
    return run / "source" / "final.st", run


def test_pass_contract(tmp_path):
    card = _task_card(tmp_path)
    source, _ = _example_run(tmp_path)
    rc, payload = _run(tmp_path, source, card)
    assert rc == 0
    assert payload["status"] == "pass"
    assert payload["total"] == 6 and payload["passed"] == 6
    assert len(payload["passed_ids"]) == 6 and len(set(payload["passed_ids"])) == 6
    assert payload["failures"] == []


def test_fail_reports_cycle_and_signal(tmp_path):
    card = _task_card(tmp_path)
    source, run = _example_run(tmp_path)
    f = run / "test" / "actual" / "P03-01.csv"
    rows = list(csv.reader(f.open(encoding="utf-8")))
    # 第 2 行（cycle=1）把 hiAlarm 翻掉
    idx = rows[0].index("hiAlarm")
    rows[1][idx] = "FALSE" if rows[1][idx] == "TRUE" else "TRUE"
    with f.open("w", encoding="utf-8", newline="") as fh:
        csv.writer(fh).writerows(rows)

    rc, payload = _run(tmp_path, source, card)
    assert rc == 1
    assert payload["status"] == "fail"
    assert payload["passed"] == 5 and payload["total"] == 6
    fail = payload["failures"][0]
    assert set(fail) >= {"case_id", "cycle", "signal", "expected", "actual"}
    assert fail["case_id"] == "P03-01" and fail["signal"] == "hiAlarm"


def test_missing_cases_is_skipped(tmp_path):
    card = _task_card(tmp_path)
    source, _ = _example_run(tmp_path)
    empty = tmp_path / "empty_cases"
    empty.mkdir()
    result = tmp_path / "r.json"
    rc = tester_cli.main([
        "--source", str(source), "--task-card", str(card),
        "--cases-dir", str(empty), "--result", str(result),
    ])
    payload = json.loads(result.read_text(encoding="utf-8"))
    assert rc == 0 and payload["status"] == "skipped"


def test_no_actual_and_no_runner_is_skipped(tmp_path):
    card = _task_card(tmp_path)
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    source = src_dir / "final.st"
    source.write_text("PROGRAM P END_PROGRAM\n", encoding="utf-8")
    result = tmp_path / "r.json"
    rc = tester_cli.main([
        "--source", str(source), "--task-card", str(card),
        "--cases-dir", str(HERE / "cases"), "--result", str(result),
    ])
    payload = json.loads(result.read_text(encoding="utf-8"))
    assert rc == 0 and payload["status"] == "skipped"
    assert "actual" in payload["reason"]


def test_corrupt_actual_is_tool_error(tmp_path):
    card = _task_card(tmp_path)
    source, run = _example_run(tmp_path)
    f = run / "test" / "actual" / "P03-01.csv"
    rows = list(csv.reader(f.open(encoding="utf-8")))
    rows = [r[:-1] for r in rows]          # 删掉最后一列
    with f.open("w", encoding="utf-8", newline="") as fh:
        csv.writer(fh).writerows(rows)

    rc, payload = _run(tmp_path, source, card)
    assert rc == 2 and payload["status"] == "tool_error"

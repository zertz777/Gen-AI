"""run_batch.py 的端到端测试：passed / missing / timeout 三种结局。"""
import csv
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import run_batch                                    # noqa: E402
from test_contract import write_actual              # noqa: E402

CASES = HERE / "cases"


def _make_run(root, setting, task, repeat=1, seed=42):
    d = Path(root) / setting / ("%s_r%d_s%d" % (task, repeat, seed))
    (d / "source").mkdir(parents=True)
    (d / "source" / "final.st").write_text("PROGRAM P END_PROGRAM\n", encoding="utf-8")
    (d / "test").mkdir()
    return d


def _summary(out):
    with open(Path(out) / "summary.csv", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def test_batch_passed(tmp_path):
    run = _make_run(tmp_path / "runs", "E3", "P03")
    write_actual(CASES / "P03.csv", CASES / "_fixtures" / "P03.io.json", run / "test" / "actual")
    rc = run_batch.main(["--runs", str(tmp_path / "runs"), "--out", str(tmp_path / "out"),
                         "--framework", "self", "--model", "m"])
    assert rc == 0
    rows = _summary(tmp_path / "out")
    assert len(rows) == 1
    r = rows[0]
    assert r["run_id"] == "E3_P03_r1_s42"
    assert r["final_status"] == "passed"
    assert r["test_total"] == "6" and r["test_passed"] == "6"
    assert r["framework"] == "self" and r["verify_status"] == "skipped"
    # 每个 run 自己也要留一份逐条结果
    assert (run / "test" / "cases_result.jsonl").exists()


def test_batch_missing_actual_is_not_failure(tmp_path):
    _make_run(tmp_path / "runs", "E1", "P03")
    run_batch.main(["--runs", str(tmp_path / "runs"), "--out", str(tmp_path / "out")])
    r = _summary(tmp_path / "out")[0]
    assert r["final_status"] == "missing"
    assert r["test_missing"] == "6" and r["test_failed"] == "0"


def test_batch_status_timeout(tmp_path):
    run = _make_run(tmp_path / "runs", "E4", "P03")
    (run / "test" / "status.json").write_text(
        json.dumps({"status": "timeout", "reason": "compile 90s"}), encoding="utf-8")
    run_batch.main(["--runs", str(tmp_path / "runs"), "--out", str(tmp_path / "out")])
    r = _summary(tmp_path / "out")[0]
    assert r["final_status"] == "abandoned"
    assert r["test_timeout"] == "6" and r["note"] == "compile 90s"


def test_batch_ignores_unrelated_dirs(tmp_path):
    _make_run(tmp_path / "runs", "E2", "P03")
    (tmp_path / "runs" / "E2" / "scratch").mkdir()
    run_batch.main(["--runs", str(tmp_path / "runs"), "--out", str(tmp_path / "out")])
    assert len(_summary(tmp_path / "out")) == 1


def test_batch_partial_failure_is_best_effort(tmp_path):
    run = _make_run(tmp_path / "runs", "E3", "P03")
    # 只给前 3 条用例的 actual，后 3 条缺失 → 那 3 条判 error，整体 best-effort
    write_actual(CASES / "P03.csv", CASES / "_fixtures" / "P03.io.json",
                 run / "test" / "actual", case_filter=lambda c: c.case_id <= "P03-03")
    run_batch.main(["--runs", str(tmp_path / "runs"), "--out", str(tmp_path / "out")])
    r = _summary(tmp_path / "out")[0]
    assert r["final_status"] == "best-effort"
    assert r["test_passed"] == "3" and r["test_error"] == "3"

"""批量汇总的干跑测试：没有真 actual 时也能验证 run_batch 的口径。

用 `gen/make_fake_runs.py` 造一套假实验目录（pass / wrong / missing / timeout /
partial / corrupt 六种结局），再跑 run_batch，逐 run 与 manifest 对账。
"""
import csv
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "gen"))

import run_batch                                  # noqa: E402
from make_fake_runs import build                  # noqa: E402

TASKS = ["P01", "P03", "P04", "P12", "S01", "S07"]


def _summary(out):
    with (Path(out) / "summary.csv").open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def test_dryrun_shape_matches_manifest(tmp_path):
    manifest = build(tmp_path / "runs", ["E1", "E2", "E3", "E4"], TASKS,
                     force={("E1", "P01"): "timeout", ("E1", "P03"): "corrupt",
                            ("E2", "P01"): "missing", ("E2", "P03"): "wrong"})
    rc = run_batch.main(["--runs", str(tmp_path / "runs"), "--out", str(tmp_path / "out")])
    assert rc == 0

    rows = _summary(tmp_path / "out")
    assert len(rows) == len(manifest) == 24

    bad = [r["run_id"] for r in rows
           if r["final_status"] != manifest[r["run_id"]]["final"]
           or int(r["test_passed"] or 0) != manifest[r["run_id"]]["passed"]]
    assert not bad, bad

    # 三种非 pass 结局都要真的出现，否则这套测试没覆盖到分支
    finals = {r["final_status"] for r in rows}
    assert {"passed", "best-effort", "missing", "abandoned"} <= finals, finals


def test_dryrun_missing_rate_and_denominator(tmp_path):
    manifest = build(tmp_path / "runs", ["E1", "E2"], ["P01", "P03", "S07"])
    run_batch.main(["--runs", str(tmp_path / "runs"), "--out", str(tmp_path / "out")])
    rows = _summary(tmp_path / "out")

    n_missing = sum(1 for r in rows if r["final_status"] == "missing")
    assert n_missing == sum(1 for v in manifest.values() if v["final"] == "missing")
    # 缺失的 run 不能把 test_missing 记成 test_failed
    for r in rows:
        if r["final_status"] == "missing":
            assert r["test_failed"] == "0"


def test_dryrun_corrupt_actual_is_error_not_fail(tmp_path):
    manifest = build(tmp_path / "runs", ["E3"], ["P03", "S07"],
                     force={("E3", "P03"): "corrupt"})
    run_batch.main(["--runs", str(tmp_path / "runs"), "--out", str(tmp_path / "out")])
    rows = {r["run_id"]: r for r in _summary(tmp_path / "out")}
    r = rows["E3_P03_r1_s42"]
    assert manifest["E3_P03_r1_s42"]["outcome"] == "corrupt"
    assert r["final_status"] == "abandoned"
    assert int(r["test_error"]) > 0 and r["test_failed"] == "0"


def test_dryrun_timeout_keeps_its_own_state(tmp_path):
    build(tmp_path / "runs", ["E4"], ["P01"], force={("E4", "P01"): "timeout"})
    run_batch.main(["--runs", str(tmp_path / "runs"), "--out", str(tmp_path / "out")])
    r = _summary(tmp_path / "out")[0]
    assert r["final_status"] == "abandoned"
    assert int(r["test_timeout"]) > 0 and r["test_failed"] == "0"

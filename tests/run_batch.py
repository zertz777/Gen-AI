"""批量对拍：把一个实验目录下的所有 run 跑成一张表。

    python tests/run_batch.py --runs experiments/runs --out tests/results/batch
    python tests/run_batch.py --runs experiments/runs/E3 --out tests/results/E3 \
        --framework self --model deepseek-v4.1-flash

目录约定（与任务书表 7-2 一致）：

    experiments/runs/
    └── E3/
        └── P07_r1_s42/                  # 组别/题号_第几次_种子
            ├── source/final.st
            └── test/
                ├── actual/<case_id>.csv # 成员2 产出，逐拍实际输出
                └── status.json          # 可选，整题超时/跑崩时写

产物：

    <run>/test/cases_result.jsonl        # 每个 run 的逐条判定
    <out>/runs.jsonl                     # 汇总（逐条，带 run 元数据）
    <out>/summary.csv                    # 逐 run 汇总，字段对齐成员3 的 summary

缺失 actual 的 run 记为 missing，**不计入失败率**——分母里既不放它，也不拿它凑数。
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from runner.actual_io import ActualError, ActualStore, read_status   # noqa: E402
from runner.backends import BackendError, ReplayBackend              # noqa: E402
from runner.case_loader import CaseError, load_cases, load_io        # noqa: E402
from runner.verdict import PASS, judge                               # noqa: E402

RUN_RE = re.compile(r"^(P\d{2}|S\d{2})_r(\d+)_s(\d+)$")
PLAIN_RE = re.compile(r"^(P\d{2}|S\d{2})$")

SUMMARY_FIELDS = [
    "run_id", "setting_id", "framework", "model", "task_id", "repeat_idx", "seed",
    "test_total", "test_passed", "test_failed", "test_timeout", "test_error",
    "test_missing", "latency_s", "verify_status", "final_status", "note",
]


def discover(runs_dir, setting=None, default_seed=42):
    """返回 [(setting_id, task_id, repeat, seed, run_dir)]。"""
    runs_dir = Path(runs_dir)
    if not runs_dir.exists():
        raise SystemExit("找不到实验目录：%s" % runs_dir)

    def parse(d, parent):
        m = RUN_RE.match(d.name)
        if m:
            return (setting or parent, m.group(1), int(m.group(2)), int(m.group(3)), d)
        m = PLAIN_RE.match(d.name)
        if m:
            return (setting or parent, m.group(1), 1, default_seed, d)
        return None

    found = []
    if RUN_RE.match(runs_dir.name) or PLAIN_RE.match(runs_dir.name):
        item = parse(runs_dir, runs_dir.parent.name)
        if item:
            found.append(item)
        return found

    for setting_dir in sorted(p for p in runs_dir.iterdir() if p.is_dir()):
        for d in sorted(p for p in setting_dir.iterdir() if p.is_dir()):
            item = parse(d, setting_dir.name)
            if item:
                found.append(item)
    return found


def run_one(setting, task, repeat, seed, run_dir, cases_dir, timeout_s):
    """跑一个 run，返回 (summary_row, case_rows)。"""
    run_id = "%s_%s_r%d_s%d" % (setting, task, repeat, seed)
    cases_csv = Path(cases_dir) / ("%s.csv" % task)
    io_json = Path(cases_dir) / "_fixtures" / ("%s.io.json" % task)
    row = {k: "" for k in SUMMARY_FIELDS}
    row.update(run_id=run_id, setting_id=setting, task_id=task,
               repeat_idx=repeat, seed=seed, verify_status="skipped",
               test_total=0, test_passed=0, test_failed=0,
               test_timeout=0, test_error=0, test_missing=0)

    if not cases_csv.exists() or not io_json.exists():
        row.update(final_status="missing", note="没有用例或 fixture")
        return row, []

    _, ins, outs = load_io(io_json)
    _, cases = load_cases(cases_csv, io_json)

    actual_dir = Path(run_dir) / "test" / "actual"
    try:
        status = read_status(run_dir)
    except ActualError as e:
        status = {"status": "error", "reason": str(e)}

    if status and status["status"] == "timeout":
        case_rows = [{"run_id": run_id, "task_id": task, "case_id": c.case_id,
                      "status": "timeout", "mismatch": None,
                      "reason": status.get("reason") or "status.json: timeout",
                      "latency_s": None} for c in cases]
        row.update(test_total=len(cases), test_timeout=len(cases),
                   final_status="abandoned", note=status.get("reason") or "timeout")
        _write_run_result(run_dir, case_rows)
        return row, case_rows

    if not actual_dir.exists():
        case_rows = [{"run_id": run_id, "task_id": task, "case_id": c.case_id,
                      "status": "missing", "mismatch": None,
                      "reason": "没有 %s" % actual_dir, "latency_s": None}
                     for c in cases]
        row.update(test_total=len(cases), test_missing=len(cases),
                   final_status="missing", note="actual 目录缺失")
        _write_run_result(run_dir, case_rows)
        return row, case_rows

    backend = ReplayBackend(ActualStore(actual_dir), outs, status)
    case_rows = []
    lat = []
    for case in cases:
        r = judge(case, backend, "", timeout_s)
        if r.get("latency_s") is not None:
            lat.append(r["latency_s"])
        case_rows.append({"run_id": run_id, "task_id": task, **r})

    counts = {k: sum(1 for r in case_rows if r["status"] == k)
              for k in ("pass", "fail", "timeout", "error")}
    total = len(case_rows)
    if counts["pass"] == total and total:
        final = "passed"
    elif counts["pass"] > 0:
        final = "best-effort"
    else:
        final = "abandoned"
    row.update(test_total=total, test_passed=counts["pass"], test_failed=counts["fail"],
               test_timeout=counts["timeout"], test_error=counts["error"],
               latency_s=round(sum(lat) / len(lat), 3) if lat else "",
               final_status=final,
               note="" if counts["error"] == 0 else "有工具故障，见 cases_result.jsonl")
    _write_run_result(run_dir, case_rows)
    return row, case_rows


def _write_run_result(run_dir, case_rows):
    p = Path(run_dir) / "test"
    p.mkdir(parents=True, exist_ok=True)
    with (p / "cases_result.jsonl").open("w", encoding="utf-8") as f:
        for r in case_rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", required=True, help="实验根目录或单个 run 目录")
    ap.add_argument("--cases-dir", default=str(Path(__file__).resolve().parent / "cases"))
    ap.add_argument("--out", required=True, help="汇总输出目录")
    ap.add_argument("--setting", help="runs 指向单组时显式指定 E1—E4")
    ap.add_argument("--framework", default="", help="self / baseline（写进 summary）")
    ap.add_argument("--model", default="", help="模型名（写进 summary）")
    ap.add_argument("--seed", type=int, default=42, help="目录名不带 _s<seed> 时用")
    ap.add_argument("--timeout", type=float, default=900.0)
    a = ap.parse_args(argv)

    found = discover(a.runs, a.setting, a.seed)
    if not found:
        print("没有发现 run 目录（期望 <setting>/<P07|S03>_r1_s42/）", file=sys.stderr)
        return 2

    out_dir = Path(a.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    rows, all_cases = [], []
    for setting, task, repeat, seed, run_dir in found:
        try:
            row, cases = run_one(setting, task, repeat, seed, run_dir,
                                 a.cases_dir, a.timeout)
        except (CaseError, ActualError, BackendError) as e:
            row = {k: "" for k in SUMMARY_FIELDS}
            row.update(run_id="%s_%s_r%d_s%d" % (setting, task, repeat, seed),
                       setting_id=setting, task_id=task, repeat_idx=repeat, seed=seed,
                       final_status="error", note=str(e))
            cases = []
        row["framework"] = a.framework
        row["model"] = a.model
        rows.append(row)
        all_cases.extend(cases)
        print("%-22s %-12s pass=%s/%s" % (row["run_id"], row["final_status"],
                                          row["test_passed"] or 0, row["test_total"] or 0))

    with (out_dir / "summary.csv").open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=SUMMARY_FIELDS)
        w.writeheader()
        w.writerows(rows)
    with (out_dir / "runs.jsonl").open("w", encoding="utf-8") as f:
        for r in all_cases:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    n_missing = sum(1 for r in rows if r["final_status"] == "missing")
    print("\nrun %d 个，缺失 %d（%.1f%%），结果 -> %s"
          % (len(rows), n_missing, 100.0 * n_missing / max(len(rows), 1), out_dir))
    return 0


if __name__ == "__main__":
    sys.exit(main())

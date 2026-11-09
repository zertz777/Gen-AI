"""Read only the frozen experiment records and build reproducible result tables.

Run without --final during the live batch. Final mode refuses incomplete 8 x 4 runs.
This script never calls a model and never reads API credentials.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path


HERE = Path(__file__).resolve().parent
RUNS = HERE / "archive" / "source_runs"
SETTINGS = ("E1", "E2", "E3", "E4")
FROZEN = ("P01", "P08", "P13", "P14", "P17", "P18", "P19", "S11")
EXPECTED = {f"{setting}_{task}_1_42" for setting in SETTINGS for task in FROZEN}
GROUPS = {
    "E1": ("baseline", "deepseek-v4.1-flash"),
    "E2": ("baseline", "gpt-6.1-sol"),
    "E3": ("self", "deepseek-v4.1-flash"),
    "E4": ("self", "gpt-6.1-sol"),
}
FIELDS = (
    "run_id", "setting_id", "task_id", "framework", "model", "source_batch",
    "result_path", "final_status", "compile_status", "test_passed", "test_total",
    "latency_s", "repair_rounds", "tokens_in", "tokens_out", "usage_known",
)


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def read_old() -> dict[str, dict]:
    path = RUNS / "formal34_v7" / "composite_runs.jsonl"
    result = {}
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        key = row["run_id"]
        if key in result:
            raise ValueError(f"Duplicate old run: {key}")
        result[key] = row
    if len(result) != 136:
        raise ValueError(f"Expected 136 original runs, found {len(result)}")
    for setting in SETTINGS:
        tasks = [row["task_id"] for row in result.values() if row["setting_id"] == setting]
        if len(tasks) != 34 or len(set(tasks)) != 34:
            raise ValueError(f"Original group {setting} is not 34 unique tasks")
    return result


def read_frozen() -> dict[str, dict]:
    live = RUNS / "formal34_frozen8_v1" / "live"
    result = {}
    if not live.exists():
        return result
    for path in sorted(live.glob("*/result.json")):
        run_id = path.parent.name
        if run_id not in EXPECTED:
            raise ValueError(f"Unexpected result in frozen batch: {run_id}")
        row = read_json(path)
        if row.get("run_id") != run_id:
            raise ValueError(f"Run ID mismatch: {path}")
        setting, task = row["setting_id"], row["task_id"]
        if run_id != f"{setting}_{task}_1_42":
            raise ValueError(f"Task or setting mismatch: {path}")
        if (row.get("framework"), row.get("model")) != GROUPS[setting]:
            raise ValueError(f"Model or framework mismatch: {path}")
        result[run_id] = row
    return result


def write_csv(path: Path, columns: tuple[str, ...], rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def source_path(row: dict, fresh: bool) -> str:
    if fresh:
        batch = "formal34_frozen8_v1"
    elif row["setting_id"] == "E3" and row["task_id"] not in ("P15", "P20"):
        batch = "formal34_v6"
    else:
        batch = "formal34_v7"
    path = f"{batch}/live/{row['run_id']}/result.json"
    if not (RUNS / path).is_file():
        raise ValueError(f"Missing evidence file: {path}")
    return path


def final_tables(old: dict[str, dict], fresh: dict[str, dict], out: Path) -> None:
    missing = EXPECTED - fresh.keys()
    if missing:
        raise ValueError(f"Frozen batch is incomplete: {len(missing)} runs missing")
    combined = {key: value for key, value in old.items() if value["task_id"] not in FROZEN}
    combined.update(fresh)
    if len(combined) != 136:
        raise ValueError(f"Combined matrix has {len(combined)} rows instead of 136")
    rows = []
    for key in sorted(combined):
        row = combined[key]
        setting = row["setting_id"]
        if (row.get("framework"), row.get("model")) != GROUPS[setting]:
            raise ValueError(f"Model or framework mismatch: {key}")
        fresh_row = key in fresh
        rows.append({**row, "source_batch": "frozen8_v1" if fresh_row else "original",
                     "result_path": source_path(row, fresh_row),
                     "usage_known": row.get("tokens_in") is not None and row.get("tokens_out") is not None})
    for setting in SETTINGS:
        tasks = [row["task_id"] for row in rows if row["setting_id"] == setting]
        if len(tasks) != 34 or len(set(tasks)) != 34:
            raise ValueError(f"Combined group {setting} is not 34 unique tasks")
    write_csv(out / "逐题逐组结果.csv", FIELDS, rows)

    tasks = sorted({row["task_id"] for row in rows})
    matrix = []
    for task in tasks:
        by_group = {row["setting_id"]: row for row in rows if row["task_id"] == task}
        matrix.append({"task_id": task, **{setting: by_group[setting]["final_status"]
                                           for setting in SETTINGS}})
    write_csv(out / "34题四组矩阵.csv", ("task_id", *SETTINGS), matrix)

    groups = []
    for setting in SETTINGS:
        group = [row for row in rows if row["setting_id"] == setting]
        passed = sum(row["final_status"] == "passed" for row in group)
        known = [row for row in group if row["usage_known"]]
        status_counts = Counter(row["final_status"] for row in group)
        groups.append({"setting_id": setting, "framework": GROUPS[setting][0],
                       "model": GROUPS[setting][1], "tasks": 34, "passed": passed,
                       "strict_pass_rate": f"{passed / 34:.4f}",
                       "compile_pass": sum(row["compile_status"] == "pass" for row in group),
                       "known_tokens_in": sum(row["tokens_in"] for row in known),
                       "known_tokens_out": sum(row["tokens_out"] for row in known),
                       "unknown_usage_runs": 34 - len(known),
                       "status_counts_json": json.dumps(status_counts, ensure_ascii=False, sort_keys=True)})
    write_csv(out / "四组汇总.csv", tuple(groups[0]), groups)
    (out / "统计口径.txt").write_text(
        "四组汇总为每题一次、每组34题的严格口径。技术故障、超时和预算终止在状态列单列，不会伪装成通过。"
        "token仅求已知usage之和；未知usage次数单列，金额需查DMXAPI单价和账单。"
        "P19/S11用例争议未解决前，四组汇总只是可追溯的原始判定，不宜作最终模型结论。\n",
        encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--final", action="store_true", help="Require all 32 frozen runs and write final tables")
    parser.add_argument("--out", type=Path, default=HERE)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    old = read_old()
    fresh = read_frozen()
    progress = {"expected_frozen_runs": 32, "completed_frozen_runs": len(fresh),
                "missing_run_ids": sorted(EXPECTED - fresh.keys()), "groups": {}}
    for setting in SETTINGS:
        group = [row for row in fresh.values() if row["setting_id"] == setting]
        progress["groups"][setting] = {
            "completed": len(group), "passed": sum(row["final_status"] == "passed" for row in group),
            "statuses": dict(Counter(row["final_status"] for row in group))}
    (args.out / "当前进度.json").write_text(json.dumps(progress, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Frozen reruns: {len(fresh)}/32. Progress: {args.out / '当前进度.json'}")
    if args.final:
        final_tables(old, fresh, args.out)
        print(f"Final 34 x 4 tables written to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

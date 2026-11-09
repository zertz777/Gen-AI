"""Recompute formal experiment metrics from experiments/per_task.csv."""
from __future__ import annotations

import argparse
import csv
import json
import statistics
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TABLE = ROOT / "experiments" / "per_task.csv"
DEFAULT_OUTPUT = ROOT / "experiments" / "summary.csv"
SETTINGS = ("E1", "E2", "E3", "E4")


def percentile_95(values: list[float]) -> float:
    ordered = sorted(values)
    position = 0.95 * (len(ordered) - 1)
    low = int(position)
    high = min(low + 1, len(ordered) - 1)
    return ordered[low] + (ordered[high] - ordered[low]) * (position - low)


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != 136:
        raise ValueError(f"Expected 136 final records, found {len(rows)}")
    for setting in SETTINGS:
        group = [row for row in rows if row["setting_id"] == setting]
        if len(group) != 34 or len({row["task_id"] for row in group}) != 34:
            raise ValueError(f"{setting} must contain 34 unique tasks")
    return rows


def number(value: str) -> float | None:
    return None if value in ("", "None", "null") else float(value)


def summarize(rows: list[dict[str, str]]) -> list[dict[str, str | int | float]]:
    result: list[dict[str, str | int | float]] = []
    for setting in SETTINGS:
        group = [row for row in rows if row["setting_id"] == setting]
        passed = sum(row["final_status"] == "passed" for row in group)
        compile_pass = sum(row["compile_status"] == "pass" for row in group)
        test_total = sum(int(row["test_total"]) for row in group)
        test_passed = sum(int(row["test_passed"]) for row in group)
        latencies = [
            value
            for row in group
            if (value := number(row["latency_s"])) is not None
        ]
        known = [
            row
            for row in group
            if row["tokens_in"] not in ("", "None", "null")
            and row["tokens_out"] not in ("", "None", "null")
        ]
        statuses = Counter(row["final_status"] for row in group)
        result.append(
            {
                "setting_id": setting,
                "framework": group[0]["framework"],
                "model": group[0]["model"],
                "tasks": 34,
                "passed": passed,
                "strict_pass_rate": f"{passed / 34:.4f}",
                "compile_pass": compile_pass,
                "compile_rate": f"{compile_pass / 34:.4f}",
                "test_cases_entered": test_total,
                "test_cases_passed": test_passed,
                "test_case_pass_rate": f"{test_passed / test_total:.4f}" if test_total else "0.0000",
                "avg_repair_rounds": f"{statistics.mean(float(row['repair_rounds']) for row in group):.2f}",
                "median_latency_s": f"{statistics.median(latencies):.1f}",
                "p95_latency_s": f"{percentile_95(latencies):.1f}",
                "known_tokens_in": sum(int(row["tokens_in"]) for row in known),
                "known_tokens_out": sum(int(row["tokens_out"]) for row in known),
                "unknown_usage_runs": 34 - len(known),
                "status_counts_json": json.dumps(statuses, ensure_ascii=False, sort_keys=True),
            }
        )
    return result


def write_summary(path: Path, rows: list[dict[str, str | int | float]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=tuple(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--table", type=Path, default=DEFAULT_TABLE)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check", action="store_true", help="Also compare with an existing summary")
    args = parser.parse_args()

    rows = read_rows(args.table)
    summary = summarize(rows)
    write_summary(args.out, summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if args.check:
        with args.out.open(encoding="utf-8-sig", newline="") as handle:
            written = list(csv.DictReader(handle))
        if written != [{key: str(value) for key, value in row.items()} for row in summary]:
            raise RuntimeError("summary.csv is not reproducible from per_task.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

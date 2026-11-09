"""Read-only consistency check for the merged experiment evidence."""
from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TABLE = ROOT / "experiments" / "per_task.csv"
RUNS = ROOT / "experiments" / "runs"
ARCHIVE = ROOT / "experiments" / "archive" / "source_runs"
FIGURES = ROOT / "figures"
EXPECTED = {
    "E1": ("baseline", "deepseek-v4.1-flash", 18),
    "E2": ("baseline", "gpt-6.1-sol", 16),
    "E3": ("self", "deepseek-v4.1-flash", 8),
    "E4": ("self", "gpt-6.1-sol", 7),
}


def main() -> int:
    with TABLE.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 136, f"Expected 136 result rows, found {len(rows)}"

    for setting, (framework, model, expected_passed) in EXPECTED.items():
        selected = [row for row in rows if row["setting_id"] == setting]
        assert len(selected) == 34
        assert len({row["task_id"] for row in selected}) == 34
        assert all(row["framework"] == framework and row["model"] == model for row in selected)
        passed = sum(row["final_status"] == "passed" for row in selected)
        assert passed == expected_passed, (setting, passed)
        print(f"{setting}: {passed}/34")

    batches = Counter(row["source_batch"] for row in rows)
    assert batches == {"original": 104, "frozen8_v1": 32}, batches

    for row in rows:
        canonical = RUNS / row["setting_id"] / row["run_id"] / "result.json"
        archived = ARCHIVE / row["result_path"]
        assert canonical.is_file(), f"Missing canonical evidence: {canonical}"
        assert archived.is_file(), f"Missing archive evidence: {archived}"
        canonical_result = json.loads(canonical.read_text(encoding="utf-8-sig"))
        archived_result = json.loads(archived.read_text(encoding="utf-8-sig"))
        assert canonical_result == archived_result, f"Evidence mismatch: {row['run_id']}"
        assert canonical_result["final_status"] == row["final_status"]

    frozen = list((ARCHIVE / "formal34_frozen8_v1" / "live").glob("*/result.json"))
    assert len(frozen) == 32, f"Expected 32 revised runs, found {len(frozen)}"
    for name in (
        "fig4-1_strict_pass.png",
        "fig4-2_difficulty.png",
        "fig4-3_status.png",
        "fig4-4_latency.png",
    ):
        assert (FIGURES / name).is_file(), f"Missing figure: {name}"
    print("PASS: 136 final runs, 32 revised reruns, 104 original rows, four figures")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

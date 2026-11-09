"""Read-only checks for the self-contained group 3 experiment package."""
from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RUNS = ROOT / "正式实验_runs"
STATS = ROOT / "统计输出"
EXPECTED = {
    "E1": ("baseline", "deepseek-v4.1-flash", 18),
    "E2": ("baseline", "gpt-6.1-sol", 16),
    "E3": ("self", "deepseek-v4.1-flash", 8),
    "E4": ("self", "gpt-6.1-sol", 7),
}


def main() -> None:
    with (STATS / "逐题逐组结果.csv").open(encoding="utf-8-sig", newline="") as handle:
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
        path = RUNS / row["result_path"]
        assert path.is_file(), f"Missing evidence: {path}"
        result = json.loads(path.read_text(encoding="utf-8-sig"))
        assert result["run_id"] == row["run_id"]
        assert result["final_status"] == row["final_status"]
    assert (RUNS / "formal34_v7" / "composite_runs.jsonl").is_file()
    assert len(list((STATS / "figures").glob("*.png"))) == 4
    print("PASS: 136 evidence records, 32 revised reruns, four figures")


if __name__ == "__main__":
    main()

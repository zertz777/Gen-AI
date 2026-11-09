"""Run the repository ST interpreter against every final run that has source."""
from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--table", type=Path, default=ROOT / "experiments" / "per_task.csv")
    parser.add_argument(
        "--out",
        type=Path,
        default=ROOT / "experiments" / "reproduction",
    )
    args = parser.parse_args()

    with args.table.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    args.out.mkdir(parents=True, exist_ok=True)
    summary_path = args.out / "summary.jsonl"
    records = []

    for index, row in enumerate(rows, 1):
        run_id = row["run_id"]
        setting = row["setting_id"]
        task_id = row["task_id"]
        run_dir = ROOT / "experiments" / "runs" / setting / run_id
        source = run_dir / "final.st"
        output_dir = args.out / setting / run_id
        actual_dir = output_dir / "actual"
        result_path = output_dir / "cases_result.jsonl"
        cases = ROOT / "tests" / "cases" / f"{task_id}.csv"
        io = ROOT / "tests" / "cases" / "_fixtures" / f"{task_id}.io.json"
        record = {
            "run_id": run_id,
            "setting_id": setting,
            "task_id": task_id,
            "official_final_status": row["final_status"],
            "evidence_kind": "independent_replay",
            "source_present": source.is_file(),
        }
        if not source.is_file():
            record["replay_status"] = "skipped_no_source"
            records.append(record)
            print(f"[{index:03d}/136] {run_id} skipped: no final.st", flush=True)
            continue

        output_dir.mkdir(parents=True, exist_ok=True)
        interp = subprocess.run(
            [
                sys.executable,
                str(ROOT / "tests" / "runner" / "interp" / "run.py"),
                "--source",
                str(source),
                "--cases",
                str(cases),
                "--io",
                str(io),
                "--out-dir",
                str(actual_dir),
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=60,
        )
        record["interpreter_exit"] = interp.returncode
        if interp.returncode != 0:
            record["replay_status"] = "interpreter_error"
            record["stderr"] = interp.stderr[-1200:]
            records.append(record)
            print(f"[{index:03d}/136] {run_id} interpreter_error", flush=True)
            continue

        replay = subprocess.run(
            [
                sys.executable,
                str(ROOT / "tests" / "run_tests.py"),
                "--cases",
                str(cases),
                "--io",
                str(io),
                "--out",
                str(result_path),
                "--backend",
                "replay",
                "--actual",
                str(actual_dir),
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=60,
        )
        record["replay_exit"] = replay.returncode
        record["replay_status"] = "completed" if replay.returncode in (0, 1) else "replay_error"
        record["stdout"] = replay.stdout.strip()
        if replay.returncode not in (0, 1):
            record["stderr"] = replay.stderr[-1200:]
        records.append(record)
        print(
            f"[{index:03d}/136] {run_id} {record['replay_status']} {record['stdout']}",
            flush=True,
        )

    summary_path.write_text(
        "".join(json.dumps(record, ensure_ascii=False) + "\n" for record in records),
        encoding="utf-8",
    )
    completed = sum(record["replay_status"] == "completed" for record in records)
    skipped = sum(record["replay_status"] == "skipped_no_source" for record in records)
    errors = len(records) - completed - skipped
    print(f"summary: {summary_path}")
    print(f"completed={completed} skipped_no_source={skipped} errors={errors}")
    return 0 if errors == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

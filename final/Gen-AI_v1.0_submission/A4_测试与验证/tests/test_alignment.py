"""成员3 对账脚本的单测：一致时退出 0，有差异时退出 1。"""
import csv
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "gen"))

import check_alignment                       # noqa: E402

DRY = HERE / "results" / "_dryrun" / "summary.csv"


def test_alignment_identical():
    assert check_alignment.main(["--ours", str(DRY), "--theirs", str(DRY)]) == 0


def test_alignment_detects_changed_row(tmp_path):
    with DRY.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    rows[0]["test_passed"] = "999"
    bad = tmp_path / "bad.csv"
    with bad.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)
    assert check_alignment.main(["--ours", str(DRY), "--theirs", str(bad)]) == 1


def test_alignment_setting_filter(tmp_path):
    with DRY.open(encoding="utf-8-sig", newline="") as f:
        rows = [r for r in csv.DictReader(f) if r["setting_id"] == "E3"]
    sub = tmp_path / "e3.csv"
    with sub.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)
    assert check_alignment.main(["--ours", str(DRY), "--theirs", str(sub),
                                 "--setting", "E3"]) == 0

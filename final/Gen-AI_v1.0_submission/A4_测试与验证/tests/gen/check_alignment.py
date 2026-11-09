"""对账：成员4 的 summary.csv ↔ 成员3 的 summary.csv。

    python gen/check_alignment.py --ours tests/results/batch/E3/summary.csv \
        --theirs experiments/summary.csv --setting E3

只比三样（这三样一致，指标就一致）：
1. run_id 集合；
2. 每个 run 的 test_total 与 test_passed；
3. 用例总数与通过总数。

退出码 0 = 一致，1 = 有差异（差异逐条打印）。
"""
from __future__ import annotations

import argparse
import csv
import sys


def load(path, setting=None):
    with open(path, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    if setting:
        rows = [r for r in rows if (r.get("setting_id") or setting) == setting]
    return rows


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--ours", required=True)
    ap.add_argument("--theirs", required=True)
    ap.add_argument("--setting", help="只比某一组（E1—E4）")
    a = ap.parse_args(argv)

    ours = {r["run_id"]: r for r in load(a.ours, a.setting)}
    theirs = {r["run_id"]: r for r in load(a.theirs, a.setting)}

    problems = []
    only_ours = sorted(set(ours) - set(theirs))
    only_theirs = sorted(set(theirs) - set(ours))
    if only_ours:
        problems.append("只在成员4 结果里：%s" % only_ours[:10])
    if only_theirs:
        problems.append("只在成员3 结果里：%s" % only_theirs[:10])

    for rid in sorted(set(ours) & set(theirs)):
        o, t = ours[rid], theirs[rid]
        for col in ("test_total", "test_passed"):
            if str(o.get(col, "")) != str(t.get(col, "")):
                problems.append("%s 的 %s：成员4=%r 成员3=%r"
                                % (rid, col, o.get(col), t.get(col)))

    so = sum(int(r.get("test_total") or 0) for r in ours.values())
    st = sum(int(r.get("test_total") or 0) for r in theirs.values())
    po = sum(int(r.get("test_passed") or 0) for r in ours.values())
    pt = sum(int(r.get("test_passed") or 0) for r in theirs.values())
    if (so, po) != (st, pt):
        problems.append("合计不一致：用例 %d/%d，通过 %d/%d" % (so, st, po, pt))

    print("run 数：成员4 %d，成员3 %d" % (len(ours), len(theirs)))
    print("用例合计：%d；通过合计：%d" % (so, po))
    if problems:
        print("差异 %d 条：" % len(problems))
        for p in problems:
            print("  -", p)
        return 1
    print("一致：run_id、test_total、test_passed 三项全部对得上")
    return 0


if __name__ == "__main__":
    sys.exit(main())

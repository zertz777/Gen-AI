"""从上游 data/tasks/*.yaml 生成 34 份 fixture，并刷新 tests/coverage.csv。

    python tests/gen/gen_fixtures.py
    python tests/gen/gen_fixtures.py --tasks <目录> --out <目录> --coverage <文件>

产物：
    tests/cases/_fixtures/<题号>.io.json   每题一份 I/O 方向与类型
    tests/coverage.csv                     K -> LTL 条款 -> 用例 的双向索引
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from collections import defaultdict
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent          # tests/gen
TESTS = HERE.parent                             # tests
ROOT = TESTS.parent.parent                      # 仓库根

sys.path.insert(0, str(TESTS))
from runner.io_normalize import dump, normalize  # noqa: E402

K_RE = re.compile(r"^\s*(K\d+)\s*[—–\-:：]?\s*(.*)$", re.S)
C_RE = re.compile(r"^(C\d+b?)\s*:", re.M)
K_REF_RE = re.compile(r"K\d+")


def load_tasks(tasks_dir: Path) -> list:
    cards = []
    for f in sorted(tasks_dir.glob("*.yaml")):
        cards.append(yaml.safe_load(f.read_text(encoding="utf-8")))
    return cards


def parse_constraints(card: dict) -> list:
    """[('K1', '...'), ...]，保持 yaml 里的顺序。"""
    out = []
    for raw in card.get("constraints") or []:
        m = K_RE.match(str(raw))
        if m:
            out.append((m.group(1), " ".join(m.group(2).split())))
    return out


def parse_ltl(spec_path: Path) -> dict:
    """{C 号: [引用的 K 号, ...]}；文件不存在时返回空。"""
    if not spec_path.exists():
        return {}
    text = spec_path.read_text(encoding="utf-8", errors="replace")
    refs = {}
    for line in text.splitlines():
        m = C_RE.match(line)
        if m:
            refs[m.group(1)] = sorted(set(K_REF_RE.findall(line)))
    return refs


def scan_cases(cases_dir: Path) -> dict:
    """{(题号, K 号): [case_id, ...]}，合并该用例所有行的 spec_refs。"""
    hit = defaultdict(list)
    for csv_path in sorted(cases_dir.glob("*.csv")):
        if csv_path.name.startswith("_"):
            continue
        tid = csv_path.stem
        with csv_path.open(encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                for ref in (row.get("spec_refs") or "").split(";"):
                    ref = ref.strip()
                    if ref.startswith("K"):
                        hit[(tid, ref)].append(row["case_id"].strip())
    return hit


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--tasks", default=str(ROOT / "组员1_提交包" / "data" / "tasks"))
    ap.add_argument("--specs", default=str(ROOT / "组员1_提交包" / "data" / "specs"))
    ap.add_argument("--out", default=str(TESTS / "cases" / "_fixtures"))
    ap.add_argument("--cases", default=str(TESTS / "cases"))
    ap.add_argument("--coverage", default=str(TESTS / "coverage.csv"))
    a = ap.parse_args(argv)

    tasks_dir = Path(a.tasks)
    if not tasks_dir.is_dir():
        print("找不到题目目录：%s" % tasks_dir, file=sys.stderr)
        return 2

    cards = load_tasks(tasks_dir)
    out_dir = Path(a.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    n_io = 0
    problems = []
    for card in cards:
        tid = card["task_id"]
        fx = normalize(card)
        names = [r["name"] for r in fx["io"]]
        dup = {n for n in names if names.count(n) > 1}
        if dup:
            problems.append("%s 规范化后出现重名列：%s" % (tid, sorted(dup)))
        dump(card, str(out_dir))
        n_io += len(fx["io"])

    cases_hit = scan_cases(Path(a.cases))
    specs_dir = Path(a.specs)

    rows = []
    for card in cards:
        tid = card["task_id"]
        ltl = parse_ltl(specs_dir / ("%s.ltl" % tid))
        for k_id, k_text in parse_constraints(card):
            clauses = [c for c, ks in ltl.items() if k_id in ks]
            cases = cases_hit.get((tid, k_id), [])
            rows.append({
                "task_id": tid,
                "k_id": k_id,
                "k_text": k_text,
                "ltl_clauses": ";".join(clauses),
                "cases": ";".join(dict.fromkeys(cases)),
                "status": "已覆盖" if cases else "未覆盖",
            })

    cov = Path(a.coverage)
    cov.parent.mkdir(parents=True, exist_ok=True)
    with cov.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["task_id", "k_id", "k_text",
                                          "ltl_clauses", "cases", "status"])
        w.writeheader()
        w.writerows(rows)

    n_k = len(rows)
    n_cov = sum(1 for r in rows if r["status"] == "已覆盖")
    print("题目 %d 道，I/O 列 %d 个，K 条款 %d 条（已覆盖 %d，未覆盖 %d）"
          % (len(cards), n_io, n_k, n_cov, n_k - n_cov))
    print("fixture -> %s" % out_dir)
    print("coverage -> %s" % cov)
    for p in problems:
        print("WARN %s" % p, file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())

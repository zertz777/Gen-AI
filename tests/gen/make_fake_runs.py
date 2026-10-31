"""生成一套「假」实验目录，用来在成员2 交付 actual 之前压测 run_batch。

**这不是实验结果。** 它只做三件事：

1. 按 `experiments/runs/<E1—E4>/<题号>_r1_s42/` 的真实目录形状铺 136 个 run；
2. 用用例的期望值伪造 `test/actual/<case_id>.csv`（等于 echo 后端的结果）；
3. 按确定性规则注入 missing / timeout / 部分缺文件 / 单拍错值 / 缺列，
   覆盖 run_batch 的全部结局分支。

产物：
    <out>/<setting>/<task>_r1_s42/...   # 假 run 目录
    <out>/manifest.json                 # 每个 run 的预期结局，供自检比对

用法：
    python gen/make_fake_runs.py --out %TEMP%/fake_runs
    python run_batch.py --runs %TEMP%/fake_runs --out %TEMP%/fake_batch
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
import zlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
TESTS = HERE.parent
CASES = TESTS / "cases"

sys.path.insert(0, str(TESTS))
from runner.case_loader import load_cases, load_io  # noqa: E402

TASKS = ["P%02d" % i for i in range(1, 21)] + ["S%02d" % i for i in range(1, 15)]
SETTINGS = ["E1", "E2", "E3", "E4"]


def _fmt(v, typ):
    if v == "X":                                  # 期望侧不判定，actual 必须给具体值
        if typ == "BOOL":
            return "FALSE"
        if typ in ("WORD", "DWORD"):
            return "16#0000"
        if typ.startswith("ARRAY"):
            return "[]"
        if typ.startswith("ST_") or typ == "VARIANT":
            return "{}"
        return "0"
    if isinstance(v, bool):
        return "TRUE" if v else "FALSE"
    if typ in ("TIME", "LTIME"):
        return "T#%dms" % int(v)
    if isinstance(v, list):
        return json.dumps(v, ensure_ascii=False).replace("true", "TRUE").replace("false", "FALSE")
    if isinstance(v, dict):
        return json.dumps(v, ensure_ascii=False)
    return str(v)


def _outcome(setting, task):
    """确定性分配结局，保证每次跑出来的分布一样。"""
    h = zlib.crc32(("%s|%s" % (setting, task)).encode("utf-8")) % 100
    if setting in ("E1", "E2"):
        if h < 8:
            return "missing"          # 整个 run 没 actual
        if h < 14:
            return "timeout"          # status.json: compile timeout
        if h < 26:
            return "partial"          # 少一个 case 文件 → error
        if h < 40:
            return "wrong"            # 单拍错值 → fail
    else:
        if h < 3:
            return "missing"
        if h < 5:
            return "corrupt"          # actual 缺输出列 → error
    return "pass"


def _write_actual(case, outs, path, corrupt=False, wrong=False):
    cols = list(outs)
    flipped = False
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        header = ["case_id", "cycle"] + (cols[:-1] if corrupt else cols)
        w.writerow(header)
        for cyc in case.cycles[1:]:
            vals = [_fmt(cyc["out"][k], outs[k]) for k in cols]
            if wrong and cyc["cycle"] == 1:
                for i, k in enumerate(cols):
                    if cyc["out"][k] == "X":
                        continue
                    if outs[k] == "BOOL":
                        vals[i] = "FALSE" if vals[i] == "TRUE" else "TRUE"
                    elif outs[k] in ("INT", "DINT", "UINT", "UDINT", "SINT", "USINT"):
                        vals[i] = str(int(float(vals[i])) + 1)
                    elif outs[k] in ("REAL", "LREAL"):
                        vals[i] = repr(float(vals[i]) + 1.0)
                    else:
                        continue
                    flipped = True
                    break
            w.writerow([case.case_id, cyc["cycle"]] + (vals[:-1] if corrupt else vals))
    return flipped


def build(out_dir, settings=None, tasks=None, repeat=1, seed=42, force=None):
    out = Path(out_dir)
    settings = settings or SETTINGS
    tasks = tasks or TASKS
    manifest = {}
    force = force or {}

    for setting in settings:
        for task in tasks:
            outcome = force.get((setting, task)) or _outcome(setting, task)
            run = out / setting / ("%s_r%d_s%d" % (task, repeat, seed))
            (run / "source").mkdir(parents=True, exist_ok=True)
            (run / "source" / "final.st").write_text(
                "(* fake run for pipeline dry-run: %s %s *)\nPROGRAM P END_PROGRAM\n"
                % (setting, task), encoding="utf-8")
            (run / "test").mkdir(exist_ok=True)

            cases_csv = CASES / ("%s.csv" % task)
            io_json = CASES / "_fixtures" / ("%s.io.json" % task)
            _, _, outs = load_io(io_json)
            _, cases = load_cases(cases_csv, io_json)

            run_id = "%s_%s_r%d_s%d" % (setting, task, repeat, seed)
            if outcome == "missing":
                manifest[run_id] = dict(outcome=outcome, final="missing",
                                        total=len(cases), passed=0)
                continue
            if outcome == "timeout":
                (run / "test" / "status.json").write_text(
                    json.dumps({"status": "timeout", "reason": "compile timeout 90s"}),
                    encoding="utf-8")
                manifest[run_id] = dict(outcome=outcome, final="abandoned",
                                        total=len(cases), passed=0)
                continue

            actual = run / "test" / "actual"
            actual.mkdir(exist_ok=True)
            skip = cases[-1].case_id if outcome == "partial" else None
            flipped = False
            for case in cases:
                if case.case_id == skip:
                    continue
                flipped = _write_actual(case, outs, actual / ("%s.csv" % case.case_id),
                                        corrupt=(outcome == "corrupt"),
                                        wrong=(outcome == "wrong"
                                               and case.case_id == cases[0].case_id)) or flipped

            if outcome == "partial":
                final, passed = "best-effort", len(cases) - 1
            elif outcome == "corrupt":
                final, passed = "abandoned", 0
            elif outcome == "wrong" and flipped:
                final, passed = "best-effort", len(cases) - 1
            else:
                final, passed = "passed", len(cases)
            manifest[run_id] = dict(outcome=outcome, final=final,
                                    total=len(cases), passed=passed)

    (out / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(Path.home() / "fake_runs"))
    ap.add_argument("--settings", default=",".join(SETTINGS))
    ap.add_argument("--tasks", default="", help="逗号分隔，默认 34 题全跑")
    ap.add_argument("--repeat", type=int, default=1)
    ap.add_argument("--seed", type=int, default=42)
    a = ap.parse_args(argv)

    out = Path(a.out)
    if "experiments" in str(out).replace("\\", "/").split("/"):
        raise SystemExit("拒绝写入 experiments/：这里只生成假数据")
    settings = [s.strip() for s in a.settings.split(",") if s.strip()]
    tasks = [t.strip() for t in a.tasks.split(",") if t.strip()] or None

    m = build(out, settings, tasks, a.repeat, a.seed)
    from collections import Counter
    print("假 run %d 个 -> %s" % (len(m), out))
    print("结局分布：%s" % dict(Counter(v["outcome"] for v in m.values())))
    return 0


if __name__ == "__main__":
    sys.exit(main())

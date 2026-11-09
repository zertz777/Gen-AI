"""生成给成员2 的 actual 示例包（一个完整 run 的目录形状）。

    python gen/make_example_package.py
    python gen/make_example_package.py --out ../../examples/actual_package

产物：

    <out>/README.md
    <out>/E3_P03_r1_s42/source/final.st          # 占位，成员2 换成真程序
    <out>/E3_P03_r1_s42/test/actual/P03-0x.csv   # 逐拍实际输出（真实格式）
    <out>/E3_P03_r1_s42/test/status.json.example # 整题超时怎么写（正常跑完不要放）

示例里的 actual 由 P03 的期望值生成，只用来演示格式，**不是任何程序的真实结果**。
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TESTS = HERE.parent
sys.path.insert(0, str(TESTS))
sys.path.insert(0, str(HERE))

from _emit import fmt                       # noqa: E402
from runner.case_loader import load_cases, load_io  # noqa: E402

TASK = "P03"
RUN = "E3_%s_r1_s42" % TASK


def _concrete(v, typ):
    if v == "X":
        if typ == "BOOL":
            return False
        if typ in ("WORD", "DWORD"):
            return 0
        if typ.startswith("ARRAY"):
            return []
        return 0
    return v


def build(out: Path):
    cases_csv = TESTS / "cases" / ("%s.csv" % TASK)
    io_json = TESTS / "cases" / "_fixtures" / ("%s.io.json" % TASK)
    _, _, outs = load_io(io_json)
    _, cases = load_cases(cases_csv, io_json)

    run = out / RUN
    (run / "source").mkdir(parents=True, exist_ok=True)
    (run / "test" / "actual").mkdir(parents=True, exist_ok=True)

    (run / "source" / "final.st").write_text(
        "(* 占位：这里放被测程序 final.st。\n"
        "   成员2 只需要保证这个文件 + test/actual/*.csv 存在。 *)\n"
        "FUNCTION_BLOCK FB_AlarmHandling\n"
        "VAR_INPUT\n"
        "    Value : REAL;\n"
        "    hiLevel : REAL;\n"
        "    loLevel : REAL;\n"
        "    hystWindow : REAL;\n"
        "END_VAR\n"
        "VAR_OUTPUT\n"
        "    hiAlarm : BOOL;\n"
        "    loAlarm : BOOL;\n"
        "    error : BOOL;\n"
        "    status : WORD;\n"
        "END_VAR\n"
        "(* 实现由成员2 生成 *)\n"
        "END_FUNCTION_BLOCK\n", encoding="utf-8")

    for case in cases:
        with (run / "test" / "actual" / ("%s.csv" % case.case_id)).open(
                "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(["case_id", "cycle"] + list(outs))
            for cyc in case.cycles[1:]:
                w.writerow([case.case_id, cyc["cycle"]]
                           + [fmt(_concrete(cyc["out"][k], outs[k]), outs[k]) for k in outs])

    (run / "test" / "status.json.example").write_text(
        json.dumps({"status": "timeout", "reason": "compile timeout 90s"},
                   ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # 成员2 的 task_card（tester_cli 需要它来还原 I/O 方向与类型）
    fx = json.loads(io_json.read_text(encoding="utf-8"))
    (run / "task_card.json").write_text(
        json.dumps({"task_id": TASK,
                    "io_table": [{"name": r["name"], "direction": r["direction"],
                                  "data_type": r["type"]} for r in fx["io"]]},
                   ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return run


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(TESTS.parent / "examples" / "actual_package"))
    a = ap.parse_args(argv)
    out = Path(a.out)
    run = build(out)
    print("示例包 -> %s" % out)
    print("run 目录 -> %s" % run)
    return 0


if __name__ == "__main__":
    sys.exit(main())

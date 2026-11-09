"""变异测试执行器（成员4，D4.5 的小批真实样例）。

底本是**真实模型产物**：`03_程序案例/E1_S10_1_42/final.st`（Aider + DeepSeek，官方判定 6/6 通过）。
执行通道是本仓库的 ST 解释器（`tests/runner/interp/`），因为实验机的 CODESYS 不在本机。

为什么可以用真实底本、也可以用解释器：
- 变异测试衡量的是**用例强度**（能不能发现人为注入的缺陷），与生成模型无关；
- 解释器已对 4 份真实产物做过交叉验证（4/4，且通过用例集合与官方 evaluation 完全一致），
  语义可信度见 `docs/判据与用例版本核对.md` 与 `tests/report.md` §3.2。

计分口径（与 `plan_d3.md` 一致）：
- `killed`   ：该题任一用例 `fail`（记首个失配的拍与变量）；
- `survived` ：全部用例 `pass` —— 说明用例强度不够，应补用例；
- `invalid`  ：所有用例都 `error`（解释器不支持该写法）或变异体无法生成，不计入分母。

用法：
    python verify/run_mutants.py --task S10
    python verify/run_mutants.py --task S10 --base <另一份 final.st>
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
GROUP = HERE.parents[1]                    # 组员4/
WORKSPACE = HERE.parents[2]                # 工作区根
TESTS = GROUP / "tests"
sys.path.insert(0, str(TESTS))

from runner.case_loader import load_cases                          # noqa: E402
from runner.compare import compare_case                            # noqa: E402
from runner.interp.eval import InterpError, Interpreter            # noqa: E402

DEFAULT_BASE = WORKSPACE / "03_程序案例" / "E1_S10_1_42" / "final.st"

#: 5 个变异体：题号 S10（故障锁存 + 复位上升沿），算子覆盖 plan_d3.md 的 5 类
MUTATIONS = [
    {
        "id": "M-S10-1",
        "operator": "条件取反",
        "desc": "重故障判据反相：IsHeavyFault 取 NOT",
        "patches": [(
            "IsHeavyFault := (VFDFaultCode = 16#0002) OR (VFDFaultCode = 16#0003);",
            "IsHeavyFault := NOT ((VFDFaultCode = 16#0002) OR (VFDFaultCode = 16#0003));",
        )],
        "expect_killer": "任一 code=0 的用例（例如 S10-01 第 1 拍）",
    },
    {
        "id": "M-S10-2",
        "operator": "边界偏移",
        "desc": "重故障阈值边界：16#0003 → 16#0004",
        "patches": [(
            "(VFDFaultCode = 16#0003)",
            "(VFDFaultCode = 16#0004)",
        )],
        "expect_killer": "S10-02（code=3 应跳闸）",
    },
    {
        "id": "M-S10-3",
        "operator": "运算符替换",
        "desc": "复位上升沿 → 电平触发",
        "patches": [(
            "ResetRising := ResetBtn AND NOT ResetBtnLast;",
            "ResetRising := ResetBtn;",
        )],
        "expect_killer": "按住复位时来了新故障的用例（S10-06）",
    },
    {
        "id": "M-S10-4",
        "operator": "常量替换",
        "desc": "锁存状态码常量：LatchedCode := VFDFaultCode → 16#0001",
        "patches": [(
            "LatchedCode := VFDFaultCode;",
            "LatchedCode := 16#0001;",
        )],
        "expect_killer": "S10-02（Status 应为 16#0002/16#0003）",
    },
    {
        "id": "M-S10-5",
        "operator": "语句删除",
        "desc": "删除复位分支的解锁存语句",
        "patches": [(
            "    LatchedTrip := FALSE;\n    LatchedCode := 16#0000;",
            "    LatchedCode := 16#0000;",
        )],
        "expect_killer": "S10-06（复位后应清 TripOutput）",
    },
]


def evaluate(text, task, cases):
    """在给定源码上跑全部用例，返回逐条结果。"""
    results = []
    for case in cases:
        itp = Interpreter.from_source(text, block="FB_" + task, cycle_ms=20.0)
        actual = []
        try:
            for c in case.cycles:
                itp.set_inputs(dict(c["in"]))
                if c["cycle"] == 0:
                    continue
                itp.run_cycle()
                actual.append({"cycle": c["cycle"],
                               "out": {n: v for n, _, v in itp.snapshot()}})
        except (InterpError, Exception) as e:      # noqa: BLE001 - 变异体可能写崩
            results.append({"case_id": case.case_id, "status": "error",
                            "detail": str(e)[:200]})
            continue
        ok, mm = compare_case(case, actual)
        results.append({"case_id": case.case_id,
                        "status": "pass" if ok else "fail",
                        "mismatch": mm})
    return results


def run_one(base_text, task, cases, mutation):
    text = base_text
    for old, new in mutation["patches"]:
        if old not in text:
            raise SystemExit("%s 的补丁没匹配上：\n%r" % (mutation["id"], old))
        text = text.replace(old, new, 1)
    return text, evaluate(text, task, cases)


def merge_cases(primary, extra, out_dir):
    """把补充用例拼到冻结用例后面（表头必须一致），返回合并后的临时文件。"""
    with open(primary, encoding="utf-8-sig", newline="") as fh:
        a = list(csv.reader(fh))
    with open(extra, encoding="utf-8-sig", newline="") as fh:
        b = list(csv.reader(fh))
    if a[0] != b[0]:
        raise SystemExit("补充用例的表头与冻结用例不一致")
    out_dir.mkdir(parents=True, exist_ok=True)
    merged = out_dir / ("merged_" + Path(primary).name)
    with open(merged, "w", encoding="utf-8", newline="") as fh:
        csv.writer(fh).writerows(a + b[1:])
    return merged


def main(argv=None):
    ap = argparse.ArgumentParser(description="变异测试执行器（真实底本 + 解释器）")
    ap.add_argument("--task", default="S10")
    ap.add_argument("--base", default=str(DEFAULT_BASE))
    ap.add_argument("--cases", default="")
    ap.add_argument("--io", default="")
    ap.add_argument("--extra", default="", help="补充用例 CSV（用于验证补用例后能杀死存活变异体）")
    ap.add_argument("--out", default=str(HERE.parent / "mutants"))
    a = ap.parse_args(argv)

    task = a.task.upper()
    cases_csv = a.cases or str(TESTS / "cases" / ("%s.csv" % task))
    io_json = a.io or str(TESTS / "cases" / "_fixtures" / ("%s.io.json" % task))
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    if a.extra:
        cases_csv = str(merge_cases(Path(cases_csv), Path(a.extra), out))
    base_path = Path(a.base)
    base_text = base_path.read_text(encoding="utf-8-sig")
    try:
        base_ref = base_path.resolve().relative_to(WORKSPACE).as_posix()
    except ValueError:
        base_ref = base_path.name
    _, cases = load_cases(cases_csv, io_json)

    summary = []
    # 先验证底本本身全通过：底本或补充用例有问题时，变异得分没有意义
    base_results = evaluate(base_text, task, cases)
    base_fail = [r for r in base_results if r["status"] != "pass"]
    if base_fail:
        print("底本未全部通过，变异测试不成立：", file=sys.stderr)
        for r in base_fail[:5]:
            print("  ", r["case_id"], r["status"], r.get("mismatch") or r.get("detail"),
                  file=sys.stderr)
        return 2
    print("底本自检：%d/%d 用例通过" % (len(base_results), len(cases)))
    for mut in MUTATIONS:
        text, results = run_one(base_text, task, cases, mut)
        d = out / mut["id"]
        d.mkdir(parents=True, exist_ok=True)
        (d / "final.st").write_text(text, encoding="utf-8")
        (d / "mutation.json").write_text(json.dumps({
            "mutant_id": mut["id"], "task_id": task, "operator": mut["operator"],
            "description": mut["desc"], "base_source": base_ref,
            "patches": [{"from": o, "to": n} for o, n in mut["patches"]],
            "expect_killer": mut["expect_killer"],
        }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        with open(d / "cases_result.jsonl", "w", encoding="utf-8") as fh:
            for r in results:
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")

        fails = [r for r in results if r["status"] == "fail"]
        errs = [r for r in results if r["status"] == "error"]
        if fails:
            status = "killed"
            killer = "%s@%s" % (fails[0]["case_id"], (fails[0]["mismatch"] or {}).get("cycle"))
        elif len(errs) == len(results):
            status, killer = "invalid", ""
        else:
            status, killer = "survived", ""
        (d / "result.json").write_text(json.dumps({
            "mutant_id": mut["id"], "status": status, "killed_by": killer,
            "passed": sum(1 for r in results if r["status"] == "pass"),
            "failed": len(fails), "error": len(errs), "total": len(results),
        }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        summary.append({
            "mutant_id": mut["id"], "task_id": task, "operator": mut["operator"],
            "description": mut["desc"], "status": status, "killed_by": killer,
            "passed": sum(1 for r in results if r["status"] == "pass"),
            "failed": len(fails), "error": len(errs), "total": len(results),
            "base_source": base_path.name,
        })
        print("%-9s %-12s %-8s killed_by=%-14s pass=%d fail=%d err=%d"
              % (mut["id"], mut["operator"], status, killer or "-",
                 summary[-1]["passed"], len(fails), len(errs)))

    with open(out / "summary.csv", "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(summary[0].keys()))
        w.writeheader()
        w.writerows(summary)

    killed = sum(1 for r in summary if r["status"] == "killed")
    valid = sum(1 for r in summary if r["status"] != "invalid")
    print("\n变异得分：%d/%d（有效变异体 %d 个）；明细 %s"
          % (killed, valid, valid, out))
    return 0


if __name__ == "__main__":
    sys.exit(main())

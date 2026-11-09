"""解释器入口：两种调用方式，命令行契约与成员2 的 `runner-cmd` 完全一致。

模式 1（喂给 ExecBackend / 单个用例）::

    python tests/runner/interp/run.py --source refimpl/P03.st \
        --inputs inputs.csv --outputs outputs.csv --case-id P03-01

    输入：`cycle` + 所有 IN 列（cycle=0 是初态行），由 `runner.backends.ExecBackend` 生成；
    输出：`case_id,cycle` + 所有 OUT 列（列名与 fixture 逐字一致）。

模式 2（变异测试一次性跑完整题）::

    python tests/runner/interp/run.py --source refimpl/P03.st \
        --cases tests/cases/P03.csv --io tests/cases/_fixtures/P03.io.json \
        --out-dir verify/mutants/M-P03-1/test/actual

退出码：0 正常；2 解释/类型/输入错误（调用方应判 error，不算模型失败）。
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
_TESTS = HERE.parents[2]                     # .../tests
if str(_TESTS) not in sys.path:
    sys.path.insert(0, str(_TESTS))

from runner.case_loader import CaseError, load_cases        # noqa: E402
from runner.interp.eval import InterpError, Interpreter      # noqa: E402
from runner.interp.parser import ParseError, parse            # noqa: E402
from runner.interp.st_types import StTypeError                   # noqa: E402


def _build(source, block=None, cycle_ms=20.0, task=None):
    """读源码 -> 解释器；`--task P03` 时优先挑 FB_P03，挑不到再用唯一块。"""
    p = Path(source)
    if not p.exists():
        raise InterpError("源文件不存在：%s" % p)
    try:
        prog = parse(p.read_text(encoding="utf-8-sig"))
    except ParseError as e:
        raise InterpError(str(e)) from e
    cand = block
    if cand is None and task:
        name = "FB_%s" % task.upper()
        if name in prog.blocks:
            cand = name
    return Interpreter(prog, block=cand, cycle_ms=cycle_ms)


def _records(itp, rows, case_id):
    """rows: [(cycle, {列: 原文或已解析值})]，cycle=0 只设初态、不出行。"""
    cols = itp.output_columns()
    out = []
    for cyc, mapping in rows:
        itp.set_inputs(mapping)
        if cyc == 0:
            continue
        itp.run_cycle()
        cells = itp.snapshot_text()
        row = {"case_id": case_id, "cycle": str(cyc)}
        row.update({c: cells[c] for c in cols})
        out.append(row)
    return cols, out


def _read_inputs_csv(path):
    with open(path, encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        header = reader.fieldnames or []
        if "cycle" not in header:
            raise InterpError("%s 缺 cycle 列" % path)
        rows = [(int(r["cycle"]), {k: v for k, v in r.items() if k and k != "cycle"})
                for r in reader]
    rows.sort(key=lambda x: x[0])
    if not rows or rows[0][0] != 0:
        raise InterpError("%s 缺 cycle=0 初态行（用例规范要求先给初态）" % path)
    nums = [c for c, _ in rows]
    if nums != list(range(len(nums))):
        raise InterpError("%s 的 cycle 不连续：%r" % (path, nums))
    return rows


def _write_csv(path, cols, records):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["case_id", "cycle"] + cols)
        w.writeheader()
        w.writerows(records)


def main(argv=None):
    ap = argparse.ArgumentParser(description="ST 子集解释器（成员4 兜底执行通道）")
    ap.add_argument("--source", required=True, help="被测 ST 源文件")
    ap.add_argument("--inputs", help="模式1：输入 CSV（cycle + IN 列）")
    ap.add_argument("--outputs", help="模式1：输出 CSV")
    ap.add_argument("--case-id", default="", help="模式1：写进 actual 的 case_id")
    ap.add_argument("--cases", help="模式2：用例 CSV（如 tests/cases/P03.csv）")
    ap.add_argument("--io", help="模式2：fixture（tests/cases/_fixtures/P03.io.json）")
    ap.add_argument("--out-dir", help="模式2：actual 输出目录")
    ap.add_argument("--task", help="题目号（优先挑 FB_<task> 块）")
    ap.add_argument("--block", help="显式指定 FB 块名")
    ap.add_argument("--cycle-ms", type=float, default=20.0, help="扫描周期，默认 20 ms")
    a = ap.parse_args(argv)

    try:
        if a.cases:
            if not a.io or not a.out_dir:
                print("--cases 需要同时给 --io 与 --out-dir", file=sys.stderr)
                return 2
            task_id, cases = load_cases(a.cases, a.io)
            out_dir = Path(a.out_dir)
            for case in cases:
                # 每条用例都从初态重来：换新解释器，避免状态串题
                itp = _build(a.source, a.block, a.cycle_ms, a.task)
                rows = [(c["cycle"], {k: v for k, v in c["in"].items()})
                        for c in case.cycles]
                cols, recs = _records(itp, rows, case.case_id)
                _write_csv(out_dir / ("%s.csv" % case.case_id), cols, recs)
            print("%s：%d 条用例 -> %s" % (task_id, len(cases), out_dir))
            return 0

        if not (a.inputs and a.outputs):
            print("模式1 需要 --inputs 与 --outputs；模式2 需要 --cases/--io/--out-dir",
                  file=sys.stderr)
            return 2
        itp = _build(a.source, a.block, a.cycle_ms, a.task)
        rows = _read_inputs_csv(a.inputs)
        cols, recs = _records(itp, rows, a.case_id)
        _write_csv(a.outputs, cols, recs)
        return 0

    except (InterpError, StTypeError, CaseError) as e:
        print("解释器错误：%s" % e, file=sys.stderr)
        return 2
    except Exception as e:                   # noqa: BLE001 - 兜底，别把错误吞成 0
        print("解释器内部错误：%s: %s" % (type(e).__name__, e), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())

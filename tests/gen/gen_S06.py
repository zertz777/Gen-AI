"""生成 S06（烘箱分段升温与超温降载）的用例。"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from _emit import Case, write_cases  # noqa: E402

TESTS = HERE.parent
FX = TESTS / "cases" / "_fixtures" / "S06.io.json"
OUT = TESTS / "cases" / "S06.csv"


def i_(pv, setp, seg=0, req=False):
    return {"TempPV": pv, "SetTemp": setp, "Segment": seg,
            "LoadReduceReq": req}


def o_(heat=False, fan=False, alarm=False, reduce=False, st=0):
    return {"HeatOn": heat, "FanOn": fan, "OverTempAlarm": alarm,
            "LoadReduce": reduce, "Status": st}


def case_01():
    """0 段目标 = SetTemp × 0.5，低于目标 -5 ℃ 加热。"""
    c = Case("S06-01", "K1;K2;K4;C10",
             "0 段目标 50 ℃：40 ℃ 加热，风机与加热联锁同时为 TRUE")
    c.add(i_(20.0, 100.0, 0), o_())                       # 0
    c.add(i_(40.0, 100.0, 0), o_(heat=True, fan=True))    # 1 低于 45
    c.add(i_(44.0, 100.0, 0), o_(heat=True, fan=True))    # 2
    return c


def case_02():
    """±5 ℃ 死区：区间内保持上一拍状态。"""
    c = Case("S06-02", "K2",
             "45—55 ℃ 死区内保持加热状态；超过 55 ℃ 才停")
    c.add(i_(20.0, 100.0, 0), o_())                       # 0
    c.add(i_(40.0, 100.0, 0), o_(heat=True, fan=True))    # 1 加热
    c.add(i_(50.0, 100.0, 0), o_(heat="X", fan="X"))      # 2 死区内，保持
    c.add(i_(50.0, 100.0, 0), o_(heat="X", fan="X"))      # 3 仍保持
    c.add(i_(56.0, 100.0, 0), o_())                       # 4 高于 55，停
    c.add(i_(50.0, 100.0, 0), o_())                       # 5 死区内，保持停
    return c


def case_03():
    """非法段号按 0 段处理并报 16#8601。"""
    c = Case("S06-03", "K1",
             "段号 5 非法：按 0 段目标（×0.5）执行，Status = 16#8601")
    c.add(i_(20.0, 100.0, 5), o_(st=0x8601))              # 0
    c.add(i_(40.0, 100.0, 5), o_(heat=True, fan=True, st=0x8601))  # 1
    c.add(i_(40.0, 100.0, 1), o_(heat=True, fan=True))    # 2 合法段 1（目标 80）
    return c


def case_04():
    """超温 +10 ℃ 置降载，回落 -3 ℃ 才撤销。"""
    c = Case("S06-04", "K3",
             "超目标 10 ℃ 报警并降载；回落到目标 -3 ℃ 以下才撤销")
    c.add(i_(20.0, 100.0, 0), o_())                                    # 0
    c.add(i_(65.0, 100.0, 0), o_(alarm=True, reduce=True, st=0x8602))  # 1 65 > 60
    c.add(i_(55.0, 100.0, 0), o_(alarm=True, reduce=True, st=0x8602))  # 2 仍高于 47
    c.add(i_(45.0, 100.0, 0), o_())                                    # 3 低于 47，撤销
    return c


def case_05():
    """上位机请求降载：降载优先切断加热。"""
    c = Case("S06-05", "K3;K4;C1",
             "LoadReduceReq = TRUE 时降载置位且加热必须断开（不报警）")
    c.add(i_(20.0, 100.0, 0), o_())                                    # 0
    c.add(i_(40.0, 100.0, 0, req=True), o_(reduce=True))               # 1 降载断加热
    c.add(i_(40.0, 100.0, 0), o_(heat=True, fan=True))                 # 2 撤销请求，恢复加热
    return c


def main():
    cases = [c.dict() for c in
             (case_01(), case_02(), case_03(), case_04(), case_05())]
    write_cases(OUT, FX, cases)
    print("S06: %d 条用例 / %d 行" % (len(cases), sum(len(c["rows"]) for c in cases)))


if __name__ == "__main__":
    main()

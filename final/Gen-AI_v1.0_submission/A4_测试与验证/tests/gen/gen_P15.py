"""生成 P15（物料配比控制）的用例。

手动模式按上升沿切换阀门/搅拌；自动模式按液位顺序推进；急停优先。
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from _emit import Case, write_cases  # noqa: E402

TESTS = HERE.parent
FX = TESTS / "cases" / "_fixtures" / "P15.io.json"
OUT = TESTS / "cases" / "P15.csv"


def i_(estop=True, ope=False, level=0, pm=False, complete=False,
       aStart=False, bStart=False, cStart=False, dStart=False,
       mStart=False, autoStart=False):
    return {"estop": estop, "opeMode": ope, "levelSensor": level,
            "processMode": pm, "mixMotorComplete": complete,
            "valveAStart": aStart, "valveBStart": bStart,
            "valveCStart": cStart, "valveDStart": dStart,
            "mixMotorStart": mStart, "autoStart": autoStart}


def o_(a=False, b=False, c=False, d=False, mix=False):
    return {"valveARun": a, "valveBRun": b, "valveCRun": c,
            "valveDRun": d, "mixMotorRun": mix}


def x_():
    return {k: "X" for k in ("valveARun", "valveBRun", "valveCRun",
                             "valveDRun", "mixMotorRun")}


def case_01():
    """手动模式：按钮上升沿切换，按住不放不重复翻转。"""
    c = Case("P15-01", "K2;C10",
             "手动模式按钮按上升沿切换：按一次开、按住不重复翻转、再按一次关")
    c.add(i_(), o_())                                        # 0 上电全停
    c.add(i_(aStart=True), o_(a=True))                       # 1 上升沿，开 A
    c.add(i_(aStart=True), o_(a=True))                       # 2 按住不放，保持
    c.add(i_(aStart=False), o_(a=True))                      # 3 松开，保持
    c.add(i_(aStart=True), o_(a=False))                      # 4 再按一次，关 A
    c.add(i_(aStart=False), o_(a=False))                     # 5
    c.add(i_(mStart=True), o_(mix=True))                     # 6 搅拌电机同样切换
    c.add(i_(mStart=False), o_(mix=True))                    # 7
    c.add(i_(mStart=True), o_(mix=False))                    # 8
    return c


def case_02():
    """急停优先，且恢复后不得从中断处续跑。"""
    c = Case("P15-02", "K1;K4;C1;C2",
             "急停当拍停全部设备；恢复后回到安全步，必须重新按 autoStart")
    c.add(i_(ope=True), o_())                                # 0
    c.add(i_(ope=True, autoStart=True), o_(a=True))          # 1 自动启动，开 A
    c.add(i_(ope=True, level=30), o_(a=True))                # 2 进料中
    c.add(i_(ope=False, level=30), o_())                     # 3 急停，全停
    c.add(i_(ope=False, level=30), o_())                     # 4 急停保持
    c.add(i_(ope=True, level=30), o_())                      # 5 恢复，不得续跑
    c.add(i_(ope=True, level=60), o_())                      # 6 液位已过 50，仍不得开 B
    c.add(i_(ope=True, level=60, autoStart=True), o_(a=True))  # 7 重新启动，从 A 开始
    return c


def case_03():
    """自动模式 processMode = FALSE：A→B→搅拌→D。"""
    c = Case("P15-03", "K3;C4;C6",
             "两段配比后直接搅拌：A 到 50 关、B 到 80 关，搅拌完成后开 D")
    c.add(i_(ope=True), o_())                                # 0
    c.add(i_(ope=True, autoStart=True), o_(a=True))          # 1 开 A
    c.add(i_(ope=True, level=30), o_(a=True))                # 2 A 进料
    c.add(i_(ope=True, level=55), o_(b=True))                # 3 关 A 开 B
    c.add(i_(ope=True, level=70), o_(b=True))                # 4 B 进料
    c.add(i_(ope=True, level=85), o_(mix=True))              # 5 关 B 开搅拌
    c.add(i_(ope=True, level=85), o_(mix=True))              # 6 搅拌中
    c.add(i_(ope=True, level=85, complete=True), o_(d=True))  # 7 搅拌完成，开 D
    c.add(i_(ope=True, level=85), o_(d=True))                # 8 D 出料
    return c


def case_04():
    """自动模式 processMode = TRUE：A→B→C→搅拌→D。"""
    c = Case("P15-04", "K3;C4;C6",
             "三段配比：C 到 100 才关并启动搅拌，搅拌完成后开 D")
    c.add(i_(ope=True, pm=True), o_())                       # 0
    c.add(i_(ope=True, pm=True, autoStart=True), o_(a=True))  # 1 开 A
    c.add(i_(ope=True, pm=True, level=55), o_(b=True))       # 2 关 A 开 B
    c.add(i_(ope=True, pm=True, level=85), o_(c=True))       # 3 关 B 开 C
    c.add(i_(ope=True, pm=True, level=95), o_(c=True))       # 4 C 进料
    c.add(i_(ope=True, pm=True, level=105), o_(mix=True))    # 5 关 C 开搅拌
    c.add(i_(ope=True, pm=True, level=105, complete=True), o_(d=True))  # 6 完成，开 D
    c.add(i_(ope=True, pm=True, level=105), o_(d=True))      # 7
    return c


def case_05():
    """手动模式五个设备独立切换，急停一次全清。"""
    c = Case("P15-05", "K1;K2;C1",
             "手动可同时开多个设备；急停当拍全部清零，恢复后保持全停")
    c.add(i_(), o_())                                        # 0
    c.add(i_(aStart=True), o_(a=True))                       # 1
    c.add(i_(bStart=True), o_(a=True, b=True))               # 2
    c.add(i_(cStart=True), o_(a=True, b=True, c=True))       # 3
    c.add(i_(dStart=True), o_(a=True, b=True, c=True, d=True))  # 4
    c.add(i_(mStart=True), o_(a=True, b=True, c=True, d=True, mix=True))  # 5
    c.add(i_(estop=False), o_())                             # 6 急停全停
    c.add(i_(), o_())                                        # 7 恢复后仍全停
    return c


def case_06():
    """液位阈值边界拍（恰好 50/80/100）需求未定义，写 X。"""
    c = Case("P15-06", "K3;C10",
             "液位恰好等于 50/80/100 的那一拍按 X 不判定，越过阈值后判定")
    c.add(i_(ope=True), o_())                                # 0
    c.add(i_(ope=True, autoStart=True), o_(a=True))          # 1
    c.add(i_(ope=True, level=50), x_())                      # 2 恰好 50，边界
    c.add(i_(ope=True, level=51), o_(b=True))                # 3 已过 50
    c.add(i_(ope=True, level=80), x_())                      # 4 恰好 80，边界
    c.add(i_(ope=True, level=81), o_(mix=True))              # 5 已过 80
    return c


def main():
    cases = [c.dict() for c in
             (case_01(), case_02(), case_03(), case_04(), case_05(), case_06())]
    write_cases(OUT, FX, cases)
    print("P15: %d 条用例 / %d 行 -> %s"
          % (len(cases), sum(len(c["rows"]) for c in cases), OUT))


if __name__ == "__main__":
    main()

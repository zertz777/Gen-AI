"""生成 S03（安全门分级停机）的用例。

B 区允许再走 500 ms = 25 拍；A 区当拍停。
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from _emit import Case, write_cases  # noqa: E402

TESTS = HERE.parent
FX = TESTS / "cases" / "_fixtures" / "S03.io.json"
OUT = TESTS / "cases" / "S03.csv"

DELAY_B = 25       # 500 ms


def i_(door=False, za=False, zb=False, reset=False, estop=True):
    return {"DoorSwitch": door, "ZoneAOccupied": za, "ZoneBOccupied": zb,
            "ResetBtn": reset, "EStop_NC": estop}


def o_(a=False, b=False, lamp=False, st=0):
    return {"DriveA_Run": a, "DriveB_Run": b, "AlarmLamp": lamp, "Status": st}


def case_01():
    """门打开：A 区当拍停，B 区继续。"""
    c = Case("S03-01", "K1;C1b",
             "DoorSwitch 变 TRUE 的同一拍 DriveA_Run 必须为 FALSE，B 区仍在运行")
    c.add(i_(), o_())                                       # 0 初态
    c.add(i_(), o_(a=True, b=True))                         # 1 正常运行
    c.add(i_(door=True), o_(b=True, lamp=True, st=0x8302))  # 2 门开，A 当拍停
    c.add(i_(door=True), o_(b=True, lamp=True, st=0x8302))  # 3
    return c


def case_02():
    """B 区 500 ms 延时停机。"""
    c = Case("S03-02", "K2;C5",
             "门开后 B 区最多再保持 500 ms（25 拍），到点必须停")
    c.add(i_(), o_())                                       # 0
    c.add(i_(), o_(a=True, b=True))                         # 1
    c.add(i_(door=True), o_(b=True, lamp=True, st=0x8302))  # 2 门开
    for _ in range(DELAY_B - 2):                            # 3..25 B 继续
        c.add(i_(door=True), o_(b=True, lamp=True, st=0x8302))
    c.add(i_(door=True), o_(b="X", lamp=True, st=0x8302))   # 26 满 25 拍边界
    c.add(i_(door=True), o_(lamp=True, st=0x8302))          # 27 B 已停
    c.add(i_(door=True), o_(lamp=True, st=0x8302))          # 28
    return c


def case_03():
    """门关闭后必须按复位才能重启。"""
    c = Case("S03-03", "K3;C6",
             "门关后不按复位不得重启；ResetBtn 上升沿确认后才恢复")
    c.add(i_(), o_())                                       # 0
    c.add(i_(), o_(a=True, b=True))                         # 1
    c.add(i_(door=True), o_(b=True, lamp=True, st=0x8302))  # 2
    c.add(i_(door=True), o_(lamp=True, st=0x8302))          # 3 B 停
    c.add(i_(), o_(lamp=True, st=0x8301))                   # 4 门关，待复位
    c.add(i_(), o_(lamp=True, st=0x8301))                   # 5 未复位
    c.add(i_(reset=True), o_(a="X", b="X", lamp="X", st="X"))  # 6 复位拍
    c.add(i_(), o_(a=True, b=True))                         # 7 恢复运行
    return c


def case_04():
    """急停优先于 500 ms 延时。"""
    c = Case("S03-04", "K4;C1",
             "EStop_NC = FALSE 时 A、B 两区当拍都停，Status = 16#8303")
    c.add(i_(), o_())                                       # 0
    c.add(i_(), o_(a=True, b=True))                         # 1
    c.add(i_(door=True), o_(b=True, lamp=True, st=0x8302))  # 2
    c.add(i_(door=True, estop=False), o_(lamp=True, st=0x8303))  # 3 急停
    c.add(i_(estop=False), o_(lamp=True, st=0x8303))        # 4
    return c


def main():
    cases = [c.dict() for c in
             (case_01(), case_02(), case_03(), case_04())]
    write_cases(OUT, FX, cases)
    print("S03: %d 条用例 / %d 行"
          % (len(cases), sum(len(c["rows"]) for c in cases)))


if __name__ == "__main__":
    main()

"""生成 S02（输送线正反转与检修锁）的用例。

200 ms 换向死区 = 10 拍；1 Hz 闪烁 = 500 ms 亮 / 500 ms 灭 = 25 拍。
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from _emit import Case, write_cases  # noqa: E402

TESTS = HERE.parent
FX = TESTS / "cases" / "_fixtures" / "S02.io.json"
OUT = TESTS / "cases" / "S02.csv"

DEAD = 10          # 200 ms
HALF = 25          # 1 Hz 的半周期 500 ms


def i_(fwd=False, rev=False, maint=False, estop=True):
    return {"FwdBtn": fwd, "RevBtn": rev, "MaintKey": maint, "EStop_NC": estop}


def o_(fwd=False, rev=False, lamp=False, st=0):
    return {"MotorFwd": fwd, "MotorRev": rev, "RunLamp": lamp, "Status": st}


def case_01():
    """正转按钮电平驱动，松开即停。"""
    c = Case("S02-01", "K1;C10",
             "按住正转按钮正转，松开当拍停止；反转输出始终 FALSE")
    c.add(i_(), o_())                                    # 0
    c.add(i_(fwd=True), o_(fwd=True))                    # 1
    c.add(i_(fwd=True), o_(fwd=True))                    # 2
    c.add(i_(), o_())                                    # 3
    return c


def case_02():
    """正转切反转：必须先停 200 ms 死区。"""
    c = Case("S02-02", "K2;C2",
             "正转切反转要等满 200 ms 死区；死区内 Status = 16#8203")
    c.add(i_(), o_())                                    # 0
    c.add(i_(fwd=True), o_(fwd=True))                    # 1 正转
    c.add(i_(rev=True), o_(st=0x8203))                   # 2 换向，死区开始
    for _ in range(DEAD - 2):                            # 3..10 死区内
        c.add(i_(rev=True), o_(st=0x8203))
    c.add(i_(rev=True), o_(rev="X", st="X"))             # 11 满 10 拍边界
    c.add(i_(rev=True), o_(rev=True))                    # 12 反转
    return c


def case_03():
    """检修钥匙：两个方向锁定，指示灯 1 Hz 闪烁。"""
    c = Case("S02-03", "K3",
             "MaintKey = TRUE 时两个方向恒 FALSE，RunLamp 以 1 Hz 闪烁")
    c.add(i_(), o_())                                    # 0
    c.add(i_(maint=True, fwd=True), o_(lamp=True, st=0x8201))   # 1 检修
    for _ in range(HALF - 1):                            # 2..25 亮
        c.add(i_(maint=True, fwd=True), o_(lamp=True, st=0x8201))
    for _ in range(HALF):                                # 26..50 灭
        c.add(i_(maint=True, fwd=True), o_(st=0x8201))
    for _ in range(HALF):                                # 51..75 亮
        c.add(i_(maint=True, fwd=True), o_(lamp=True, st=0x8201))
    return c


def case_04():
    """急停立即停机并清死区计时。"""
    c = Case("S02-04", "K4",
             "急停当拍两个方向停止、Status = 16#8202；解除后不得自行恢复")
    c.add(i_(), o_())                                    # 0
    c.add(i_(fwd=True), o_(fwd=True))                    # 1
    c.add(i_(fwd=True, estop=False), o_(st=0x8202))      # 2 急停
    c.add(i_(fwd=True), o_())                            # 3 解除，仍停
    return c


def case_05():
    """两个按钮同时按下：两个方向都不得输出。"""
    c = Case("S02-05", "K1",
             "正转与反转按钮同时有效时不得同时输出，两个方向都保持 FALSE")
    c.add(i_(), o_())                                    # 0
    c.add(i_(fwd=True, rev=True), o_())                  # 1
    c.add(i_(fwd=True, rev=True), o_())                  # 2
    return c


def main():
    cases = [c.dict() for c in
             (case_01(), case_02(), case_03(), case_04(), case_05())]
    write_cases(OUT, FX, cases)
    print("S02: %d 条用例 / %d 行" % (len(cases), sum(len(c["rows"]) for c in cases)))


if __name__ == "__main__":
    main()

"""生成 S01（双工位气动夹具互锁）的用例。"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from _emit import Case, write_cases  # noqa: E402

TESTS = HERE.parent
FX = TESTS / "cases" / "_fixtures" / "S01.io.json"
OUT = TESTS / "cases" / "S01.csv"


def i_(start=False, left=False, right=False, estop=True):
    return {"StartBtn": start, "LeftPartPresent": left,
            "RightPartPresent": right, "EStop_NC": estop}


def o_(cl=False, cr=False, busy=False, st=0):
    return {"ClampLeft": cl, "ClampRight": cr, "Busy": busy, "Status": st}


def case_01():
    """左侧夹紧：上升沿触发并保持，按住不放不重复动作。"""
    c = Case("S01-01", "K2;K3;C10",
             "左工位有件时按一次 StartBtn 夹紧并保持；按住不放不重复触发")
    c.add(i_(), o_())                                    # 0 初态
    c.add(i_(start=True, left=True), o_(cl=True, busy=True))   # 1 夹紧
    c.add(i_(start=True, left=True), o_(cl=True, busy=True))   # 2 按住
    c.add(i_(left=True), o_(cl=True, busy=True))               # 3 松开仍保持
    return c


def case_02():
    """右侧夹紧：与左侧对称。"""
    c = Case("S01-02", "K1;K2",
             "右工位有件时按 StartBtn 夹紧右侧，左侧保持 FALSE")
    c.add(i_(), o_())                                          # 0
    c.add(i_(start=True, right=True), o_(cr=True, busy=True))  # 1
    c.add(i_(right=True), o_(cr=True, busy=True))              # 2
    return c


def case_03():
    """没有零件时不得夹紧。"""
    c = Case("S01-03", "K2",
             "工位无零件时按 StartBtn 不得夹紧任何一侧")
    c.add(i_(), o_())                                          # 0
    c.add(i_(start=True), o_())                                # 1 无件
    c.add(i_(left=True), o_())                                 # 2 只有件没按钮
    c.add(i_(start=True, left=True), o_(cl=True, busy=True))   # 3 有件+按钮
    return c


def case_04():
    """急停立即松开并清忙标志。"""
    c = Case("S01-04", "K4;C10",
             "EStop_NC = FALSE 时两侧立即松开、Busy 清零、Status = 16#8102")
    c.add(i_(), o_())                                          # 0
    c.add(i_(start=True, left=True), o_(cl=True, busy=True))   # 1 夹紧
    c.add(i_(left=True, estop=False), o_(st=0x8102))           # 2 急停
    c.add(i_(left=True), o_())                                 # 3 解除后仍松开
    return c


def case_05():
    """两侧同时请求：报 16#8101，输出归属未定义。"""
    c = Case("S01-05", "K1;K2",
             "两侧都有件且同时按 StartBtn 时报 16#8101；哪侧夹紧需求未定义，写 X")
    c.add(i_(), o_())                                          # 0
    c.add(i_(start=True, left=True, right=True),
          o_(cl="X", cr="X", busy="X", st=0x8101))             # 1
    c.add(i_(left=True, right=True), o_(cl="X", cr="X", busy="X", st=0x8101))  # 2
    return c


def main():
    cases = [c.dict() for c in
             (case_01(), case_02(), case_03(), case_04(), case_05())]
    write_cases(OUT, FX, cases)
    print("S01: %d 条用例 / %d 行" % (len(cases), sum(len(c["rows"]) for c in cases)))


if __name__ == "__main__":
    main()

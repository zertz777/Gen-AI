"""生成 S05（泵站流量累计与班次清零）的用例。"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from _emit import Case, write_cases  # noqa: E402

TESTS = HERE.parent
FX = TESTS / "cases" / "_fixtures" / "S05.io.json"
OUT = TESTS / "cases" / "S05.csv"


def i_(pulse=False, reset=False, ct=20):
    return {"FlowPulse": pulse, "ShiftReset": reset, "CycleTime": ct}


def o_(total, shift, count, over=False, st=0):
    return {"TotalVolume": total, "ShiftVolume": shift,
            "PulseCount": count, "OverflowFlag": over, "Status": st}


def case_01():
    """每个上升沿累加 0.5 L。"""
    c = Case("S05-01", "K1;C2;C10",
             "三个脉冲累计 1.5 L，计数 3；电平保持不重复累加")
    c.add(i_(), o_(0.0, 0.0, 0))            # 0 初态
    c.add(i_(pulse=True), o_(0.5, 0.5, 1))  # 1
    c.add(i_(pulse=True), o_(0.5, 0.5, 1))  # 2 无新沿
    c.add(i_(), o_(0.5, 0.5, 1))            # 3
    c.add(i_(pulse=True), o_(1.0, 1.0, 2))  # 4
    c.add(i_(), o_(1.0, 1.0, 2))            # 5
    c.add(i_(pulse=True), o_(1.5, 1.5, 3))  # 6
    return c


def case_02():
    """班次清零：只清当班量，总量不减。"""
    c = Case("S05-02", "K2;C6",
             "ShiftReset 上升沿清当班流量与计数，TotalVolume 保持")
    c.add(i_(), o_(0.0, 0.0, 0))            # 0
    c.add(i_(pulse=True), o_(0.5, 0.5, 1))  # 1
    c.add(i_(), o_(0.5, 0.5, 1))            # 2
    c.add(i_(pulse=True), o_(1.0, 1.0, 2))  # 3
    c.add(i_(reset=True), o_(1.0, 0.0, 0))  # 4 班次清零
    c.add(i_(), o_(1.0, 0.0, 0))            # 5
    c.add(i_(pulse=True), o_(1.5, 0.5, 1))  # 6 重新累计
    return c


def case_03():
    """按住 ShiftReset 不重复清零。"""
    c = Case("S05-03", "K2",
             "ShiftReset 按住期间新脉冲照常累计，不重复清零")
    c.add(i_(), o_(0.0, 0.0, 0))                    # 0
    c.add(i_(reset=True), o_(0.0, 0.0, 0))          # 1
    c.add(i_(pulse=True, reset=True), o_(0.5, 0.5, 1))  # 2 按住，脉冲有效
    c.add(i_(pulse=True, reset=True), o_(0.5, 0.5, 1))  # 3
    return c


def case_04():
    """总量只增不减，ShiftVolume 不超过 TotalVolume。"""
    c = Case("S05-04", "K2;K3;C6",
             "总量只增不减（安全不变量）：连续计数与清零交替，TotalVolume 单调不减")
    c.add(i_(), o_(0.0, 0.0, 0))            # 0
    c.add(i_(pulse=True), o_(0.5, 0.5, 1))  # 1
    c.add(i_(), o_(0.5, 0.5, 1))            # 2
    c.add(i_(pulse=True), o_(1.0, 1.0, 2))  # 3
    c.add(i_(reset=True), o_(1.0, 0.0, 0))  # 4
    c.add(i_(), o_(1.0, 0.0, 0))            # 5
    c.add(i_(pulse=True), o_(1.5, 0.5, 1))  # 6
    c.add(i_(reset=True), o_(1.5, 0.0, 0))  # 7
    return c


def case_05():
    """K4：单周期内两次以上脉冲无法用单路 BOOL 输入表达，按 X 记录。"""
    c = Case("S05-05", "K4",
             "脉冲过快（单周期两次上升沿）需要输入层支持，本 CSV 只能记录不可判定")
    c.add(i_(), o_(0.0, 0.0, 0))                              # 0
    c.add(i_(pulse=True), o_(0.5, 0.5, 1))                    # 1
    c.add(i_(pulse=True), o_("X", "X", "X", "X", "X"))        # 2 频闪过快，无法表达
    c.add(i_(pulse=True), o_("X", "X", "X", "X", "X"))        # 3
    return c


def main():
    cases = [c.dict() for c in
             (case_01(), case_02(), case_03(), case_04(), case_05())]
    write_cases(OUT, FX, cases)
    print("S05: %d 条用例 / %d 行"
          % (len(cases), sum(len(c["rows"]) for c in cases)))


if __name__ == "__main__":
    main()

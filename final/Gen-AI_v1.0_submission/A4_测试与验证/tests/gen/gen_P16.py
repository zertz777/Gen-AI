"""生成 P16（柔性加工线）的用例。

工艺序列决定每个工位与输送方向；左右互斥，换向有 200 ms 死区。
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from _emit import Case, write_cases  # noqa: E402

TESTS = HERE.parent
FX = TESTS / "cases" / "_fixtures" / "P16.io.json"
OUT = TESTS / "cases" / "P16.csv"


def i_(length, seq, s1=False, s2=False, s3=False, s4=False, s5=False,
       start=False, c2=False, c3=False, c4=False):
    return {"processLength": length, "processSequence": seq,
            "sensor1": s1, "sensor2": s2, "sensor3": s3,
            "sensor4": s4, "sensor5": s5, "station1Start": start,
            "station2Complete": c2, "station3Complete": c3,
            "station4Complete": c4}


def o_(left=False, right=False):
    return {"conveyorLeft": left, "conveyorRight": right}


def case_01():
    """全正向序列 1→2→3→4→5。"""
    c = Case("P16-01", "K1;K2;C4;C10",
             "按序列 2→3→4→5 逐站输送，全部为右行，到位即停")
    c.add(i_(4, [2, 3, 4, 5], s1=True), o_())                    # 0 初态
    c.add(i_(4, [2, 3, 4, 5], s1=True, start=True), o_(right=True))   # 1 1→2
    c.add(i_(4, [2, 3, 4, 5]), o_(right=True))                   # 2 输送中
    c.add(i_(4, [2, 3, 4, 5], s2=True), o_())                    # 3 到位停
    c.add(i_(4, [2, 3, 4, 5], s2=True, c2=True), o_(right=True)) # 4 2→3
    c.add(i_(4, [2, 3, 4, 5], s3=True), o_())                    # 5 到位停
    c.add(i_(4, [2, 3, 4, 5], s3=True, c3=True), o_(right=True)) # 6 3→4
    c.add(i_(4, [2, 3, 4, 5], s4=True), o_())                    # 7 到位停
    c.add(i_(4, [2, 3, 4, 5], s4=True, c4=True), o_(right=True)) # 8 4→5
    c.add(i_(4, [2, 3, 4, 5], s5=True), o_())                    # 9 到达成品站
    c.add(i_(4, [2, 3, 4, 5], s5=True), o_())                    # 10 不得再动
    return c


def case_02():
    """序列 4→2→5：右、左、右，换向必须满足 200 ms 死区。"""
    c = Case("P16-02", "K1;K2;C4;C9",
             "序列含回头路：4→2 左行，停下后至少 10 拍才允许右行去 5")
    c.add(i_(3, [4, 2, 5], s1=True), o_())                       # 0
    c.add(i_(3, [4, 2, 5], s1=True, start=True), o_(right=True))  # 1 1→4 右行
    c.add(i_(3, [4, 2, 5], s4=True), o_())                       # 2 到 4
    c.add(i_(3, [4, 2, 5], s4=True, c4=True), o_(left=True))     # 3 4→2 左行
    for _ in range(9):                                            # 4..12 左行中
        c.add(i_(3, [4, 2, 5]), o_(left=True))
    c.add(i_(3, [4, 2, 5], s2=True), o_())                       # 13 到 2，左行停
    for _ in range(10):                                           # 14..23 死区内
        c.add(i_(3, [4, 2, 5], s2=True), o_())
    c.add(i_(3, [4, 2, 5], s2=True, c2=True), o_(right=True))    # 24 2→5 右行
    c.add(i_(3, [4, 2, 5], s5=True), o_())                       # 25 到达
    return c


def case_03():
    """processLength = 0：空工艺不得启动输送。"""
    c = Case("P16-03", "K4;C1",
             "工艺长度为 0 时即使有料有启动按钮也不得输送")
    c.add(i_(0, [2, 3, 4, 5], s1=True), o_())                    # 0
    c.add(i_(0, [2, 3, 4, 5], s1=True, start=True), o_())        # 1 不启动
    c.add(i_(0, [2, 3, 4, 5], s1=True, start=True), o_())        # 2 仍不启动
    return c


def case_04():
    """K3：到位但未按加工完成，不得推进。"""
    c = Case("P16-04", "K3;C4",
             "目标工位到位但加工完成信号未到，输送保持停止")
    c.add(i_(3, [2, 3, 5], s1=True), o_())                       # 0
    c.add(i_(3, [2, 3, 5], s1=True, start=True), o_(right=True))  # 1 1→2
    c.add(i_(3, [2, 3, 5], s2=True), o_())                       # 2 到 2
    for _ in range(4):                                            # 3..6 等完成信号
        c.add(i_(3, [2, 3, 5], s2=True), o_())
    c.add(i_(3, [2, 3, 5], s2=True, c2=True), o_(right=True))    # 7 2→3
    c.add(i_(3, [2, 3, 5], s3=True), o_())                       # 8 到 3
    return c


def case_05():
    """processLength 超出 1..8：不得输送。"""
    c = Case("P16-05", "K4",
             "工艺长度 9 超出数组范围，任何输入都不得启动输送")
    c.add(i_(9, [2, 3, 4, 5, 2, 3, 4, 5], s1=True), o_())        # 0
    c.add(i_(9, [2, 3, 4, 5, 2, 3, 4, 5], s1=True, start=True), o_())  # 1
    c.add(i_(9, [2, 3, 4, 5, 2, 3, 4, 5], s2=True), o_())        # 2
    return c


def case_06():
    """序列里有非法工位号 6：不得输送。"""
    c = Case("P16-06", "K4",
             "工艺序列出现 1—5 以外的工位号，不得启动输送")
    c.add(i_(3, [2, 6, 5], s1=True), o_())                       # 0
    c.add(i_(3, [2, 6, 5], s1=True, start=True), o_())           # 1
    c.add(i_(3, [2, 6, 5], s1=True, start=True), o_())           # 2
    return c


def main():
    cases = [c.dict() for c in
             (case_01(), case_02(), case_03(), case_04(), case_05(), case_06())]
    write_cases(OUT, FX, cases)
    print("P16: %d 条用例 / %d 行 -> %s"
          % (len(cases), sum(len(c["rows"]) for c in cases), OUT))


if __name__ == "__main__":
    main()

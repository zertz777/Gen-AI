"""生成 P05（焊缝间隙报警 + 上电 5 s 抑制）的用例。

5 s ÷ 20 ms = 250 拍，手写不现实，所以整题由脚本铺满。
未定义的边界拍（抑制结束那一拍、去抖恰好凑满那一拍）写 X，其余全判定。
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from _emit import Case, write_cases  # noqa: E402

TESTS = HERE.parent
FX = TESTS / "cases" / "_fixtures" / "P05.io.json"
OUT = TESTS / "cases" / "P05.csv"

DEB = 100          # DebounceTime = T#100ms = 5 拍


def io(gap, estop, soft, alert):
    return ({"Gap_Exceeded": gap, "Weld_E_Stop_NC": estop, "DebounceTime": DEB},
            {"Operator_Alert": alert, "Weld_Soft_Start_Active": soft})


def case_01():
    """抑制期内间隙就超限，抑制结束不得立即报警。"""
    c = Case("P05-01", "K1;K2;C10",
             "上电 5 s 抑制期内不报警；抑制期内的超限信号不得累计去抖")
    c.add(*io(False, True, True, False))            # 0
    c.span(249, *io(True, True, True, False))       # 1..249
    c.add(*io(True, True, "X", "X"))                # 250 抑制结束边界
    c.add(*io(True, True, False, False))            # 251 恢复监视，关键：仍不报警
    c.span(3, *io(True, True, False, False))        # 252..254 去抖 20/40/60
    c.add(*io(True, True, False, "X"))              # 255 去抖凑满边界
    c.add(*io(True, True, False, True))             # 256 报警
    return c


def case_02():
    """抑制结束后正常去抖；间隙恢复立即撤警。"""
    c = Case("P05-02", "K2;K3;C6",
             "抑制结束后连续超限满 DebounceTime 才报警，间隙恢复当拍撤警")
    c.add(*io(False, True, True, False))            # 0
    c.span(249, *io(False, True, True, False))      # 1..249
    c.add(*io(False, True, "X", "X"))               # 250
    c.add(*io(False, True, False, False))           # 251
    c.span(4, *io(True, True, False, False))        # 252..255 去抖 20/40/60/80
    c.add(*io(True, True, False, "X"))              # 256 边界
    c.add(*io(True, True, False, True))             # 257 报警
    c.add(*io(False, True, False, False))           # 258 恢复，立即撤警
    c.add(*io(True, True, False, False))            # 259 重新计，不得立刻再报
    return c


def case_03():
    """急停优先于抑制期。"""
    c = Case("P05-03", "K4;C1;C2",
             "急停优先于抑制期与监视：当拍清报警，抑制期内急停不得报警")
    c.add(*io(True, True, True, False))             # 0
    c.span(99, *io(True, True, True, False))        # 1..99
    c.add(*io(True, False, "X", False))             # 100 急停动作
    c.add(*io(True, False, "X", False))             # 101 急停保持
    c.add(*io(True, True, True, False))             # 102 急停复位，回到抑制期
    c.span(3, *io(True, True, True, False))         # 103..105
    return c


def case_04():
    """急停必须清掉未完成的去抖计时。"""
    c = Case("P05-04", "K4;C1",
             "急停清去抖计时：复位后间隙仍超限也不得瞬间报警")
    c.add(*io(False, True, True, False))            # 0
    c.span(249, *io(False, True, True, False))      # 1..249
    c.add(*io(False, True, "X", "X"))               # 250
    c.add(*io(False, True, False, False))           # 251
    c.span(4, *io(True, True, False, False))        # 252..255 去抖 20/40/60/80
    c.add(*io(True, False, False, False))           # 256 急停，清计时
    c.add(*io(True, True, False, False))            # 257 关键：不得立即报警
    c.span(3, *io(True, True, False, False))        # 258..260 重新计 40/60/80
    c.add(*io(True, True, False, "X"))              # 261 凑满边界
    c.add(*io(True, True, False, True))             # 262 报警
    return c


def main():
    cases = [c.dict() for c in (case_01(), case_02(), case_03(), case_04())]
    write_cases(OUT, FX, cases)
    print("P05: %d 条用例 / %d 行 -> %s"
          % (len(cases), sum(len(c["rows"]) for c in cases), OUT))


if __name__ == "__main__":
    main()

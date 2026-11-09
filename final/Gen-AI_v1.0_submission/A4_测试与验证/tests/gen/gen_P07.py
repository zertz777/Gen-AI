"""生成 P07（多泵切换控制）的用例。

手动：按 selection 启停；自动：按 priority 取前 3 台（三用两备），
优先级相同按泵号升序。
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from _emit import Case, write_cases  # noqa: E402

TESTS = HERE.parent
FX = TESTS / "cases" / "_fixtures" / "P07.io.json"
OUT = TESTS / "cases" / "P07.csv"

F5 = [False] * 5
PRI = [1, 2, 3, 4, 5]


def i_(mode=False, start=False, stop=False, pri=None, sel=None):
    return {"mode": mode, "start": start, "stop": stop,
            "pumpGroup[].priority": list(pri or PRI),
            "pumpGroup[].selection": list(sel or F5)}


def o_(run=None):
    return {"pumpGroup[].RunComd": list(run or F5)}


def case_01():
    """手动启停 → 切自动 → 三用两备 → 停止优先。"""
    c = Case("P07-01", "K1;K2;K3;C10",
             "手动启停、切自动、三用两备", category="正常")
    c.add(i_(), o_())                                            # 0 初态
    c.add(i_(sel=[True, False, True, False, False]), o_())       # 1 选中泵 1、3
    c.add(i_(start=True, sel=[True, False, True, False, False]),
          o_([True, False, True, False, False]))                 # 2 启动
    c.add(i_(sel=[True, False, True, False, False]),
          o_([True, False, True, False, False]))                 # 3 松开保持
    c.add(i_(stop=True, sel=[True, False, True, False, False]), o_())  # 4 停止
    c.add(i_(mode=True, pri=[1, 5, 3, 2, 4]), o_())              # 5 切自动
    c.add(i_(mode=True, start=True, pri=[1, 5, 3, 2, 4]),
          o_([False, True, True, False, True]))                  # 6 取最高三台
    c.add(i_(mode=True, stop=True, pri=[1, 5, 3, 2, 4]), o_())   # 7 停止优先
    return c


def case_02():
    """手动模式没选任何泵，按启动不得运行。"""
    c = Case("P07-02", "K1;K2",
             "手动模式未选中任何泵时，按启动不运行任何泵", category="正常")
    c.add(i_(), o_())                                            # 0
    c.add(i_(start=True), o_())                                  # 1 无选中
    c.add(i_(), o_())                                            # 2
    c.add(i_(start=True, sel=[False, False, False, True, False]),
          o_([False, False, False, True, False]))                # 3 选泵 4 后启动
    c.add(i_(sel=[False, False, False, True, False]),
          o_([False, False, False, True, False]))                # 4 保持
    return c


def case_03():
    """优先级全部相同时按泵号升序取前三台。"""
    c = Case("P07-03", "K3;C6",
             "优先级全部相同（边界）：按泵号升序取 1、2、3", category="边界")
    c.add(i_(mode=True, pri=[5, 5, 5, 5, 5]), o_())              # 0
    c.add(i_(mode=True, start=True, pri=[5, 5, 5, 5, 5]),
          o_([True, True, True, False, False]))                  # 1
    c.add(i_(mode=True, pri=[5, 5, 5, 5, 5]),
          o_([True, True, True, False, False]))                  # 2 保持
    c.add(i_(mode=True, stop=True, pri=[5, 5, 5, 5, 5]), o_())   # 3 停止
    return c


def case_04():
    """停止优先，且停止后不得自行重启。"""
    c = Case("P07-04", "K4;C1;C4",
             "停止优先：start 与 stop 同时有效时全部停止，之后不得自行重启",
             category="安全")
    c.add(i_(), o_())                                            # 0
    c.add(i_(start=True, sel=[True, False, False, False, False]),
          o_([True, False, False, False, False]))                # 1 启动泵 1
    c.add(i_(start=True, stop=True, sel=[True, False, False, False, False]),
          o_())                                                  # 2 两键同按，停止优先
    c.add(i_(sel=[True, False, False, False, False]), o_())      # 3 不得自行重启
    c.add(i_(start=True, sel=[True, False, False, False, False]),
          o_([True, False, False, False, False]))                # 4 重新按启动
    return c


def case_05():
    """手动模式改变选中对象：运行中的泵保持，停止后按新选中启动。"""
    c = Case("P07-05", "K1;C6",
             "手动模式改变选中对象时运行状态保持，重新启动按新选中执行")
    c.add(i_(), o_())                                            # 0
    c.add(i_(start=True, sel=[True, False, False, False, False]),
          o_([True, False, False, False, False]))                # 1 泵 1
    c.add(i_(sel=[False, True, False, False, False]),
          o_([True, False, False, False, False]))                # 2 改选泵 2，运行保持
    c.add(i_(stop=True, sel=[False, True, False, False, False]), o_())  # 3 停止
    c.add(i_(start=True, sel=[False, True, False, False, False]),
          o_([False, True, False, False, False]))                # 4 按新选中启动
    return c


def case_06():
    """三用两备的数量边界：五台全选也只跑三台。"""
    c = Case("P07-06", "K2;K3",
             "三用两备的数量边界：五台全选中也恰好只跑优先级最高的 3 台",
             category="边界")
    c.add(i_(mode=True, sel=[True] * 5, pri=[2, 4, 1, 5, 3]), o_())  # 0
    c.add(i_(mode=True, start=True, sel=[True] * 5, pri=[2, 4, 1, 5, 3]),
          o_([False, True, False, True, True]))                  # 1 泵 4/2/5
    c.add(i_(mode=True, sel=[True] * 5, pri=[2, 4, 1, 5, 3]),
          o_([False, True, False, True, True]))                  # 2 保持
    return c


def main():
    cases = [c.dict() for c in
             (case_01(), case_02(), case_03(), case_04(),
              case_05(), case_06())]
    write_cases(OUT, FX, cases)
    print("P07: %d 条用例 / %d 行"
          % (len(cases), sum(len(c["rows"]) for c in cases)))


if __name__ == "__main__":
    main()

"""生成 S14（液压站压力分级加载与卸荷）的用例。

K2 允许低压泵延迟一拍投用、K4 允许 200 ms 内报警，所以触发拍写 X。
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from _emit import Case, write_cases  # noqa: E402

TESTS = HERE.parent
FX = TESTS / "cases" / "_fixtures" / "S14.io.json"
OUT = TESTS / "cases" / "S14.csv"


def i_(p, enable=True, reset=False):
    return {"Pressure": p, "PumpEnable": enable, "ResetBtn": reset}


def o_(low=False, high=False, relief=False, alarm=False, st=0):
    return {"LowPump": low, "HighPump": high, "ReliefValve": relief,
            "AlarmLamp": alarm, "Status": st}


def case_01():
    """低压加载：压力低于 120 bar 投低压泵（允许延迟一拍）。"""
    c = Case("S14-01", "K2;C10",
             "压力 100 bar 且允许加载时投低压泵；未允许时不得加载")
    c.add(i_(100.0, enable=False), o_())                    # 0
    c.add(i_(100.0), o_(low="X"))                           # 1 允许加载，边界拍
    c.add(i_(110.0), o_(low=True))                          # 2 投低压泵
    c.add(i_(130.0), o_())                                  # 3 高于 120，退出
    return c


def case_02():
    """高压加载：压力达到 140 bar 投高压泵。"""
    c = Case("S14-02", "K3",
             "压力 145 bar 投高压泵，低压泵退出")
    c.add(i_(0.0), o_())                                    # 0
    c.add(i_(145.0), o_(high=True))                         # 1
    c.add(i_(150.0), o_(high=True))                         # 2
    return c


def case_03():
    """高压泵 40 bar 滞回：100—140 之间保持。"""
    c = Case("S14-03", "K3",
             "高压泵投入后，压力 110 bar 仍保持；低于 100 bar 才断开并回投低压泵")
    c.add(i_(0.0), o_())                                    # 0
    c.add(i_(145.0), o_(high=True))                         # 1 投高压
    c.add(i_(110.0), o_(high=True))                         # 2 滞回区，保持
    c.add(i_(99.0), o_(low="X"))                            # 3 低于 100，切换拍
    c.add(i_(99.0), o_(low=True))                           # 4 低压泵投用
    return c


def case_04():
    """卸荷：超过 160 bar 当拍开卸荷阀并停泵，低于 150 bar 关闭。"""
    c = Case("S14-04", "K1;K5",
             "压力 170 bar 当拍卸荷且两泵 FALSE；155 bar 保持；145 bar 关闭")
    c.add(i_(0.0), o_())                                    # 0
    c.add(i_(170.0), o_(relief=True))                       # 1 卸荷
    c.add(i_(155.0), o_(relief=True))                       # 2 滞回区，保持
    c.add(i_(145.0), o_(high=True))                         # 3 关闭卸荷
    return c


def case_05():
    """传感器越界：200 ms 内停泵报警，故障消失后需复位。"""
    c = Case("S14-05", "K4",
             "压力 300 bar 判传感器故障；恢复后待复位（16#8D02），复位后恢复加载")
    c.add(i_(100.0), o_(low="X"))                           # 0
    c.add(i_(300.0), o_(alarm="X", st="X"))                 # 1 越界，允许 200 ms 响应
    c.add(i_(300.0), o_(alarm=True, st=0x8D01))             # 2 已报警
    c.add(i_(100.0), o_(alarm=True, st=0x8D02))             # 3 待复位
    c.add(i_(100.0, reset=True), o_(low="X"))               # 4 复位拍
    c.add(i_(100.0), o_(low=True))                          # 5 恢复加载
    return c


def main():
    cases = [c.dict() for c in
             (case_01(), case_02(), case_03(), case_04(), case_05())]
    write_cases(OUT, FX, cases)
    print("S14: %d 条用例 / %d 行"
          % (len(cases), sum(len(c["rows"]) for c in cases)))


if __name__ == "__main__":
    main()

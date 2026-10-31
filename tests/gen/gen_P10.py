"""生成 P10（温度逻辑控制）的用例。

5 s 连续加热 = 250 拍，3 s 保护保持 = 150 拍，手写不现实。
边界拍（"超过 5 s"那一拍、3 s 刚到那一拍）写 X，其余逐拍判定。
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from _emit import Case, write_cases  # noqa: E402

TESTS = HERE.parent
FX = TESTS / "cases" / "_fixtures" / "P10.io.json"
OUT = TESTS / "cases" / "P10.csv"

HEAT_5S = 250      # 5 s ÷ 20 ms
HOLD_3S = 150      # 3 s ÷ 20 ms


def io(t, s, heat, prot=False):
    """显示量按输入直通；HeaterStatus 与 HeaterOutput 同值（见 A-28）。"""
    return ({"TemperatureSensorInput": t, "SetTemperature": s},
            {"CurrentTemperature": t, "SetTempDisplay": s,
             "HeaterStatus": heat, "OverheatProtection": prot,
             "HeaterOutput": heat})


def xio(t, s):
    """边界拍：显示量仍确定，三个状态/控制量不判定。"""
    return ({"TemperatureSensorInput": t, "SetTemperature": s},
            {"CurrentTemperature": t, "SetTempDisplay": s,
             "HeaterStatus": "X", "OverheatProtection": "X",
             "HeaterOutput": "X"})


def to(c, n, ins, outs):
    """把用例铺到第 n 拍之前（即下一拍编号为 n）。"""
    while len(c.rows) < n:
        c.add(ins, outs)
    return c


def case_01():
    """基本温控：低于设定加热、高于设定停止。"""
    c = Case("P10-01", "K1;C10",
             "低于设定值加热、高于设定值停止；显示量跟随输入")
    c.add(*io(20.0, 30.0, False))            # 0 上电首拍不加热
    c.add(*io(20.0, 30.0, True))             # 1 低于设定，加热
    c.add(*io(25.0, 30.0, True))             # 2 仍低于设定，保持加热
    c.add(*io(30.5, 30.0, False))            # 3 高于设定，停止
    c.add(*io(29.0, 30.0, True))             # 4 回落到设定以下，重新加热
    c.add(*io(31.0, 30.0, False))            # 5 再次高于设定
    return c


def case_02():
    """连续加热满 5 s 触发过热保护。"""
    c = Case("P10-02", "K2;C1;C2",
             "连续加热满 5 s 触发过热保护并强制停加热")
    c.add(*io(20.0, 30.0, False))                       # 0
    to(c, HEAT_5S, *io(20.0, 30.0, True))               # 1..249 加热 249 拍
    c.add(*xio(20.0, 30.0))                             # 250 累计正好 5 s，边界
    c.add(*xio(20.0, 30.0))                             # 251 "超过 5 s"边界
    c.span(8, *io(20.0, 30.0, False, True))             # 252..259 保护动作，停加热
    return c


def case_03():
    """过热保护必须保持 3 s，期间温度仍低于设定也不得重新加热。"""
    c = Case("P10-03", "K3;C9",
             "过热保护触发后至少保持 3 s，期间温度低于设定也不得加热")
    c.add(*io(20.0, 30.0, False))                       # 0
    to(c, HEAT_5S, *io(20.0, 30.0, True))               # 1..249
    c.add(*xio(20.0, 30.0))                             # 250
    c.add(*xio(20.0, 30.0))                             # 251
    to(c, HEAT_5S + HOLD_3S + 2, *io(20.0, 30.0, False, True))  # 252..401 保护保持满 150 拍
    c.add(*xio(20.0, 30.0))                             # 402 满 3 s 边界
    c.add(*io(20.0, 30.0, True, False))                 # 403 解除，温度仍低，恢复加热
    c.span(5, *io(20.0, 30.0, True, False))             # 404..408
    return c


def case_04():
    """传感器越界判故障，当拍停加热，且不得误触发过热保护。"""
    c = Case("P10-04", "K4;C7;C7b",
             "传感器 <0 或 >100 判故障并停加热，故障解除后恢复温控")
    c.add(*io(20.0, 30.0, False))            # 0
    c.add(*io(20.0, 30.0, True))             # 1 正常加热
    c.add(*io(-5.0, 30.0, False))            # 2 低于 0，故障停加热
    c.add(*io(-0.5, 30.0, False))            # 3 仍为故障
    c.add(*io(150.0, 30.0, False))           # 4 高于 100，故障停加热
    c.add(*io(100.5, 30.0, False))           # 5 仍为故障
    c.add(*io(20.0, 30.0, True))             # 6 恢复正常，重新加热
    c.add(*io(20.0, 30.0, True))             # 7
    return c


def main():
    cases = [c.dict() for c in (case_01(), case_02(), case_03(), case_04())]
    write_cases(OUT, FX, cases)
    print("P10: %d 条用例 / %d 行 -> %s"
          % (len(cases), sum(len(c["rows"]) for c in cases), OUT))


if __name__ == "__main__":
    main()

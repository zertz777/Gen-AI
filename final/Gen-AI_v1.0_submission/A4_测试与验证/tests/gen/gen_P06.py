"""生成 P06（曝气风机延时启动）的用例。

5 s ÷ 20 ms = 250 拍，整题由脚本铺满。
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from _emit import Case, write_cases  # noqa: E402

TESTS = HERE.parent
FX = TESTS / "cases" / "_fixtures" / "P06.io.json"
OUT = TESTS / "cases" / "P06.csv"


def io(dolow, estop, run, cnt):
    return ({"DO_LOW": dolow, "AERATION_E_STOP_NC": estop},
            {"BLOWER_RUN": run, "AERATION_BLOWER_CYCLE_COUNT": cnt})


def case_01():
    """正常 5 s 延时启动，运行期间不重复计数。"""
    c = Case("P06-01", "K1;K2;K4;C10",
             "两条件持续 5 s 才启动；连续运行期间计数不重复累加")
    c.add(*io(False, True, False, 0))               # 0
    c.span(249, *io(True, True, False, 0))          # 1..249
    c.add(*io(True, True, "X", "X"))                # 250 计满 5 s 边界
    c.add(*io(True, True, True, 1))                 # 251 启动，计数 1
    c.span(9, *io(True, True, True, 1))             # 252..260 运行中不重复计数
    return c


def case_02():
    """DO_LOW 中途掉，计时复位后必须重新计满 5 s。"""
    c = Case("P06-02", "K3;C3",
             "DO_LOW 消失当拍停机并复位计时，新需求须重新计满 5 s")
    c.add(*io(False, True, False, 0))               # 0
    c.span(100, *io(True, True, False, 0))          # 1..100
    c.add(*io(False, True, False, 0))               # 101 复位
    c.span(249, *io(True, True, False, 0))          # 102..350 重新计
    c.add(*io(True, True, "X", "X"))                # 351 边界
    c.add(*io(True, True, True, 1))                 # 352 启动
    return c


def case_03():
    """急停打断，计时同样复位。"""
    c = Case("P06-03", "K1;K3;C1",
             "急停当拍停机并复位计时，急停解除后须重新计满 5 s")
    c.add(*io(False, True, False, 0))               # 0
    c.span(9, *io(True, True, False, 0))            # 1..9
    c.add(*io(True, False, False, 0))               # 10 急停
    c.span(249, *io(True, True, False, 0))          # 11..259 重新计
    c.add(*io(True, True, "X", "X"))                # 260 边界
    c.add(*io(True, True, True, 1))                 # 261 启动
    return c


def case_04():
    """两次启动，计数为 2。"""
    c = Case("P06-04", "K4;C2",
             "计数只在 BLOWER_RUN 的 FALSE→TRUE 沿加 1，第二次启动计到 2")
    c.add(*io(False, True, False, 0))               # 0
    c.span(249, *io(True, True, False, 0))          # 1..249
    c.add(*io(True, True, "X", "X"))                # 250
    c.add(*io(True, True, True, 1))                 # 251 第一次启动
    c.add(*io(False, True, False, 1))               # 252 停机，计数保持 1
    c.span(249, *io(True, True, False, 1))          # 253..501 重新计
    c.add(*io(True, True, "X", "X"))                # 502
    c.add(*io(True, True, True, 2))                 # 503 第二次启动
    return c


def case_05():
    """安全类：条件抖动两次不得「凑够」5 s。"""
    c = Case("P06-05", "K2;K3;C6",
             "DO_LOW 抖动两次各复位一次，累计时长不得凑成 5 s 而提前启动")
    c.add(*io(False, True, False, 0))               # 0
    c.span(100, *io(True, True, False, 0))          # 1..100
    c.add(*io(False, True, False, 0))               # 101 第一次复位
    c.span(99, *io(True, True, False, 0))           # 102..200
    c.add(*io(False, True, False, 0))               # 201 第二次复位，仍不得启动
    c.span(249, *io(True, True, False, 0))          # 202..450 重新计满
    c.add(*io(True, True, "X", "X"))                # 451 边界
    c.add(*io(True, True, True, 1))                 # 452 启动
    return c


def main():
    cases = [c.dict() for c in
             (case_01(), case_02(), case_03(), case_04(), case_05())]
    write_cases(OUT, FX, cases)
    print("P06: %d 条用例 / %d 行 -> %s"
          % (len(cases), sum(len(c["rows"]) for c in cases), OUT))


if __name__ == "__main__":
    main()

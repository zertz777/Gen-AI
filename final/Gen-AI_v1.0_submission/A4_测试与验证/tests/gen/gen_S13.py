"""生成 S13（双段输送合流同步与堵料防撞）的用例。

堵料 2 s = 100 拍；有料 3 s = 150 拍切高速；无料 5 s = 250 拍回落。
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from _emit import Case, write_cases  # noqa: E402

TESTS = HERE.parent
FX = TESTS / "cases" / "_fixtures" / "S13.io.json"
OUT = TESTS / "cases" / "S13.csv"

JAM = 100
HIGH = 150
LOW = 250


def i_(line=False, merge_part=False, main_part=False, jam=False,
       reset=False, auto=True):
    return {"LineRun": line, "PartAtMerge": merge_part,
            "PartOnMain": main_part, "JamSensor": jam,
            "ResetBtn": reset, "ModeAuto": auto}


def o_(main=False, merge=False, high=False, alarm=False, st=0):
    return {"MainMotor": main, "MergeMotor": merge, "SpeedHigh": high,
            "JamAlarm": alarm, "Status": st}


def to(c, n, ins, outs):
    while len(c.rows) < n:
        c.add(ins, outs)
    return c


def case_01():
    """启动：LineRun 上升沿开主电机，合流段无料才开汇流电机。"""
    c = Case("S13-01", "K1;K2;C10",
             "LineRun 上升沿开主电机；合流点无料时汇流电机跟随启动")
    c.add(i_(), o_())                                    # 0 初态
    c.add(i_(line=True), o_(main=True, merge=True))      # 1 启动
    c.add(i_(line=True), o_(main=True, merge=True))      # 2
    c.add(i_(line=False), o_())                          # 3 停机，两台电机停
    return c


def case_02():
    """防撞：合流段有料时汇流电机必须停。"""
    c = Case("S13-02", "K2;C4",
             "PartAtMerge = TRUE 时 MergeMotor 当拍为 FALSE，主电机照常")
    c.add(i_(), o_())                                    # 0
    c.add(i_(line=True), o_(main=True, merge=True))      # 1
    c.add(i_(line=True, merge_part=True), o_(main=True))  # 2 有料，汇流停
    c.add(i_(line=True), o_(main=True, merge=True))      # 3 料走，恢复
    return c


def case_03():
    """堵料 2 s：报警并停两台电机。"""
    c = Case("S13-03", "K3;C5",
             "JamSensor 连续 100 拍后 JamAlarm = TRUE、两台电机停、Status = 16#8C01")
    c.add(i_(), o_())                                    # 0
    c.add(i_(line=True), o_(main=True, merge=True))      # 1
    c.add(i_(line=True, jam=True), o_(main=True, merge=True))  # 2 开始堵
    to(c, JAM + 2, i_(line=True, jam=True), o_(main=True, merge=True))  # 3..100
    c.add(i_(line=True, jam=True),
          o_(main="X", merge="X", alarm="X", st="X"))    # 101 满 2 s 边界
    c.add(i_(line=True, jam=True), o_(alarm=True, st=0x8C01))  # 102 报警停机
    c.add(i_(line=True, jam=True), o_(alarm=True, st=0x8C01))  # 103
    return c


def case_04():
    """复位：JamSensor 消失 + ResetBtn 上升沿，且需重新给 LineRun 沿。"""
    c = Case("S13-04", "K4;C6",
             "堵料未消失时复位无效；消失后复位清报警，但要重新给 LineRun 上升沿")
    c.add(i_(), o_())                                    # 0
    c.add(i_(line=True), o_(main=True, merge=True))      # 1
    c.add(i_(line=True, jam=True), o_(main=True, merge=True))  # 2
    to(c, JAM + 2, i_(line=True, jam=True), o_(main=True, merge=True))
    c.add(i_(line=True, jam=True), o_(alarm=True, st=0x8C01))  # 102 报警
    c.add(i_(line=True, jam=True, reset=True),
          o_(alarm=True, st=0x8C01))                     # 103 料还在，复位无效
    c.add(i_(line=True, reset=False),
          o_(alarm="X", st="X"))                         # 104 料走，等复位沿
    c.add(i_(line=True, reset=True), o_(alarm="X", st="X"))  # 105 复位
    c.add(i_(line=True), o_())                           # 106 复位后仍停
    c.add(i_(line=True), o_())                           # 107 无新上升沿
    return c


def case_05():
    """速度档：有料满 3 s 切高速。"""
    c = Case("S13-05", "K5;C7",
             "主线段连续有料满 150 拍切高速，中间抖动不得频繁换档")
    c.add(i_(), o_())                                    # 0
    c.add(i_(line=True), o_(main=True, merge=True))      # 1
    c.add(i_(line=True, main_part=True),
          o_(main=True, merge=True))                     # 2 开始有料
    to(c, HIGH + 2, i_(line=True, main_part=True),
       o_(main=True, merge=True))                        # 3..150
    c.add(i_(line=True, main_part=True),
          o_(main=True, merge=True, high="X"))           # 151 满 3 s 边界
    c.add(i_(line=True, main_part=True),
          o_(main=True, merge=True, high=True))          # 152 高速档
    return c


def main():
    cases = [c.dict() for c in
             (case_01(), case_02(), case_03(), case_04(), case_05())]
    write_cases(OUT, FX, cases)
    print("S13: %d 条用例 / %d 行"
          % (len(cases), sum(len(c["rows"]) for c in cases)))


if __name__ == "__main__":
    main()

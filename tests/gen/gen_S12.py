"""生成 S12（急停后安全重启与班次统计）的用例。

60 s 计时 = 3000 拍。
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from _emit import Case, write_cases  # noqa: E402

TESTS = HERE.parent
FX = TESTS / "cases" / "_fixtures" / "S12.io.json"
OUT = TESTS / "cases" / "S12.csv"

MINUTE = 3000       # 60 s


def i_(estop=True, reset=False, start=False, door=True):
    return {"EStop_NC": estop, "ResetBtn": reset, "StartBtn": start,
            "DoorClosed": door}


def o_(run=False, count=0, lamp=False, st=0):
    return {"MachineRun": run, "ShiftCount": count, "AlarmLamp": lamp,
            "Status": st}


def to(c, n, ins, outs):
    while len(c.rows) < n:
        c.add(ins, outs)
    return c


def case_01():
    """急停：立即停机并报警。"""
    c = Case("S12-01", "K1;C1",
             "EStop_NC = FALSE 当拍 MachineRun = FALSE、AlarmLamp = TRUE")
    c.add(i_(), o_())                                    # 0 初态
    c.add(i_(start=True), o_(run=True))                  # 1 启动
    c.add(i_(estop=False), o_(lamp=True, st=0x8B01))     # 2 急停
    c.add(i_(), o_(lamp=True, st=0x8B02))                # 3 解除，待复位
    return c


def case_02():
    """重启顺序：门关 → 复位上升沿 → 启动上升沿。"""
    c = Case("S12-02", "K2",
             "缺少任一步都不得运行：先复位后启动，顺序颠倒无效")
    c.add(i_(), o_())                                    # 0
    c.add(i_(start=True), o_(run=True))                  # 1
    c.add(i_(estop=False), o_(lamp=True, st=0x8B01))     # 2 急停
    c.add(i_(), o_(lamp=True, st=0x8B02))                # 3 解除
    c.add(i_(start=True), o_(lamp=True, st=0x8B02))      # 4 未复位就启动，无效
    c.add(i_(reset=True), o_(lamp="X", st="X"))          # 5 复位
    c.add(i_(start=True), o_(run=True))                  # 6 启动
    return c


def case_03():
    """复位后门再次打开，复位标志失效。"""
    c = Case("S12-03", "K3",
             "复位后门又打开必须重新复位，否则启动无效")
    c.add(i_(), o_())                                    # 0
    c.add(i_(start=True), o_(run=True))                  # 1
    c.add(i_(estop=False), o_(lamp=True, st=0x8B01))     # 2
    c.add(i_(), o_(lamp=True, st=0x8B02))                # 3
    c.add(i_(reset=True), o_(lamp="X", st="X"))          # 4 复位
    c.add(i_(door=False), o_(lamp=True, st=0x8B03))      # 5 门又开，复位作废
    c.add(i_(start=True), o_(lamp=True, st=0x8B03))      # 6 启动无效
    c.add(i_(reset=True), o_(lamp="X", st="X"))          # 7 重新复位
    c.add(i_(start=True), o_(run=True))                  # 8 启动成功
    return c


def case_04():
    """运行满 60 s 班次计数加 1，急停期间冻结。"""
    c = Case("S12-04", "K4",
             "运行满 3000 拍 ShiftCount 加 1；急停期间计数不变")
    c.add(i_(), o_())                                    # 0
    c.add(i_(start=True), o_(run=True))                  # 1 启动
    to(c, MINUTE, i_(), o_(run=True))                    # 2..2999
    c.add(i_(), o_(run="X", count="X"))                  # 3000 满 60 s 边界
    c.add(i_(), o_(run=True, count=1))                   # 3001
    c.add(i_(estop=False), o_(count=1, lamp=True, st=0x8B01))  # 3002 急停，计数冻结
    c.add(i_(estop=False), o_(count=1, lamp=True, st=0x8B01))  # 3003
    return c


def main():
    cases = [c.dict() for c in
             (case_01(), case_02(), case_03(), case_04())]
    write_cases(OUT, FX, cases)
    print("S12: %d 条用例 / %d 行"
          % (len(cases), sum(len(c["rows"]) for c in cases)))


if __name__ == "__main__":
    main()

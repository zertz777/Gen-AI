"""生成 S07（灌装四工位节拍控制）的用例。

单步超时 5 s = 250 拍。
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from _emit import Case, write_cases  # noqa: E402

TESTS = HERE.parent
FX = TESTS / "cases" / "_fixtures" / "S07.io.json"
OUT = TESTS / "cases" / "S07.csv"

TIMEOUT = 250      # 5 s


def i_(bottle=False, fill=False, cap=False, pack=False,
       start=False, estop=True):
    return {"BottleIn": bottle, "FillDone": fill, "CapDone": cap,
            "PackDone": pack, "StartBtn": start, "EStop_NC": estop}


def o_(conv=False, fill=False, cap=False, pack=False, count=0, st=0):
    return {"Conveyor": conv, "FillValve": fill, "CapMotor": cap,
            "PackCyl": pack, "CycleCount": count, "Status": st}


def case_01():
    """完整一瓶：进瓶→灌装→封盖→包装→计数。"""
    c = Case("S07-01", "K1;K2;K4;C10",
             "按 0→1→2→3→0 走完一瓶，CycleCount 加 1，四路输出互斥")
    c.add(i_(), o_())                                   # 0 初态
    c.add(i_(start=True), o_(conv=True))                # 1 启动，进瓶
    c.add(i_(bottle=True), o_(fill=True))               # 2 进瓶到位，开灌装
    c.add(i_(bottle=True), o_(fill=True))               # 3
    c.add(i_(bottle=True), o_(fill=True))               # 4
    c.add(i_(bottle=True), o_(fill=True))               # 5
    c.add(i_(bottle=True, fill=True), o_(cap=True))     # 6 灌装完成，封盖
    c.add(i_(cap=True), o_(pack=True))                  # 7 封盖完成，包装
    c.add(i_(pack=True), o_(conv=True, count=1))        # 8 包装完成，回到进瓶
    return c


def case_02():
    """单步超时：灌装 5 s 未完成报警并关输出。"""
    c = Case("S07-02", "K3",
             "灌装步超过 5 s 未收到 FillDone：Status = 16#8701、关灌装阀、步号不变")
    c.add(i_(), o_())                                   # 0
    c.add(i_(start=True), o_(conv=True))                # 1
    c.add(i_(bottle=True), o_(fill=True))               # 2 进灌装步
    for _ in range(TIMEOUT - 3):                        # 3..249 等待
        c.add(i_(bottle=True), o_(fill=True))
    c.add(i_(bottle=True), o_(fill="X", st="X"))        # 250 满 5 s 边界
    c.add(i_(bottle=True), o_(st=0x8701))               # 251 超时，关阀
    c.add(i_(bottle=True), o_(st=0x8701))               # 252 保持步号
    return c


def case_03():
    """急停：全部输出停、步号归 0。"""
    c = Case("S07-03", "K5;C1",
             "EStop_NC = FALSE 当拍四个执行器全停，Status = 16#8702")
    c.add(i_(), o_())                                   # 0
    c.add(i_(start=True), o_(conv=True))                # 1
    c.add(i_(bottle=True), o_(fill=True))               # 2
    c.add(i_(bottle=True, estop=False), o_(st=0x8702))  # 3 急停
    c.add(i_(bottle=True), o_())                        # 4 解除，回到 Step 0 停止
    return c


def case_04():
    """灌装输出至少保持 5 拍（100 ms）。"""
    c = Case("S07-04", "K2;C9",
             "FillDone 立即到达时灌装阀仍至少保持 5 拍，不得单拍脉冲")
    c.add(i_(), o_())                                   # 0
    c.add(i_(start=True), o_(conv=True))                # 1
    c.add(i_(bottle=True), o_(fill=True))               # 2
    c.add(i_(bottle=True, fill=True), o_(fill=True))    # 3 完成信号早到
    c.add(i_(bottle=True, fill=True), o_(fill=True))    # 4
    c.add(i_(bottle=True, fill=True), o_(fill=True))    # 5
    c.add(i_(bottle=True, fill=True), o_(fill=True))    # 6
    c.add(i_(bottle=True, fill=True), o_(cap=True))     # 7 保持满 5 拍后推进
    return c


def main():
    cases = [c.dict() for c in
             (case_01(), case_02(), case_03(), case_04())]
    write_cases(OUT, FX, cases)
    print("S07: %d 条用例 / %d 行"
          % (len(cases), sum(len(c["rows"]) for c in cases)))


if __name__ == "__main__":
    main()

"""生成 S09（CIP 三步清洗时序）的用例。

30 s = 1500 拍，60 s = 3000 拍；步结束那一拍写 X。
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from _emit import Case, write_cases  # noqa: E402

TESTS = HERE.parent
FX = TESTS / "cases" / "_fixtures" / "S09.io.json"
OUT = TESTS / "cases" / "S09.csv"

T30 = 1500
T60 = 3000


def i_(start=False, done=False, estop=True):
    return {"StartCIP": start, "StepDone": done, "EStop_NC": estop}


def o_(water=False, lye=False, rinse=False, pump=False, step=0, st=0):
    return {"WaterValve": water, "LyeValve": lye, "RinseValve": rinse,
            "PumpRun": pump, "StepNo": step, "Status": st}


def to(c, n, ins, outs):
    while len(c.rows) < n:
        c.add(ins, outs)
    return c


def case_01():
    """完整三步：30 s 水洗 → 60 s 碱洗 → 30 s 清水 → 归零。"""
    c = Case("S09-01", "K1;K4;C5",
             "按 30/60/30 s 自动推进三步，结束后全部关闭、StepNo 回 0")
    c.add(i_(), o_())                                        # 0 初态
    c.add(i_(start=True), o_(water=True, pump=True, step=1))  # 1 水洗
    to(c, T30, i_(), o_(water=True, pump=True, step=1))       # 2..1499
    c.add(i_(), o_(water="X", pump="X", step="X"))            # 1500 满 30 s 边界
    c.add(i_(), o_(lye=True, pump=True, step=2))              # 1501 碱洗
    to(c, T30 + T60, i_(), o_(lye=True, pump=True, step=2))   # 1502..4499
    c.add(i_(), o_(lye="X", pump="X", step="X"))              # 4500 满 60 s 边界
    c.add(i_(), o_(rinse=True, pump=True, step=3))            # 4501 清水
    to(c, T30 + T60 + T30, i_(), o_(rinse=True, pump=True, step=3))  # 4502..5999
    c.add(i_(), o_(rinse="X", pump="X", step="X"))            # 6000 满 30 s 边界
    c.add(i_(), o_())                                         # 6001 结束
    return c


def case_02():
    """StepDone 上升沿提前结束当前步。"""
    c = Case("S09-02", "K4",
             "水洗进行中 StepDone 上升沿立即进入碱洗，不等 30 s")
    c.add(i_(), o_())                                         # 0
    c.add(i_(start=True), o_(water=True, pump=True, step=1))   # 1
    c.add(i_(), o_(water=True, pump=True, step=1))             # 2
    c.add(i_(done=True), o_(lye=True, pump=True, step=2))      # 3 提前结束
    c.add(i_(), o_(lye=True, pump=True, step=2))               # 4
    c.add(i_(done=True), o_(rinse=True, pump=True, step=3))    # 5 再次提前结束
    c.add(i_(), o_(rinse=True, pump=True, step=3))             # 6
    c.add(i_(done=True), o_())                                 # 7 结束
    return c


def case_03():
    """急停：全部关闭、步号归 0、流程作废。"""
    c = Case("S09-03", "K5;C1",
             "急停：EStop_NC = FALSE 当拍关阀停泵、StepNo 归 0，需重新 StartCIP")
    c.add(i_(), o_())                                         # 0
    c.add(i_(start=True), o_(water=True, pump=True, step=1))   # 1
    c.add(i_(estop=False), o_(st=0x8902))                      # 2 急停
    c.add(i_(), o_())                                          # 3 解除，保持停止
    c.add(i_(start=True), o_(water=True, pump=True, step=1))   # 4 重新启动
    return c


def case_04():
    """阀门互斥且泵不空转。"""
    c = Case("S09-04", "K2;K3",
             "任何时刻最多一个阀门为 TRUE，PumpRun 为 TRUE 时必有阀门打开")
    c.add(i_(), o_())                                         # 0
    c.add(i_(start=True), o_(water=True, pump=True, step=1))   # 1
    c.add(i_(done=True), o_(lye=True, pump=True, step=2))      # 2
    c.add(i_(done=True), o_(rinse=True, pump=True, step=3))    # 3
    c.add(i_(done=True), o_())                                 # 4
    return c


def main():
    cases = [c.dict() for c in
             (case_01(), case_02(), case_03(), case_04())]
    write_cases(OUT, FX, cases)
    print("S09: %d 条用例 / %d 行"
          % (len(cases), sum(len(c["rows"]) for c in cases)))


if __name__ == "__main__":
    main()

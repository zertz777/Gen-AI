"""生成 S11（传感器断线检测与降级运行）的用例。

断线 2 s = 100 拍进入降级；恢复 3 s = 150 拍退出降级。
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from _emit import Case, write_cases  # noqa: E402

TESTS = HERE.parent
FX = TESTS / "cases" / "_fixtures" / "S11.io.json"
OUT = TESTS / "cases" / "S11.csv"

BREAK = 100        # 2 s
RECOVER = 150      # 3 s
HALF = 25          # 1 Hz 半周期


def i_(cur, fb=80.0):
    return {"SensorCurrent": cur, "FallbackValue": fb}


def o_(valid=False, degraded=False, ctrl=0.0, lamp=False, st=0):
    return {"SensorValid": valid, "DegradedMode": degraded,
            "ControlValue": ctrl, "AlarmLamp": lamp, "Status": st}


def to(c, n, ins, outs):
    while len(c.rows) < n:
        c.add(ins, outs)
    return c


def case_01():
    """正常量程：4—20 mA 线性换算成 0—100 ℃。"""
    c = Case("S11-01", "K1;C10",
             "12 mA 对应 50 ℃；20 mA 对应 100 ℃；信号有效不降级")
    c.add(i_(12.0), o_(ctrl="X"))                # 0 初态
    c.add(i_(12.0), o_(valid=True, ctrl=50.0))   # 1
    c.add(i_(20.0), o_(valid=True, ctrl=100.0))  # 2
    c.add(i_(4.0), o_(valid=True, ctrl=0.0))     # 3
    return c


def case_02():
    """断线满 2 s 进入降级，控制值切备用值。"""
    c = Case("S11-02", "K2;K4",
             "断线满 2 s 进入降级（失效导向安全）：ControlValue 切换为 FallbackValue")
    c.add(i_(12.0), o_(ctrl="X"))                      # 0
    c.add(i_(12.0), o_(valid=True, ctrl=50.0))         # 1
    c.add(i_(2.0), o_(lamp=True, st=0x8A01))           # 2 断线开始
    to(c, BREAK + 1, i_(2.0), o_(lamp="X", st=0x8A01))  # 3..100 未满 2 s
    c.add(i_(2.0), o_(degraded="X", ctrl="X", lamp="X", st="X"))  # 101 边界
    c.add(i_(2.0), o_(degraded=True, ctrl=80.0, lamp=True, st=0x8A02))  # 102 降级
    c.add(i_(2.0), o_(degraded=True, ctrl=80.0, lamp=True, st=0x8A02))  # 103
    return c


def case_03():
    """恢复满 3 s 才退出降级。"""
    c = Case("S11-03", "K3",
             "断线恢复后 SensorValid 立即 TRUE，但降级要满 3 s 才退出")
    c.add(i_(12.0), o_(ctrl="X"))                       # 0
    c.add(i_(12.0), o_(valid=True, ctrl=50.0))          # 1
    c.add(i_(2.0), o_(st=0x8A01))                       # 2 断线开始
    to(c, BREAK + 1, i_(2.0), o_(st=0x8A01))            # 3..100 未满 2 s
    c.add(i_(2.0), o_(degraded="X", ctrl="X", lamp="X", st="X"))  # 101 边界
    c.add(i_(2.0), o_(degraded=True, ctrl=80.0, lamp=True, st=0x8A02))  # 102
    to(c, BREAK + 2 + RECOVER, i_(2.0),
       o_(degraded=True, ctrl=80.0, lamp=True, st=0x8A02))   # 103..251
    c.add(i_(12.0), o_(valid=True, degraded=True, ctrl=80.0,
                      lamp=True, st=0x8A03))            # 252 恢复计时起点
    to(c, BREAK + 2 + RECOVER + RECOVER, i_(12.0),
       o_(valid=True, degraded=True, ctrl=80.0, lamp=True, st=0x8A03))  # 253..401
    c.add(i_(12.0), o_(valid=True, degraded="X", ctrl="X",
                      lamp="X", st="X"))                # 402 满 3 s 边界
    c.add(i_(12.0), o_(valid=True, ctrl=50.0))          # 403 退出降级
    return c


def case_04():
    """断线未满 2 s：报警灯 1 Hz 闪烁。"""
    c = Case("S11-04", "K2",
             "断线但未满 2 s 时报警灯闪烁，不进入降级")
    c.add(i_(12.0), o_(ctrl="X"))                       # 0
    c.add(i_(2.0), o_(lamp=True, st=0x8A01))            # 1
    for _ in range(HALF - 1):                           # 2..25 亮
        c.add(i_(2.0), o_(lamp=True, st=0x8A01))
    for _ in range(HALF):                               # 26..50 灭
        c.add(i_(2.0), o_(st=0x8A01))
    for _ in range(HALF):                               # 51..75 亮
        c.add(i_(2.0), o_(lamp=True, st=0x8A01))
    return c


def main():
    cases = [c.dict() for c in
             (case_01(), case_02(), case_03(), case_04())]
    write_cases(OUT, FX, cases)
    print("S11: %d 条用例 / %d 行"
          % (len(cases), sum(len(c["rows"]) for c in cases)))


if __name__ == "__main__":
    main()

"""生成 P19（机械臂六动作四模式）的用例。

单步模式由 Start 上升沿逐动作推进，判定可以写到拍；
单周期/连续模式的「到位后下一动作何时开始」需求未定义，过渡拍写 X。
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from _emit import Case, write_cases  # noqa: E402

TESTS = HERE.parent
FX = TESTS / "cases" / "_fixtures" / "P19.io.json"
OUT = TESTS / "cases" / "P19.csv"

BASE = {
    "ManualMode": False, "SingleStepMode": False, "SingleCycleMode": False,
    "ContinuousMode": False, "EmergencyStop": True, "Start": False,
    "DownButton": False, "UpButton": False, "LeftButton": False,
    "RightButton": False, "GripButton": False, "ReleaseButton": False,
    "DownLimitSwitch": False, "UpLimitSwitch": True, "LeftLimitSwitch": True,
    "RightLimitSwitch": False, "GripLimitSwitch": False,
    "ReleaseLimitSwitch": False,
}


def i_(**kw):
    d = dict(BASE)
    d.update(kw)
    return d


def o_(down=False, up=False, left=False, right=False, grip=False,
       release=False):
    return {"MoveDown": down, "MoveUp": up, "MoveLeft": left,
            "MoveRight": right, "ActivateGrip": grip,
            "ActivateRelease": release}


OFF = o_()


def case_01():
    """手动模式：按住才动，到限位或松手立即停。"""
    c = Case("P19-01", "K1;C2;C4;C7",
             "手动模式按住按钮才动作；到达限位或松开按钮当拍停止")
    c.add(i_(), OFF)                                                   # 0 初态
    c.add(i_(ManualMode=True, DownButton=True), o_(down=True))         # 1 下
    c.add(i_(ManualMode=True, DownButton=True), o_(down=True))         # 2 继续下
    c.add(i_(ManualMode=True, DownButton=True, DownLimitSwitch=True), OFF)  # 3 到下限位
    c.add(i_(ManualMode=True), OFF)                                    # 4 松手
    c.add(i_(ManualMode=True, RightButton=True), o_(right=True))       # 5 右
    c.add(i_(ManualMode=True), OFF)                                    # 6 松手立即停
    c.add(i_(ManualMode=True, GripButton=True), o_(grip=True))         # 7 抓取
    c.add(i_(ManualMode=True, GripButton=True, GripLimitSwitch=True), OFF)  # 8 抓到位
    c.add(i_(ManualMode=True, LeftButton=True), OFF)                   # 9 已在左位，不动
    c.add(i_(ManualMode=True, UpButton=True), OFF)                     # 10 已在上位，不动
    return c


def case_02():
    """单步模式：每按一次 Start 走一个动作。"""
    c = Case("P19-02", "K3;K5;C6",
             "单步模式八个动作逐个确认：下→抓→上→右→下→放→上→左")
    c.add(i_(), OFF)                                                       # 0
    c.add(i_(SingleStepMode=True, Start=True), o_(down=True))              # 1 下
    c.add(i_(SingleStepMode=True, UpLimitSwitch=False), o_(down=True))     # 2 下行中
    c.add(i_(SingleStepMode=True, DownLimitSwitch=True), OFF)              # 3 到下位
    c.add(i_(SingleStepMode=True, DownLimitSwitch=True), OFF)              # 4 等确认
    c.add(i_(SingleStepMode=True, DownLimitSwitch=True, Start=True),
          o_(grip=True))                                                   # 5 抓
    c.add(i_(SingleStepMode=True, DownLimitSwitch=True, GripLimitSwitch=True),
          OFF)                                                             # 6 抓到
    c.add(i_(SingleStepMode=True, DownLimitSwitch=True, GripLimitSwitch=True),
          OFF)                                                             # 7 等确认
    c.add(i_(SingleStepMode=True, DownLimitSwitch=True, GripLimitSwitch=True,
             Start=True), o_(up=True))                                     # 8 上
    c.add(i_(SingleStepMode=True, GripLimitSwitch=True), OFF)              # 9 到上位
    c.add(i_(SingleStepMode=True, GripLimitSwitch=True), OFF)              # 10 等确认
    c.add(i_(SingleStepMode=True, GripLimitSwitch=True, Start=True),
          o_(right=True))                                                  # 11 右
    c.add(i_(SingleStepMode=True, GripLimitSwitch=True, RightLimitSwitch=True),
          OFF)                                                             # 12 到右位
    c.add(i_(SingleStepMode=True, GripLimitSwitch=True, RightLimitSwitch=True),
          OFF)                                                             # 13 等确认
    c.add(i_(SingleStepMode=True, GripLimitSwitch=True, RightLimitSwitch=True,
             Start=True), o_(down=True))                                   # 14 下
    c.add(i_(SingleStepMode=True, GripLimitSwitch=True, RightLimitSwitch=True,
             DownLimitSwitch=True), OFF)                                   # 15 到下位
    c.add(i_(SingleStepMode=True, GripLimitSwitch=True, RightLimitSwitch=True,
             DownLimitSwitch=True), OFF)                                   # 16 等确认
    c.add(i_(SingleStepMode=True, GripLimitSwitch=True, RightLimitSwitch=True,
             DownLimitSwitch=True, Start=True), o_(release=True))          # 17 放
    c.add(i_(SingleStepMode=True, RightLimitSwitch=True, DownLimitSwitch=True,
             ReleaseLimitSwitch=True), OFF)                                # 18 放到位
    c.add(i_(SingleStepMode=True, RightLimitSwitch=True, DownLimitSwitch=True,
             ReleaseLimitSwitch=True), OFF)                                # 19 等确认
    c.add(i_(SingleStepMode=True, RightLimitSwitch=True, DownLimitSwitch=True,
             ReleaseLimitSwitch=True, Start=True), o_(up=True))            # 20 上
    c.add(i_(SingleStepMode=True, RightLimitSwitch=True,
             ReleaseLimitSwitch=True), OFF)                                # 21 到上位
    c.add(i_(SingleStepMode=True, RightLimitSwitch=True,
             ReleaseLimitSwitch=True), OFF)                                # 22 等确认
    c.add(i_(SingleStepMode=True, RightLimitSwitch=True,
             ReleaseLimitSwitch=True, Start=True), o_(left=True))          # 23 左
    c.add(i_(SingleStepMode=True, ReleaseLimitSwitch=True,
             LeftLimitSwitch=True), OFF)                                   # 24 回到左上
    return c


def case_03():
    """单周期模式：按一次 Start 自动走完一整轮。"""
    c = Case("P19-03", "K4;K5;C7",
             "单周期模式自动完成下→抓→上→右→下→放→上→左后停在左上")
    c.add(i_(), OFF)                                                      # 0
    c.add(i_(SingleCycleMode=True, Start=True), o_(down=True))            # 1 下
    c.add(i_(SingleCycleMode=True, UpLimitSwitch=False), o_(down=True))   # 2
    c.add(i_(SingleCycleMode=True, DownLimitSwitch=True), o_(grip="X"))   # 3 到下位
    c.add(i_(SingleCycleMode=True, DownLimitSwitch=True), o_(grip=True))  # 4 抓
    c.add(i_(SingleCycleMode=True, DownLimitSwitch=True, GripLimitSwitch=True),
          o_(up="X"))                                                     # 5 抓到
    c.add(i_(SingleCycleMode=True, GripLimitSwitch=True), o_(up=True))    # 6 上
    c.add(i_(SingleCycleMode=True, GripLimitSwitch=True, UpLimitSwitch=True),
          o_(right="X"))                                                  # 7 到上位
    c.add(i_(SingleCycleMode=True, GripLimitSwitch=True, UpLimitSwitch=True),
          o_(right=True))                                                 # 8 右
    c.add(i_(SingleCycleMode=True, GripLimitSwitch=True, RightLimitSwitch=True),
          o_(down="X"))                                                   # 9 到右位
    c.add(i_(SingleCycleMode=True, GripLimitSwitch=True, RightLimitSwitch=True),
          o_(down=True))                                                  # 10 下
    c.add(i_(SingleCycleMode=True, GripLimitSwitch=True, RightLimitSwitch=True,
             DownLimitSwitch=True), o_(release="X"))                      # 11 到下位
    c.add(i_(SingleCycleMode=True, GripLimitSwitch=True, RightLimitSwitch=True,
             DownLimitSwitch=True), o_(release=True))                     # 12 放
    c.add(i_(SingleCycleMode=True, RightLimitSwitch=True, DownLimitSwitch=True,
             ReleaseLimitSwitch=True), o_(up="X"))                        # 13 放到位
    c.add(i_(SingleCycleMode=True, RightLimitSwitch=True, DownLimitSwitch=True,
             ReleaseLimitSwitch=True), o_(up=True))                       # 14 上
    c.add(i_(SingleCycleMode=True, RightLimitSwitch=True,
             ReleaseLimitSwitch=True, UpLimitSwitch=True), o_(left="X"))  # 15 到上位
    c.add(i_(SingleCycleMode=True, RightLimitSwitch=True,
             ReleaseLimitSwitch=True, UpLimitSwitch=True), o_(left=True))  # 16 左
    c.add(i_(SingleCycleMode=True, ReleaseLimitSwitch=True,
             LeftLimitSwitch=True), OFF)                                  # 17 回左上，停
    c.add(i_(SingleCycleMode=True, ReleaseLimitSwitch=True,
             LeftLimitSwitch=True), OFF)                                  # 18 等指令
    return c


def case_04():
    """连续模式：回到左上后自动开始下一轮。"""
    c = Case("P19-04", "K4",
             "连续模式完成一轮后不停，回到左上继续下一轮")
    c.add(i_(), OFF)                                                      # 0
    c.add(i_(ContinuousMode=True, Start=True), o_(down=True))             # 1
    c.add(i_(ContinuousMode=True, UpLimitSwitch=False), o_(down=True))    # 2
    c.add(i_(ContinuousMode=True, DownLimitSwitch=True), o_(grip="X"))    # 3
    c.add(i_(ContinuousMode=True, DownLimitSwitch=True), o_(grip=True))   # 4
    c.add(i_(ContinuousMode=True, DownLimitSwitch=True, GripLimitSwitch=True),
          o_(up="X"))                                                     # 5
    c.add(i_(ContinuousMode=True, GripLimitSwitch=True), o_(up=True))     # 6
    c.add(i_(ContinuousMode=True, GripLimitSwitch=True, UpLimitSwitch=True),
          o_(right="X"))                                                  # 7
    c.add(i_(ContinuousMode=True, GripLimitSwitch=True, UpLimitSwitch=True),
          o_(right=True))                                                 # 8
    c.add(i_(ContinuousMode=True, GripLimitSwitch=True, RightLimitSwitch=True),
          o_(down="X"))                                                   # 9
    c.add(i_(ContinuousMode=True, GripLimitSwitch=True, RightLimitSwitch=True),
          o_(down=True))                                                  # 10
    c.add(i_(ContinuousMode=True, GripLimitSwitch=True, RightLimitSwitch=True,
             DownLimitSwitch=True), o_(release="X"))                      # 11
    c.add(i_(ContinuousMode=True, GripLimitSwitch=True, RightLimitSwitch=True,
             DownLimitSwitch=True), o_(release=True))                     # 12
    c.add(i_(ContinuousMode=True, RightLimitSwitch=True, DownLimitSwitch=True,
             ReleaseLimitSwitch=True), o_(up="X"))                        # 13
    c.add(i_(ContinuousMode=True, RightLimitSwitch=True, DownLimitSwitch=True,
             ReleaseLimitSwitch=True), o_(up=True))                       # 14
    c.add(i_(ContinuousMode=True, RightLimitSwitch=True,
             ReleaseLimitSwitch=True, UpLimitSwitch=True), o_(left="X"))  # 15
    c.add(i_(ContinuousMode=True, RightLimitSwitch=True,
             ReleaseLimitSwitch=True, UpLimitSwitch=True), o_(left=True))  # 16
    c.add(i_(ContinuousMode=True, ReleaseLimitSwitch=True,
             LeftLimitSwitch=True), o_(down="X"))                         # 17 回左上
    c.add(i_(ContinuousMode=True, ReleaseLimitSwitch=True,
             LeftLimitSwitch=True), o_(down=True))                        # 18 第二轮开始
    c.add(i_(ContinuousMode=True, ReleaseLimitSwitch=True,
             LeftLimitSwitch=True, DownLimitSwitch=True), o_(grip="X"))   # 19
    return c


def case_05():
    """急停：六路动作当拍清零，恢复后不得自行续跑。"""
    c = Case("P19-05", "K4;C1",
             "急停当拍停止全部动作；解除后保持全停，必须重新给 Start")
    c.add(i_(), OFF)                                                   # 0
    c.add(i_(SingleCycleMode=True, Start=True), o_(down=True))         # 1
    c.add(i_(SingleCycleMode=True, EmergencyStop=False), OFF)          # 2 急停
    c.add(i_(SingleCycleMode=True, EmergencyStop=False), OFF)          # 3
    c.add(i_(SingleCycleMode=True), OFF)                               # 4 解除，不得续跑
    c.add(i_(SingleCycleMode=True), OFF)                               # 5
    return c


def case_06():
    """手动模式已到限位时，按钮不得再输出动作。"""
    c = Case("P19-06", "K1;K5;C7",
             "已在限位时按对应按钮不得输出动作（下行/上行/抓取/释放）")
    c.add(i_(), OFF)                                                   # 0
    c.add(i_(ManualMode=True, DownButton=True, DownLimitSwitch=True), OFF)   # 1
    c.add(i_(ManualMode=True, UpButton=True, UpLimitSwitch=True), OFF)       # 2
    c.add(i_(ManualMode=True, GripButton=True, GripLimitSwitch=True), OFF)   # 3
    c.add(i_(ManualMode=True, ReleaseButton=True, ReleaseLimitSwitch=True),
          OFF)                                                             # 4
    c.add(i_(ManualMode=True, LeftButton=True, LeftLimitSwitch=True), OFF)   # 5
    c.add(i_(ManualMode=True, RightButton=True, RightLimitSwitch=True), OFF)  # 6
    return c


def case_07():
    """K2：多模式同时为 TRUE 时，只有一种模式的动作生效。"""
    c = Case("P19-07", "K2",
             "多模式同时选中：无输入时不得有任何动作；有输入时归属哪种模式未定义，写 X")
    c.add(i_(), OFF)                                                   # 0
    c.add(i_(ManualMode=True, SingleStepMode=True), OFF)               # 1 都空闲，全停
    c.add(i_(ManualMode=True, SingleStepMode=True, Start=True),
          o_(down="X", up="X", left="X", right="X",
             grip="X", release="X"))                                   # 2 归属未定义
    c.add(i_(ManualMode=True, SingleStepMode=True, DownButton=True,
             Start=True),
          o_(down="X", up="X", left="X", right="X",
             grip="X", release="X"))                                   # 3 归属未定义
    c.add(i_(ManualMode=True, SingleStepMode=True), OFF)               # 4 撤销输入后全停
    return c


def main():
    cases = [c.dict() for c in
             (case_01(), case_02(), case_03(), case_04(), case_05(),
              case_06(), case_07())]
    write_cases(OUT, FX, cases)
    print("P19: %d 条用例 / %d 行 -> %s"
          % (len(cases), sum(len(c["rows"]) for c in cases), OUT))


if __name__ == "__main__":
    main()

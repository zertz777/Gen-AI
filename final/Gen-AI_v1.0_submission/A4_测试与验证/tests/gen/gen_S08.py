"""生成 S08（分拣线配方切换）的用例。

切换保持 2 s = 100 拍。
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from _emit import Case, write_cases  # noqa: E402

TESTS = HERE.parent
FX = TESTS / "cases" / "_fixtures" / "S08.io.json"
OUT = TESTS / "cases" / "S08.csv"

BUSY = 100         # 2 s

# 配方号 -> (左阈值, 右阈值)
LIMITS = {1: (30.0, 60.0), 2: (50.0, 90.0), 3: (70.0, 120.0)}


def i_(recipe=1, req=False, height=0.0, estop=True):
    return {"RecipeSelect": recipe, "ChangeoverReq": req,
            "PartHeight": height, "EStop_NC": estop}


def o_(active=1, left=False, right=False, busy=False, st=0):
    return {"ActiveRecipe": active, "SortLeft": left, "SortRight": right,
            "Busy": busy, "Status": st}


def case_01():
    """配方 1 分拣：左 30 / 右 60。"""
    c = Case("S08-01", "K4;C2;C10",
             "配方 1：20 mm 分左、45 mm 分右、70 mm 超规格不动作")
    c.add(i_(), o_())                                    # 0 初态
    c.add(i_(height=20.0), o_(left=True))                # 1 分左
    c.add(i_(height=45.0), o_(right=True))               # 2 分右
    c.add(i_(height=70.0), o_(st=0x8802))                # 3 超右阈值
    c.add(i_(height=0.0), o_())                          # 4 无料
    return c


def case_02():
    """切换配方：Busy 保持 2 s，期间不得分拣。"""
    c = Case("S08-02", "K1;K2;C9",
             "无料时切换配方：Busy 保持 100 拍，期间 SortLeft/SortRight 均为 FALSE")
    c.add(i_(), o_())                                    # 0
    c.add(i_(recipe=2, req=True), o_(busy=True))         # 1 切换开始
    for _ in range(BUSY - 2):                            # 2..99
        c.add(i_(recipe=2, height=40.0), o_(busy=True))
    c.add(i_(recipe=2, height=40.0), o_(busy="X", active="X"))  # 100 满 2 s 边界
    c.add(i_(recipe=2, height=40.0), o_(active=2, left=True))   # 101 新配方生效
    return c


def case_03():
    """非法配方号：拒绝切换并报 16#8801。"""
    c = Case("S08-03", "K3",
             "RecipeSelect = 4 非法：ActiveRecipe 保持 1，Status = 16#8801")
    c.add(i_(), o_())                                    # 0
    c.add(i_(recipe=4, req=True), o_(st=0x8801))         # 1
    c.add(i_(recipe=4, req=True), o_(st=0x8801))         # 2
    c.add(i_(recipe=1), o_())                            # 3 恢复
    return c


def case_04():
    """有料时拒绝切换。"""
    c = Case("S08-04", "K2",
             "线上有料时按切换请求不得进入 Busy，ActiveRecipe 不变")
    c.add(i_(), o_())                                    # 0
    c.add(i_(recipe=3, req=True, height=25.0), o_(left=True))  # 1 有料，拒绝切换
    c.add(i_(recipe=3, height=25.0), o_(left=True))      # 2
    c.add(i_(recipe=3, req=True), o_(busy=True))         # 3 无料，允许切换
    return c


def main():
    cases = [c.dict() for c in
             (case_01(), case_02(), case_03(), case_04())]
    write_cases(OUT, FX, cases)
    print("S08: %d 条用例 / %d 行"
          % (len(cases), sum(len(c["rows"]) for c in cases)))


if __name__ == "__main__":
    main()

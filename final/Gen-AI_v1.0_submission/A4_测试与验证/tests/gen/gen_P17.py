"""生成 P17（配方管理）的用例。

配方库 recipe[] 在 fixture 里是 IN 列（D-09：INOUT 当输入，不判定输出），
所以本文件只判定 4 个成功标志、error、status 与查询结果；
库内容是否真的被改写，交给 PLCVerif 的 INOUT 变量去验。
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from _emit import Case, write_cases  # noqa: E402

TESTS = HERE.parent
FX = TESTS / "cases" / "_fixtures" / "P17.io.json"
OUT = TESTS / "cases" / "P17.csv"

# 初始配方库：槽 1、2 有配方，其余为空
DB_IDS = [1, 2, 0, 0, 0, 0, 0, 0, 0, 0]
DB_TYPE = [10, 20, 0, 0, 0, 0, 0, 0, 0, 0]
DB_RATIO = [0.5, 0.3, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
DB_TEMP = [100.0, 120.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]

# 满库：10 条全占
FULL_IDS = list(range(1, 11))

RECIPE1 = {"recipeID": 1, "ingredientType": 10,
           "ingredientRatio": 0.5, "productionTemperature": 100.0}
RECIPE2 = {"recipeID": 2, "ingredientType": 20,
           "ingredientRatio": 0.3, "productionTemperature": 120.0}


def i_(rid=0, typ=0, ratio=0.0, temp=0.0, add=False, dele=False,
       mod=False, qry=False, ids=None):
    return {"addRecipe": add, "deleteRecipe": dele,
            "modifyRecipe": mod, "queryRecipe": qry,
            "recipeIn": {"recipeID": rid, "ingredientType": typ,
                         "ingredientRatio": ratio,
                         "productionTemperature": temp},
            "recipe[].recipeID": list(DB_IDS if ids is None else ids),
            "recipe[].ingredientType": list(DB_TYPE),
            "recipe[].ingredientRatio": list(DB_RATIO),
            "recipe[].productionTemperature": list(DB_TEMP)}


def o_(added=False, deleted=False, modified=False, error=False,
       status=0, result="X"):
    return {"recipeAdded": added, "recipeDeleted": deleted,
            "recipeModified": modified, "error": error,
            "status": status, "recipeQueryResult": result}


def case_01():
    """按编号查询：命中则输出配方，未命中报 16#8001。"""
    c = Case("P17-01", "K3;C10",
             "查询命中输出配方内容；编号不存在报 16#8001")
    c.add(i_(), o_())                                            # 0 初态
    c.add(i_(1, qry=True), o_(result=RECIPE1))                   # 1 查 1
    c.add(i_(2, qry=True), o_(result=RECIPE2))                   # 2 查 2
    c.add(i_(), o_())                                            # 3 无请求
    return c


def case_02():
    """错误标志保持到下一次请求（C6）。"""
    c = Case("P17-02", "K3;C6",
             "查询不存在的编号报 8001；无请求期间 error/status 保持；新请求清掉")
    c.add(i_(), o_())                                            # 0
    c.add(i_(9, qry=True), o_(error=True, status=0x8001))        # 1 查不到
    c.add(i_(9, qry=True), o_(error=True, status=0x8001))        # 2 再查
    c.add(i_(), o_(error=True, status=0x8001))                   # 3 无请求，保持
    c.add(i_(1, qry=True), o_(result=RECIPE1))                   # 4 新请求，错误清除
    return c


def case_03():
    """新增：编号不重复时成功，落到最小空位。"""
    c = Case("P17-03", "K1;K2;C2",
             "新增不重复的编号成功：recipeAdded = TRUE、status = 0、error = FALSE")
    c.add(i_(), o_())                                            # 0
    c.add(i_(5, 30, 0.4, 150.0, add=True), o_(added=True))       # 1 新增 5
    c.add(i_(), o_())                                            # 2 无请求
    return c


def case_04():
    """新增重复编号：拒绝并报 16#8002。"""
    c = Case("P17-04", "K2;C1",
             "新增已存在的编号报 16#8002，且不得同时报成功")
    c.add(i_(), o_())                                            # 0
    c.add(i_(2, 99, 0.9, 999.0, add=True), o_(error=True, status=0x8002))  # 1
    c.add(i_(), o_(error=True, status=0x8002))                   # 2 保持
    return c


def case_05():
    """删除/修改不存在的编号报 16#8004 / 16#8005。"""
    c = Case("P17-05", "K3;C1",
             "删除不存在的编号报 8004，修改不存在的编号报 8005")
    c.add(i_(), o_())                                            # 0
    c.add(i_(9, dele=True), o_(error=True, status=0x8004))       # 1 删不存在
    c.add(i_(9, mod=True, typ=77), o_(error=True, status=0x8005))  # 2 改不存在
    c.add(i_(1, dele=True), o_(deleted=True))                    # 3 删存在的
    c.add(i_(2, mod=True, typ=21, ratio=0.6, temp=121.0), o_(modified=True))  # 4
    return c


def case_06():
    """库满时新增报 16#8003。"""
    c = Case("P17-06", "K4",
             "配方库 10 条全占时新增报 16#8003")
    c.add(i_(ids=FULL_IDS), o_())                                # 0
    c.add(i_(11, 30, 0.4, 150.0, add=True, ids=FULL_IDS),
          o_(error=True, status=0x8003))                         # 1
    c.add(i_(ids=FULL_IDS), o_(error=True, status=0x8003))       # 2 保持
    return c


def case_07():
    """成功标志只在请求拍有效，不得常驻。"""
    c = Case("P17-07", "K1;C4",
             "成功标志只在请求当拍为 TRUE，下一拍回落；新增与删除不得同拍为真")
    c.add(i_(), o_())                                            # 0
    c.add(i_(5, 30, 0.4, 150.0, add=True), o_(added=True))       # 1
    c.add(i_(), o_())                                            # 2 回落
    c.add(i_(1, dele=True), o_(deleted=True))                    # 3
    c.add(i_(), o_())                                            # 4 回落
    return c


def main():
    cases = [c.dict() for c in
             (case_01(), case_02(), case_03(), case_04(),
              case_05(), case_06(), case_07())]
    write_cases(OUT, FX, cases)
    print("P17: %d 条用例 / %d 行 -> %s"
          % (len(cases), sum(len(c["rows"]) for c in cases), OUT))


if __name__ == "__main__":
    main()

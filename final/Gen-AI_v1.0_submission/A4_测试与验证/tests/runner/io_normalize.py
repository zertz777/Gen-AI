"""把上游 io_table 规范化成 tests/cases/_fixtures/<题号>.io.json。

只做三件事，不改类型、不改方向语义：

1. FIELD_FIX —— 把裸字段名补上父结构前缀
2. 丢弃「容器列」—— INOUT 结构体数组如果已经有 <name>[].<field> 扁平字段，
   容器本身不再单列（否则同一个东西要写两遍）
3. 其余 INOUT 视作输入列（它们的输出侧不参与判定，见 ambiguities A-22）

依据：同项目的 P08 已经把逐元素字段写成 channels[].enable 这种形式。
"""
from __future__ import annotations

import json
import re
from pathlib import Path

# 上游 io_table 里的裸字段名 -> 规范化后的名字
# 依据：P07 的 pumpGroup、P17 的 recipe 都是 INOUT 结构体数组，
# 裸字段就是它们的逐元素字段（与 P08 的 channels[].xxx 同构）。
FIELD_FIX = {
    "P07": {
        "priority":  "pumpGroup[].priority",
        "selection": "pumpGroup[].selection",
        "RunComd":   "pumpGroup[].RunComd",
    },
    "P17": {
        "recipeID":              "recipe[].recipeID",
        "ingredientType":        "recipe[].ingredientType",
        "ingredientRatio":       "recipe[].ingredientRatio",
        "productionTemperature": "recipe[].productionTemperature",
    },
}


def _flatten(task_id: str, io_table: list) -> list:
    fix = FIELD_FIX.get(task_id, {})
    rows = []
    for row in io_table:
        rows.append({
            "name": fix.get(row["name"], row["name"]),
            "direction": row["direction"],
            "type": row["data_type"],
        })
    return rows


def _drop_containers(rows: list) -> list:
    """INOUT 容器若已有 <name>[].<field> 子列，容器本身不再单列。

    子列的类型要升一维：priority: INT -> ARRAY[1..5] OF INT，
    因为这一列装的是 5 台泵的同一个字段。
    """
    names = {r["name"] for r in rows}
    dims = {}
    for r in rows:
        m = re.match(r"^ARRAY\[(.*?)\]\s+OF\s+", r["type"])
        if m:
            dims[r["name"]] = m.group(1)

    dropped = {r["name"] for r in rows
               if r["direction"] == "INOUT"
               and any(n.startswith(r["name"] + "[].") for n in names)}

    kept = []
    for r in rows:
        if r["name"] in dropped:
            continue
        for c in dropped:
            if r["name"].startswith(c + "[].") and c in dims:
                r["type"] = "ARRAY[%s] OF %s" % (dims[c], r["type"])
                break
        kept.append(r)
    return kept


def normalize(task_card: dict) -> dict:
    tid = task_card["task_id"]
    rows = _flatten(tid, task_card["io_table"])
    rows = _drop_containers(rows)

    for r in rows:
        if r["direction"] == "INOUT":
            r["direction"] = "IN"      # 余下的 INOUT 当输入用

    return {"task_id": tid, "io": rows}


def dump(task_card: dict, out_dir: str) -> Path:
    """task_card 是已解析的 dict（yaml/json 均可）。"""
    fixture = normalize(task_card)
    out = Path(out_dir) / f"{fixture['task_id']}.io.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(fixture, ensure_ascii=False, indent=2), encoding="utf-8")
    return out

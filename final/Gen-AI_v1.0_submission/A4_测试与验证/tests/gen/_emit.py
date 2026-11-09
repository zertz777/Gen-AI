"""用例 CSV 的最小生成工具，供 gen_*.py 使用。

    from _emit import Case, write_cases
    c = Case("P05-01", "K1;K2", "一句话目的")
    c.add(ins, outs)          # cycle 自动递增，第一条必须是 0
    c.span(250, ins, outs)    # 连续铺 250 拍
    write_cases(out_csv, fixture_json, [c.dict(), ...])

列顺序与字面量格式完全按 tests/cases/_fixtures/<题号>.io.json 来，
写出来的文件可以直接被 runner/case_loader.py 读。
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

META = ["case_id", "cycle", "spec_refs", "purpose", "category"]

# 用例类别（任务书 T4.2：正常 / 边界 / 异常 / 安全 四类必须齐）
CATEGORIES = ("正常", "边界", "异常", "安全")

# 关键词优先级：安全 > 异常 > 边界 > 正常。
# 一条用例同时沾几类时，取「最需要被单独证明」的那一类。
_RULES = [
    ("安全", ("安全", "急停", "互斥", "不得", "禁止", "优先", "保护", "联锁",
              "锁定", "拒绝", "让位", "冻结")),
    ("异常", ("异常", "故障", "非法", "无效", "错误", "超时", "断线", "越界",
              "报 ", "16#8", "失配")),
    ("边界", ("边界", "恰好", "阈值", "上限", "下限", "极限", "临界",
              "满 5", "满 2", "满 3", "满 30", "满 60", "到点", "死区")),
]


def classify(purpose: str) -> str:
    """按目的文本猜类别；生成器可显式覆盖。

    目的以「安全：」「边界：」「异常：」开头时直接采信作者标注，
    否则按关键词优先级 安全 > 异常 > 边界 > 正常 推断。
    """
    for cat in CATEGORIES:
        if purpose.startswith(cat):
            return cat
    for cat, words in _RULES:
        if any(w in purpose for w in words):
            return cat
    return "正常"


def fmt(v, typ: str) -> str:
    if isinstance(v, str) and v == "X":
        return "X"
    if typ.startswith("ARRAY"):
        et = typ.split(" OF ", 1)[1]
        return "[" + ",".join(fmt(x, et) for x in v) + "]"
    if typ == "BOOL":
        return "TRUE" if v else "FALSE"
    if typ == "WORD":
        return "16#%04X" % int(v)
    if typ == "DWORD":
        return "16#%08X" % int(v)
    if typ in ("TIME", "LTIME"):
        return "T#%dms" % int(v)
    if typ.startswith("STRING"):
        return '"%s"' % v
    if typ.startswith("ST_") or typ == "VARIANT":
        return json.dumps(v, ensure_ascii=False)
    if typ in ("REAL", "LREAL"):
        return repr(float(v))
    return str(v)


class Case:
    def __init__(self, case_id: str, refs: str, purpose: str,
                 category: str | None = None):
        self.case_id = case_id
        self.refs = refs
        self.purpose = purpose
        self.category = category or classify(purpose)
        if self.category not in CATEGORIES:
            raise ValueError("%s 的 category 非法：%r" % (case_id, self.category))
        self.rows = []

    def add(self, ins: dict, outs: dict) -> "Case":
        self.rows.append({"cycle": len(self.rows), "in": ins, "out": outs})
        return self

    def span(self, n: int, ins: dict, outs: dict) -> "Case":
        for _ in range(n):
            self.add(ins, outs)
        return self

    def dict(self) -> dict:
        return {"case_id": self.case_id, "refs": self.refs,
                "purpose": self.purpose, "category": self.category,
                "rows": self.rows}


def write_cases(csv_path, fixture_path, cases) -> Path:
    fx = json.loads(Path(fixture_path).read_text(encoding="utf-8"))
    ins = [r["name"] for r in fx["io"] if r["direction"] == "IN"]
    outs = [r["name"] for r in fx["io"] if r["direction"] == "OUT"]
    types = {r["name"]: r["type"] for r in fx["io"]}

    path = Path(csv_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(META + ins + outs)
        for case in cases:
            for i, row in enumerate(case["rows"]):
                if row["cycle"] != i:
                    raise ValueError("%s 的 cycle 不连续" % case["case_id"])
                head = (i == 0)
                w.writerow([case["case_id"], row["cycle"],
                            case["refs"] if head else "",
                            case["purpose"] if head else "",
                            case["category"] if head else ""]
                           + [fmt(row["in"][n], types[n]) for n in ins]
                           + [fmt(row["out"][n], types[n]) for n in outs])
    return path

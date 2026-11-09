"""读用例 CSV，校验 8 字段与字面量。

规范见 tests/cases/_schema.md。
"""
from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass
from pathlib import Path

DONT_CARE = "X"
META_COLS = ("case_id", "cycle", "spec_refs", "purpose", "category")
CATEGORIES = ("正常", "边界", "异常", "安全")

_INT_TYPES = {"INT", "DINT", "SINT", "USINT", "UINT", "UDINT", "WORD", "DWORD"}
_TIME_UNITS = {"h": 3_600_000.0, "m": 60_000.0, "s": 1_000.0, "ms": 1.0}
_TIME_RE = re.compile(r"(\d+(?:\.\d+)?)(ms|h|m|s)")


class CaseError(Exception):
    pass


@dataclass
class Case:
    case_id: str
    spec_refs: list
    purpose: str
    cycles: list          # [{"cycle": 0, "in": {...}, "out": {...}}, ...]
    category: str = ""    # 正常 / 边界 / 异常 / 安全（缺列时为空）


def load_io(io_path):
    """fixture 格式：{"task_id": "...", "io": [{"name","direction","type"}, ...]}"""
    d = json.loads(Path(io_path).read_text(encoding="utf-8"))
    ins, outs = {}, {}
    for row in d["io"]:
        if row["direction"] in ("IN", "INOUT"):
            ins[row["name"]] = row["type"]
        else:
            outs[row["name"]] = row["type"]
    return d["task_id"], ins, outs


def parse_value(raw, typ):
    s = (raw or "").strip()
    if s == DONT_CARE:
        return DONT_CARE
    if s == "":
        raise CaseError("空单元格")
    if typ == "BOOL":
        if s.upper() not in ("TRUE", "FALSE"):
            raise CaseError("BOOL 列出现 %r" % raw)
        return s.upper() == "TRUE"
    if typ in _INT_TYPES:
        return int(s[3:], 16) if s.startswith("16#") else int(s, 10)
    if typ in ("REAL", "LREAL"):
        return float(s)
    if typ in ("TIME", "LTIME"):
        body = s.split("#", 1)[1] if "#" in s else s
        total = sum(float(n) * _TIME_UNITS[u] for n, u in _TIME_RE.findall(body))
        if total == 0 and body.strip() not in ("0", "0ms", "0s"):
            raise CaseError("时间字面量无法解析：%r" % raw)
        return total
    if typ.startswith("STRING"):
        return s.strip('"')
    if typ.startswith("ARRAY") or typ.startswith("ST_") or typ == "VARIANT":
        # 用例里沿用 ST 写法 TRUE/FALSE，转成 JSON 的 true/false 再解析
        norm = re.sub(r"\bTRUE\b", "true", s, flags=re.I)
        norm = re.sub(r"\bFALSE\b", "false", norm, flags=re.I)
        try:
            return json.loads(norm)
        except json.JSONDecodeError as e:
            raise CaseError("复杂类型需要 JSON 字面量：%r (%s)" % (raw, e)) from e
    raise CaseError("未知类型 %r" % typ)


def load_cases(csv_path, io_path):
    task_id, ins, outs = load_io(io_path)
    with open(csv_path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        header = reader.fieldnames or []
        rows = list(reader)

    # 校验 1/2：输入输出列必须齐全，且不许有未知列
    for name in ins:
        if name not in header:
            raise CaseError("缺输入列 %r（fixture 里有、CSV 里没有）" % name)
    for name in outs:
        if name not in header:
            raise CaseError("缺输出列 %r（fixture 里有、CSV 里没有）" % name)
    unknown = [c for c in header if c not in META_COLS and c not in ins and c not in outs]
    if unknown:
        raise CaseError("未知列 %r（拼写或大小写与 fixture 不一致？）" % (unknown,))

    order, groups = [], {}
    for r in rows:
        cid = r["case_id"]
        if cid not in groups:
            groups[cid] = []
            order.append(cid)
        groups[cid].append(r)

    cases = []
    for cid in order:
        raw = groups[cid]
        nums = [int(r["cycle"]) for r in raw]
        # 校验 3：cycle 必须 0..n 连续
        if nums != list(range(len(nums))):
            raise CaseError("%s 的 cycle 不连续：%r" % (cid, nums))
        head = raw[0]
        # 校验 4：初态行必须有 purpose / spec_refs
        if not (head["purpose"] or "").strip():
            raise CaseError("%s 的 cycle=0 行缺 purpose" % cid)
        refs = [x.strip() for x in (head["spec_refs"] or "").split(";") if x.strip()]
        if not refs:
            raise CaseError("%s 的 cycle=0 行缺 spec_refs" % cid)
        # 校验 4b：category 可选，但写了就必须是四类之一
        cat = (head.get("category") or "").strip()
        if cat and cat not in CATEGORIES:
            raise CaseError("%s 的 category 非法：%r" % (cid, cat))

        cycles = []
        for r in raw:
            vals = {"cycle": int(r["cycle"])}
            vals["in"] = {k: parse_value(r[k], ins[k]) for k in ins}
            vals["out"] = {k: parse_value(r[k], outs[k]) for k in outs}
            # 校验 6：X 不许出现在输入列
            bad = [k for k, v in vals["in"].items() if v == DONT_CARE]
            if bad:
                raise CaseError("%s 第 %d 拍的输入列出现 X：%r" % (cid, vals["cycle"], bad))
            cycles.append(vals)

        cases.append(Case(case_id=cid, spec_refs=refs,
                          purpose=head["purpose"], cycles=cycles,
                          category=cat))
    return task_id, cases

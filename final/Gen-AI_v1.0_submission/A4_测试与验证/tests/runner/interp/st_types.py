"""IEC 61131-3 类型系统的最小实现（解释器专用）。

只覆盖题目里实际出现的类型：

    BOOL / SINT..UDINT / WORD..LWORD / BYTE / REAL / LREAL / TIME / LTIME /
    STRING / ARRAY[lo..hi] OF T / STRUCT

刻意不做（写进 docs/interp.md 的局限）：VARIANT、指针、REF、FB 实例数组、
直接地址 `AT %I*`。

值的 Python 表示：
    BOOL -> bool     整数族 -> int     REAL -> float
    TIME -> float（毫秒）              STRING -> str
    ARRAY -> list     STRUCT -> dict（键为大写字段名）
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass

# ---------------------------------------------------------------- 类型名集合

INT_TYPES = {
    "SINT", "INT", "DINT", "LINT",
    "USINT", "UINT", "UDINT", "ULINT",
    "WORD", "DWORD", "LWORD", "BYTE",
}
UNSIGNED_BITS = {
    "USINT": 8, "UINT": 16, "UDINT": 32, "ULINT": 64,
    "WORD": 16, "DWORD": 32, "LWORD": 64, "BYTE": 8,
}
REAL_TYPES = {"REAL", "LREAL"}
TIME_TYPES = {"TIME", "LTIME"}
STRING_TYPES = {"STRING", "WSTRING"}
BOOL_TYPES = {"BOOL"}
#: 解释器内置的 FB（声明成这些类型的变量是"实例"，不是值）
BUILTIN_FBS = {"TON", "TOF", "TP", "R_TRIG", "F_TRIG", "CTU", "CTD"}

SCALAR_TYPES = (BOOL_TYPES | INT_TYPES | REAL_TYPES | TIME_TYPES | STRING_TYPES)

_ARRAY_RE = re.compile(
    r"^ARRAY\s*\[\s*(?:(-?\d+)\s*\.\.\s*(-?\d+)|\*)\s*\]\s*OF\s+(.+)$", re.I)
_STRING_RE = re.compile(r"^(W?STRING)\s*([\[(]\s*\d+\s*[\])])?$", re.I)
_TIME_UNITS = {"ms": 1.0, "d": 86_400_000.0, "h": 3_600_000.0, "m": 60_000.0, "s": 1_000.0}
_TIME_RE = re.compile(r"(\d+(?:\.\d+)?)(ms|d|h|m|s)", re.I)


class StTypeError(Exception):
    """类型/字面量不合法（属于输入数据问题，调用方应判 error 而不是 fail）。"""


# ---------------------------------------------------------------- 类型描述

@dataclass(frozen=True)
class TypeSpec:
    """类型描述。

    kind:
        scalar  -> name 是标量类型名（大写）
        array   -> elem 是元素类型，lo/hi 是下标闭区间；dynamic=True 表示
                   `ARRAY[*]`（变长数组，长度由输入值决定，见 P08）
        struct  -> name 是结构体名（大写），字段表在 StructTable 里
        fb      -> name 是内置 FB 名（TON/TOF/R_TRIG/...）
    """
    kind: str
    name: str = ""
    elem: "TypeSpec | None" = None
    lo: int = 0
    hi: int = 0
    dynamic: bool = False

    def __str__(self):
        if self.kind == "array":
            if self.dynamic:
                return "ARRAY[*] OF %s" % self.elem
            return "ARRAY[%d..%d] OF %s" % (self.lo, self.hi, self.elem)
        return self.name

    @property
    def length(self):
        return 0 if self.dynamic else self.hi - self.lo + 1


#: 结构体表：大写类型名 -> [(字段名原始写法, TypeSpec), ...]（保持声明顺序）
#: 字段名保留原始大小写，因为 actual CSV 的列名（如 `pumpGroup[].RunComd`）
#: 要与 fixture 逐字一致；查找时再按大小写不敏感匹配。
StructTable = dict


def struct_fields(structs: StructTable, name) -> list:
    fields = structs.get(str(name).upper())
    if fields is None:
        raise StTypeError("未定义的结构体：%s（已知：%s）"
                          % (name, ", ".join(sorted(structs)) or "无"))
    return fields


def field_of(fields, name):
    """按大小写不敏感在字段表里找 -> (原始字段名, TypeSpec)。"""
    key = str(name).upper()
    for fname, fts in fields:
        if fname.upper() == key:
            return fname, fts
    raise StTypeError("结构体没有字段 %r" % name)


def normalize_type_text(text):
    return re.sub(r"\s+", " ", (text or "").strip())


def parse_type(text, structs: StructTable) -> TypeSpec:
    """把声明里的类型写成 TypeSpec。`structs` 必须先解析好（TYPE 块在 FB 之前）。"""
    s = normalize_type_text(text).upper()
    if not s:
        raise StTypeError("空的类型声明")

    m = _ARRAY_RE.match(s)
    if m:
        elem = parse_type(m.group(3), structs)
        if m.group(1) is None:
            return TypeSpec("array", elem=elem, lo=1, hi=0, dynamic=True)
        lo, hi = int(m.group(1)), int(m.group(2))
        if hi < lo:
            raise StTypeError("ARRAY 下标区间非法：%d..%d" % (lo, hi))
        return TypeSpec("array", elem=elem, lo=lo, hi=hi)

    m = _STRING_RE.match(s)
    if m:
        return TypeSpec("scalar", name=m.group(1))
    if s in STRING_TYPES:
        return TypeSpec("scalar", name=s)

    if s in SCALAR_TYPES:
        return TypeSpec("scalar", name=s)
    if s in BUILTIN_FBS:
        return TypeSpec("fb", name=s)
    if s in structs:
        return TypeSpec("struct", name=s)
    raise StTypeError("不支持的类型：%r（已知结构体：%s）"
                      % (text, ", ".join(sorted(structs)) or "无"))


# ---------------------------------------------------------------- 默认值与强制转换

def default_value(ts: TypeSpec, structs: StructTable):
    """IEC 的零值：BOOL=FALSE、数值=0、TIME=0 ms、ARRAY 逐元素、STRUCT 逐字段。"""
    if ts.kind == "array":
        return [default_value(ts.elem, structs) for _ in range(ts.length)]
    if ts.kind == "struct":
        return {fname: default_value(fts, structs)
                for fname, fts in struct_fields(structs, ts.name)}
    if ts.kind == "fb":
        raise StTypeError("FB 实例不能用默认值构造：%s" % ts.name)
    if ts.name in BOOL_TYPES:
        return False
    if ts.name in REAL_TYPES:
        return 0.0
    if ts.name in TIME_TYPES:
        return 0.0
    if ts.name in STRING_TYPES:
        return ""
    return 0


def coerce(value, ts: TypeSpec, structs: StructTable):
    """把计算/解析出来的值强制成声明类型（INT/INT 的除法已在求值处改成整数除法）。"""
    if ts.kind == "array":
        if not isinstance(value, (list, tuple)):
            raise StTypeError("%s 需要数组值，得到 %r" % (ts, value))
        if not ts.dynamic and len(value) != ts.length:
            raise StTypeError("%s 需要 %d 个元素，得到 %d" % (ts, ts.length, len(value)))
        return [coerce(v, ts.elem, structs) for v in value]
    if ts.kind == "struct":
        fields = struct_fields(structs, ts.name)
        if not isinstance(value, dict):
            raise StTypeError("%s 需要结构体值，得到 %r" % (ts, value))
        given = {str(k).upper(): v for k, v in value.items()}
        out = {}
        for fname, fts in fields:
            key = fname.upper()
            if key not in given:
                raise StTypeError("%s 缺字段 %s" % (ts, fname))
            out[fname] = coerce(given[key], fts, structs)
        return out
    if ts.kind == "fb":
        raise StTypeError("不能给 FB 实例赋值：%s" % ts.name)

    if ts.name in BOOL_TYPES:
        return bool(value)
    if ts.name in REAL_TYPES:
        return float(value)
    if ts.name in TIME_TYPES:
        return float(value)
    if ts.name in STRING_TYPES:
        return "" if value is None else str(value)
    iv = int(value)
    bits = UNSIGNED_BITS.get(ts.name)
    if bits:
        iv &= (1 << bits) - 1
    return iv


# ---------------------------------------------------------------- 字面量

def parse_time_ms(text) -> float:
    """`T#500ms` / `TIME#1h30m` / `LTIME#2s` / `500` -> 毫秒。"""
    s = str(text).strip()
    if not s:
        raise StTypeError("空的时间字面量")
    if "#" in s:
        head, s = s.split("#", 1)
        if head.strip().upper() not in ("T", "TIME", "LTIME", "TIME_OF_DAY", "TOD"):
            raise StTypeError("不是时间字面量：%r" % text)
    items = _TIME_RE.findall(s)
    if not items:
        try:
            return float(s)
        except ValueError:
            raise StTypeError("时间字面量无法解析：%r" % text) from None
    return sum(float(n) * _TIME_UNITS[u.lower()] for n, u in items)


def parse_literal(raw, ts: TypeSpec, structs: StructTable):
    """把 CSV / 用例里的字面量解析成声明类型的值。

    与 `runner/case_loader.parse_value` 保持同一套写法（BOOL 只认 TRUE/FALSE、
    WORD 认 16#xxxx、TIME 认 T#500ms、ARRAY/STRUCT 用 JSON）。
    """
    s = "" if raw is None else str(raw).strip()
    if s == "":
        raise StTypeError("空单元格")
    if s.upper() == "X":
        raise StTypeError("X 不能作为输入值")

    if ts.kind in ("array", "struct"):
        return coerce(_parse_jsonish(s), ts, structs)
    if ts.kind == "fb":
        raise StTypeError("FB 实例不能从字面量赋值：%s" % ts.name)

    if ts.name in BOOL_TYPES:
        if s.upper() not in ("TRUE", "FALSE"):
            raise StTypeError("BOOL 列出现 %r" % raw)
        return s.upper() == "TRUE"
    if ts.name in REAL_TYPES:
        return float(s)
    if ts.name in TIME_TYPES:
        return parse_time_ms(s)
    if ts.name in STRING_TYPES:
        return s.strip('"\'')
    # 整数族：16# / 10# / 8# / 2# / 十进制（与 case_loader 一致，至少支持 16#）
    m = re.match(r"^(\d+)#([0-9A-Fa-f_]+)$", s)
    if m:
        return int(m.group(2).replace("_", ""), int(m.group(1)))
    return int(s, 10)


def _parse_jsonish(s):
    norm = re.sub(r"\bTRUE\b", "true", s, flags=re.I)
    norm = re.sub(r"\bFALSE\b", "false", norm, flags=re.I)
    try:
        return json.loads(norm)
    except json.JSONDecodeError as e:
        raise StTypeError("复杂类型需要 JSON 字面量：%r (%s)" % (s, e)) from e


# ---------------------------------------------------------------- 类型转换函数
#: IEC 的 `X_TO_Y` 系列。TIME / LTIME 在解释器里都是"毫秒浮点"，
#: 所以 TIME_TO_LTIME 是一次无损的透传（单位一致，只差精度类型）。
CONVERSION_TARGETS = (
    INT_TYPES | REAL_TYPES | TIME_TYPES | STRING_TYPES | BOOL_TYPES
)


def split_conversion(name):
    """`TIME_TO_LTIME` -> ("TIME", "LTIME")；不是转换函数返回 None。"""
    txt = str(name).upper()
    if "_TO_" not in txt:
        return None
    src, dst = txt.split("_TO_", 1)
    if dst not in CONVERSION_TARGETS:
        return None
    return src, dst


def convert_to(value, target):
    """按目标类型做 IEC 隐式允许的显式转换（不做溢出告警，超出部分按位宽截断）。"""
    target = target.upper()
    if target in BOOL_TYPES:
        return bool(value)
    if target in REAL_TYPES:
        return float(value)
    if target in TIME_TYPES:
        return float(value)
    if target in STRING_TYPES:
        return str(value)
    iv = int(value)
    bits = UNSIGNED_BITS.get(target)
    if bits:
        iv &= (1 << bits) - 1
    return iv


# ---------------------------------------------------------------- 回写 CSV

def format_value(value, ts: TypeSpec, structs: StructTable) -> str:
    """按用例规范回写成 actual CSV 单元格。"""
    if ts.kind in ("array", "struct"):
        return _json_st(_native(value, ts, structs))
    if ts.kind == "fb":
        raise StTypeError("FB 实例不能写进 actual CSV：%s" % ts.name)
    if ts.name in BOOL_TYPES:
        return "TRUE" if value else "FALSE"
    if ts.name in REAL_TYPES:
        return repr(float(value))
    if ts.name in TIME_TYPES:
        return "T#%sms" % _fmt_ms(value)
    if ts.name in STRING_TYPES:
        return '"%s"' % value
    iv = int(value)
    return _int_text(iv, ts.name)


def _native(value, ts: TypeSpec, structs: StructTable):
    """数组/结构体单元格要先转成 JSON 原生值，否则会被 json 当成字符串再包一层引号。"""
    if ts.kind == "array":
        return [_native(v, ts.elem, structs) for v in value]
    if ts.kind == "struct":
        return {f: _native(value.get(f), fts, structs)
                for f, fts in struct_fields(structs, ts.name)}
    if ts.kind == "fb":
        raise StTypeError("FB 实例不能写进 actual CSV：%s" % ts.name)
    if ts.name in BOOL_TYPES:
        return bool(value)
    if ts.name in REAL_TYPES:
        return float(value)
    if ts.name in TIME_TYPES:
        return "T#%sms" % _fmt_ms(value)
    if ts.name in STRING_TYPES:
        return str(value)
    return _int_text(int(value), ts.name)


def _int_text(iv, name):
    if name == "WORD":
        return "16#%04X" % (iv & 0xFFFF)
    if name == "DWORD":
        return "16#%08X" % (iv & 0xFFFFFFFF)
    if name == "BYTE":
        return "16#%02X" % (iv & 0xFF)
    return str(iv)


def _fmt_ms(ms):
    ms = float(ms)
    return str(int(round(ms))) if abs(ms - round(ms)) < 1e-9 else ("%g" % ms)


def _json_st(obj):
    """JSON 里保留 ST 风格的真假值（case_loader 两种都认）。"""
    txt = json.dumps(obj, ensure_ascii=False)
    return txt.replace("true", "TRUE").replace("false", "FALSE")

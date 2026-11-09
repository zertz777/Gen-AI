"""运行时状态：变量表 + 内置 FB 实例（TON / TOF / R_TRIG / F_TRIG / CTU / CTD）。

计时语义按全组口径 D-02 / D-11：
- 一个扫描周期 **20 ms**（可由 --cycle-ms 覆盖）；
- 计时**同一拍先累加后判定**：`ET += 20` 之后才比 `ET >= PT`，
  去抖满额那一拍就动作，不用等下一拍。

这条与 `tests/gen/gen_P05.py`（5 s ÷ 20 ms = 250 拍）一致；差一拍整题都会判 fail。
"""
from __future__ import annotations

from .st_types import (BOOL_TYPES, INT_TYPES, StTypeError, TypeSpec, default_value,
                    field_of, struct_fields)


def get_field(container, name):
    """按大小写不敏感读结构体字段（字段表里保留的是声明时的原始大小写）。"""
    if not isinstance(container, dict):
        raise StTypeError("不是结构体，不能取字段 %r" % name)
    key = str(name).upper()
    for k in container:
        if k.upper() == key:
            return container[k]
    raise StTypeError("结构体没有字段 %r（现有：%s）" % (name, ", ".join(container)))


def set_field(container, name, value):
    """按大小写不敏感写结构体字段；字段必须已声明。"""
    if not isinstance(container, dict):
        raise StTypeError("不是结构体，不能写字段 %r" % name)
    key = str(name).upper()
    for k in container:
        if k.upper() == key:
            container[k] = value
            return
    raise StTypeError("结构体没有字段 %r（现有：%s）" % (name, ", ".join(container)))


class FbInstance:
    """内置 FB 实例：只有"这次调用传了哪些参数"才更新对应状态。"""

    def __init__(self, kind, cycle_ms=20.0):
        self.kind = kind.upper()
        self.cycle_ms = float(cycle_ms)
        self.name = self.kind
        self._init_state()

    def _init_state(self):
        k = self.kind
        if k in ("TON", "TOF", "TP"):
            self.inp, self.pt, self.et, self.q = False, 0.0, 0.0, False
        elif k in ("R_TRIG", "F_TRIG"):
            self.prev, self.q = False, False
        elif k in ("CTU", "CTD"):
            self.cv, self.pv, self.q = 0, 0, False
            self.prev_cu = False
            self.prev_cd = False
            self.r = False
            self.ld = False
        else:
            raise StTypeError("不支持的内置 FB：%s" % self.kind)

    # ---- 调用 ----
    def call(self, args: dict):
        k = self.kind
        if k == "TON":
            self._ton(args)
        elif k == "TOF":
            self._tof(args)
        elif k == "TP":
            self._tp(args)
        elif k == "R_TRIG":
            clk = bool(args.get("CLK", self.prev))
            self.q = clk and not self.prev
            self.prev = clk
        elif k == "F_TRIG":
            clk = bool(args.get("CLK", self.prev))
            self.q = (not clk) and self.prev
            self.prev = clk
        elif k == "CTU":
            self._ctu(args)
        elif k == "CTD":
            self._ctd(args)

    def _ton(self, args):
        if "IN" in args:
            self.inp = bool(args["IN"])
        if "PT" in args:
            self.pt = float(args["PT"] or 0.0)
        if self.inp:
            self.et += self.cycle_ms          # D-11：先累加
            self.q = self.et >= self.pt       # 再判定
        else:
            self.et = 0.0
            self.q = False

    def _tof(self, args):
        if "IN" in args:
            self.inp = bool(args["IN"])
        if "PT" in args:
            self.pt = float(args["PT"] or 0.0)
        if self.inp:
            self.et = 0.0
            self.q = True
        else:
            self.et += self.cycle_ms
            self.q = self.et < self.pt

    def _tp(self, args):
        """脉冲定时器：IN 上升沿起跳，PT 内 Q 保持。"""
        if "IN" in args:
            new_in = bool(args["IN"])
        else:
            new_in = self.inp
        if "PT" in args:
            self.pt = float(args["PT"] or 0.0)
        if new_in and not self.inp:
            self.et = 0.0
            self.q = True
        elif self.q and self.et < self.pt:
            self.et += self.cycle_ms
            self.q = self.et < self.pt
        else:
            self.q = False
        self.inp = new_in

    def _ctu(self, args):
        cu = bool(args.get("CU", self.prev_cu))
        r = bool(args.get("R", False))
        if "PV" in args:
            self.pv = int(args["PV"] or 0)
        if r:
            self.cv = 0
            self.q = False
        elif cu and not self.prev_cu:
            self.cv += 1
            self.q = self.cv >= self.pv
        self.prev_cu = cu

    def _ctd(self, args):
        cd = bool(args.get("CD", self.prev_cd))
        ld = bool(args.get("LD", False))
        if "PV" in args:
            self.pv = int(args["PV"] or 0)
        if ld:
            self.cv = self.pv
            self.q = False
        elif cd and not self.prev_cd:
            self.cv -= 1
            self.q = self.cv <= 0
        self.prev_cd = cd

    # ---- 读字段 ----
    def get(self, field):
        f = field.upper()
        if f in ("Q",):
            return self.q
        if f in ("ET",):
            return getattr(self, "et", 0.0)
        if f in ("CV",):
            return getattr(self, "cv", 0)
        raise StTypeError("%s 没有输出字段 %r（只有 Q / ET / CV）" % (self.kind, field))

    def field_type(self, field):
        f = field.upper()
        if f == "Q":
            return TypeSpec("scalar", name="BOOL")
        if f == "ET":
            return TypeSpec("scalar", name="TIME")
        if f == "CV":
            return TypeSpec("scalar", name="INT")
        raise StTypeError("%s 没有输出字段 %r" % (self.kind, field))


class VarStore:
    """变量表：键一律大写（ST 标识符大小写不敏感），另存原始名用于回写 CSV。"""

    def __init__(self):
        self.values = {}
        self.types = {}
        self.names = {}

    def declare(self, name, ts: TypeSpec, value, structs):
        key = name.upper()
        if key in self.values:
            raise StTypeError("变量重复声明：%s" % name)
        if ts.kind == "fb":
            self.values[key] = FbInstance(ts.name)
        else:
            self.values[key] = default_value(ts, structs) if value is None else value
        self.types[key] = ts
        self.names[key] = name
        return key

    def lookup(self, name) -> str:
        key = name.upper()
        if key not in self.values:
            raise StTypeError("未声明的变量：%s" % name)
        return key

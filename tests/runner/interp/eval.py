"""解释执行：把 AST 按扫描周期跑起来。

对外只暴露 `Interpreter`：

    itp = Interpreter.from_source(open("refimpl/P03.st").read(), cycle_ms=20)
    itp.set_inputs({"Value": "12", "hiLevel": "10", ...})   # cycle=0 初态
    for each cycle: itp.set_inputs(...); rows = itp.snapshot()

语义要点（与 D-02 / D-11 对齐，写进 docs/interp.md）：

1. 一拍 = 20 ms；FB 体每拍执行一次；
2. `cycle=0` 只设初值、不执行 FB 体（与 `tests/cases/_schema.md` §2 一致）；
3. 输出在每拍执行完 FB 体后采样；
4. 计时先累加后判定（见 state.FbInstance）；
5. 边沿（R_TRIG/F_TRIG）用"上一拍的 CLK"作为记忆，初值为 FALSE。

安全阀：单拍语句数超过 MAX_STEPS 或单循环超过 MAX_LOOP 直接抛错，
不把死循环拖成 900 s 的超时——那样会被记成 timeout，污染统计口径。
"""
from __future__ import annotations

from typing import Any

from .parser import (Assign, Binary, CallStmt, CaseStmt, ExitStmt, FieldRef, ForStmt,
                     FuncCall, IfStmt, IndexRef, Lit, ParseError, Program, RepeatStmt,
                     ReturnStmt, Unary, VarRef, WhileStmt, parse)
from .state import FbInstance, VarStore, get_field, set_field
from .st_types import (BOOL_TYPES, INT_TYPES, StTypeError, TypeSpec, coerce,
                       convert_to, default_value, field_of, format_value,
                       parse_literal, split_conversion, struct_fields)

MAX_STEPS = 200_000
MAX_LOOP = 100_000


class InterpError(Exception):
    """解释执行失败（语法/类型/未定义变量/死循环兜底）。"""


class _ReturnSignal(Exception):
    pass


class _ExitSignal(Exception):
    pass


class Interpreter:
    def __init__(self, program: Program, block: str | None = None, cycle_ms: float = 20.0):
        self.prog = program
        self.structs = program.structs
        self.cycle_ms = float(cycle_ms)
        self.block = self._choose_block(block)
        self.store = VarStore()
        self.input_decls, self.output_decls = [], []
        self._steps = 0
        self._declare_vars()
        self._output_specs = self._build_output_specs()

    @classmethod
    def from_source(cls, src: str, block: str | None = None, cycle_ms: float = 20.0):
        try:
            prog = parse(src)
        except ParseError as e:
            raise InterpError(str(e)) from e
        return cls(prog, block=block, cycle_ms=cycle_ms)

    # ------------------------------------------------------------ 初始化
    def _choose_block(self, name):
        blocks = self.prog.blocks
        if not blocks:
            raise InterpError("源码里没有 FUNCTION_BLOCK / PROGRAM")
        if name:
            key = name.upper()
            if key not in blocks:
                raise InterpError("找不到块 %s（现有：%s）"
                                  % (name, ", ".join(sorted(blocks))))
            return blocks[key]
        if len(blocks) == 1:
            return blocks[next(iter(blocks))]
        raise InterpError("源码里有多个块（%s），请用 --block 指定"
                          % ", ".join(sorted(blocks)))

    def _declare_vars(self):
        pending = []
        for decl in self.block.vars:
            ts = decl.ts
            if ts.kind == "fb":
                value = FbInstance(ts.name, self.cycle_ms)
            else:
                value = None
            try:
                key = self.store.declare(decl.name, ts, value, self.structs)
            except StTypeError as e:
                raise InterpError("声明 %s 失败：%s" % (decl.name, e)) from e
            if decl.scope in ("input", "inout"):
                self.input_decls.append(decl)
            if decl.scope in ("output", "inout"):
                self.output_decls.append(decl)
            if decl.init is not None:
                pending.append((decl, key))
        for decl, key in pending:
            try:
                val = self._eval(decl.init)
                self.store.values[key] = coerce(val, decl.ts, self.structs)
            except (StTypeError, InterpError) as e:
                raise InterpError("初始值 %s 求值失败：%s" % (decl.name, e)) from e

    def _build_output_specs(self):
        """[(CSV 列名, TypeSpec, 取值路径)]；列名与 fixture 逐字一致。"""
        specs = []
        for decl in self.output_decls:
            ts = decl.ts
            if ts.kind == "fb":
                continue
            if ts.kind == "array" and ts.elem.kind == "struct":
                for fname, fts in struct_fields(self.structs, ts.elem.name):
                    # 一列装所有元素的同一字段，类型要升一维（_schema.md §2.2）
                    col_ts = TypeSpec("array", elem=fts, lo=ts.lo, hi=ts.hi,
                                      dynamic=ts.dynamic)
                    specs.append(("%s[].%s" % (decl.name, fname), col_ts,
                                  ("arr_field", decl.name.upper(), fname)))
            elif ts.kind == "struct":
                for fname, fts in struct_fields(self.structs, ts.name):
                    specs.append(("%s.%s" % (decl.name, fname), fts,
                                  ("field", decl.name.upper(), fname)))
            else:
                specs.append((decl.name, ts, ("var", decl.name.upper())))
        return specs

    # ------------------------------------------------------------ 输入
    def set_inputs(self, mapping: dict):
        for col, raw in (mapping or {}).items():
            if col is None:
                continue
            self._set_input(str(col).strip(), raw)

    def _set_input(self, col, raw):
        try:
            if "[]." in col:
                base, field = col.split("[].", 1)
                key = self.store.lookup(base)
                ts = self.store.types[key]
                if not (ts.kind == "array" and ts.elem.kind == "struct"):
                    raise StTypeError("%s 不是结构体数组，不能写 %s" % (base, col))
                fields = struct_fields(self.structs, ts.elem.name)
                fname, fts = field_of(fields, field)
                list_ts = TypeSpec("array", elem=fts, lo=ts.lo, hi=ts.hi,
                                   dynamic=ts.dynamic)
                values = parse_literal(raw, list_ts, self.structs) \
                    if isinstance(raw, str) else coerce(raw, list_ts, self.structs)
                elems = self.store.values[key]
                if ts.dynamic and len(elems) != len(values):
                    elems = [default_value(ts.elem, self.structs) for _ in values]
                    self.store.values[key] = elems
                if len(elems) != len(values):
                    raise StTypeError("%s 元素个数 %d 与已写入的 %d 不一致"
                                      % (col, len(values), len(elems)))
                for elem, val in zip(elems, values):
                    set_field(elem, fname, val)
                return
            if "." in col:
                base, field = col.split(".", 1)
                key = self.store.lookup(base)
                ts = self.store.types[key]
                if ts.kind != "struct":
                    raise StTypeError("%s 不是结构体，不能写 %s" % (base, col))
                fname, fts = field_of(struct_fields(self.structs, ts.name), field)
                val = parse_literal(raw, fts, self.structs) \
                    if isinstance(raw, str) else coerce(raw, fts, self.structs)
                set_field(self.store.values[key], fname, val)
                return
            key = self.store.lookup(col)
            ts = self.store.types[key]
            if ts.kind == "fb":
                raise StTypeError("%s 是 FB 实例，不能当输入" % col)
            val = parse_literal(raw, ts, self.structs) \
                if isinstance(raw, str) else coerce(raw, ts, self.structs)
            self.store.values[key] = val
        except StTypeError as e:
            raise InterpError("输入 %s 失败：%s" % (col, e)) from e

    # ------------------------------------------------------------ 执行
    def run_cycle(self):
        """执行一个扫描周期，返回 [(列名, TypeSpec, 值)]。"""
        self._steps = 0
        try:
            self._exec_body(self.block.body)
        except _ReturnSignal:
            pass
        except _ExitSignal:
            pass
        return self.snapshot()

    def snapshot(self):
        return [(col, ts, self._extract(path)) for col, ts, path in self._output_specs]

    def output_columns(self):
        return [col for col, _, _ in self._output_specs]

    def snapshot_text(self):
        """{列名: CSV 单元格文本}，直接可写 actual。"""
        return {col: format_value(val, ts, self.structs)
                for col, ts, val in self.snapshot()}

    def _extract(self, path):
        kind = path[0]
        if kind == "var":
            return self.store.values[path[1]]
        if kind == "field":
            return get_field(self.store.values[path[1]], path[2])
        if kind == "arr_field":
            return [get_field(el, path[2]) for el in self.store.values[path[1]]]
        raise InterpError("未知输出路径 %r" % (path,))

    def _tick(self, line=0):
        self._steps += 1
        if self._steps > MAX_STEPS:
            raise InterpError("第 %d 行附近：单个扫描周期执行超过 %d 条语句，疑似死循环"
                              % (line, MAX_STEPS))

    def _exec_body(self, body):
        for st in body:
            self._exec(st)

    def _exec(self, st):
        self._tick(getattr(st, "line", 0))
        if isinstance(st, Assign):
            cont, key, ts = self._resolve(st.target)
            try:
                cont[key] = coerce(self._eval(st.value), ts, self.structs)
            except StTypeError as e:
                raise InterpError("第 %d 行赋值失败：%s" % (st.line, e)) from e
            return
        if isinstance(st, IfStmt):
            for cond, body in st.branches:
                if self._truth(self._eval(cond)):
                    self._exec_body(body)
                    return
            self._exec_body(st.else_body)
            return
        if isinstance(st, CaseStmt):
            sel = self._eval(st.selector)
            for labels, body in st.branches:
                if any(self._eq(sel, lab) for lab in labels):
                    self._exec_body(body)
                    return
            self._exec_body(st.else_body)
            return
        if isinstance(st, ForStmt):
            self._exec_for(st)
            return
        if isinstance(st, WhileStmt):
            n = 0
            while self._truth(self._eval(st.cond)):
                self._exec_body(st.body)
                n += 1
                if n > MAX_LOOP:
                    raise InterpError("第 %d 行的 WHILE 超过 %d 次迭代" % (st.line, MAX_LOOP))
            return
        if isinstance(st, RepeatStmt):
            n = 0
            while True:
                self._exec_body(st.body)
                n += 1
                if self._truth(self._eval(st.cond)):
                    break
                if n > MAX_LOOP:
                    raise InterpError("第 %d 行的 REPEAT 超过 %d 次迭代" % (st.line, MAX_LOOP))
            return
        if isinstance(st, ReturnStmt):
            raise _ReturnSignal()
        if isinstance(st, ExitStmt):
            raise _ExitSignal()
        if isinstance(st, CallStmt):
            self._exec_call(st)
            return
        raise InterpError("未知语句 %r" % (st,))

    def _exec_for(self, st):
        key = self.store.lookup(st.var)
        ts = self.store.types[key]
        if not (ts.kind == "scalar" and ts.name in INT_TYPES):
            raise InterpError("FOR 的循环变量 %s 必须是整数类型" % st.var)
        start = int(self._eval(st.start))
        end = int(self._eval(st.end))
        step = int(self._eval(st.step))
        if step == 0:
            raise InterpError("第 %d 行：FOR 的 BY 不能为 0" % st.line)
        i, n = start, 0
        while (i <= end) if step > 0 else (i >= end):
            self.store.values[key] = i
            self._exec_body(st.body)
            i += step
            n += 1
            if n > MAX_LOOP:
                raise InterpError("第 %d 行的 FOR 超过 %d 次迭代" % (st.line, MAX_LOOP))

    def _exec_call(self, st):
        key = st.name.upper()
        inst = self.store.values.get(key)
        if isinstance(inst, FbInstance):
            args = {}
            for pname, expr in st.args:
                if pname is None:
                    raise InterpError("第 %d 行：FB 实例 %s 必须用具名参数（IN := ...）"
                                      % (st.line, st.name))
                args[pname.upper()] = self._eval(expr)
            try:
                inst.call(args)
            except StTypeError as e:
                raise InterpError("第 %d 行调用 %s 失败：%s" % (st.line, st.name, e)) from e
            return
        # 普通函数当语句调用：允许，返回值丢弃
        self._call_function(st.name, st.args, st.line)

    # ------------------------------------------------------------ 表达式
    def _eval(self, node):
        if isinstance(node, Lit):
            return node.value
        if isinstance(node, VarRef):
            key = node.name.upper()
            if key not in self.store.values:
                raise InterpError("第 %d 行：未声明的变量 %s" % (node.line, node.name))
            return self.store.values[key]
        if isinstance(node, FieldRef):
            base = self._eval(node.base)
            if isinstance(base, FbInstance):
                try:
                    return base.get(node.name)
                except StTypeError as e:
                    raise InterpError("第 %d 行：%s" % (node.line, e)) from e
            try:
                return get_field(base, node.name)
            except StTypeError as e:
                raise InterpError("第 %d 行：%s" % (node.line, e)) from e
        if isinstance(node, IndexRef):
            base = self._eval(node.base)
            idx = int(self._eval(node.index))
            ts = self._type_of(node.base)
            if ts is None or ts.kind != "array":
                raise InterpError("第 %d 行：对非数组取下标" % node.line)
            return base[self._index_offset(ts, idx, len(base), node.line)]
        if isinstance(node, Unary):
            return self._unary(node.op, self._eval(node.operand), node.line)
        if isinstance(node, Binary):
            return self._binary(node.op, self._eval(node.left),
                                self._eval(node.right), node.line)
        if isinstance(node, FuncCall):
            return self._call_function(node.name, node.args, node.line)
        raise InterpError("未知表达式 %r" % (node,))

    def _type_of(self, node):
        """静态类型推导（只用于下标区间与读 FB 字段）。"""
        if isinstance(node, VarRef):
            return self.store.types.get(node.name.upper())
        if isinstance(node, IndexRef):
            base = self._type_of(node.base)
            return base.elem if base is not None and base.kind == "array" else None
        if isinstance(node, FieldRef):
            base = self._type_of(node.base)
            if base is None:
                return None
            if base.kind == "fb":
                return FbInstance(base.name).field_type(node.name)
            if base.kind == "struct":
                try:
                    return field_of(struct_fields(self.structs, base.name), node.name)[1]
                except StTypeError:
                    return None
        return None

    def _unary(self, op, val, line):
        if op == "NOT":
            if isinstance(val, bool):
                return not val
            if isinstance(val, int):
                return ~val
            raise InterpError("第 %d 行：NOT 只支持 BOOL/整数" % line)
        if op == "-":
            return -val
        if op == "+":
            return val
        raise InterpError("第 %d 行：未知一元运算符 %s" % (line, op))

    def _binary(self, op, l, r, line):
        try:
            if op == "AND":
                return self._bool_or_bit(op, l, r, lambda a, b: a and b, lambda a, b: a & b, line)
            if op == "OR":
                return self._bool_or_bit(op, l, r, lambda a, b: a or b, lambda a, b: a | b, line)
            if op == "XOR":
                return self._bool_or_bit(op, l, r, lambda a, b: a != b, lambda a, b: a ^ b, line)
            if op in ("=", "<>", "<", ">", "<=", ">="):
                return self._compare(op, l, r)
            if op == "+":
                return l + r
            if op == "-":
                return l - r
            if op == "*":
                return l * r
            if op == "/":
                if r == 0:
                    raise InterpError("第 %d 行：除数为 0" % line)
                if isinstance(l, int) and isinstance(r, int):
                    return _trunc_div(l, r)
                return l / r
            if op == "MOD":
                if r == 0:
                    raise InterpError("第 %d 行：MOD 除数为 0" % line)
                return l - r * _trunc_div(l, r)
        except TypeError as e:
            raise InterpError("第 %d 行：%s 运算类型不匹配（%r, %r）：%s"
                              % (line, op, l, r, e)) from e
        raise InterpError("第 %d 行：未知运算符 %s" % (line, op))

    @staticmethod
    def _bool_or_bit(op, l, r, fbool, fbit, line):
        if isinstance(l, bool) and isinstance(r, bool):
            return fbool(l, r)
        if isinstance(l, int) and isinstance(r, int):
            return fbit(l, r)
        raise InterpError("第 %d 行：%s 两侧类型不一致（%r, %r）" % (line, op, l, r))

    @staticmethod
    def _compare(op, l, r):
        if op == "=":
            return l == r
        if op == "<>":
            return l != r
        if op == "<":
            return l < r
        if op == ">":
            return l > r
        if op == "<=":
            return l <= r
        return l >= r

    @staticmethod
    def _eq(a, b):
        return a == b

    @staticmethod
    def _truth(val):
        if isinstance(val, bool):
            return val
        raise InterpError("条件表达式必须是 BOOL，得到 %r" % (val,))

    def _call_function(self, name, args, line):
        fname = name.upper()
        vals = [self._eval(e) for _, e in args]
        conv = split_conversion(fname)
        if conv is not None:
            if len(vals) != 1:
                raise InterpError("第 %d 行：%s 需要 1 个参数，给了 %d 个"
                                  % (line, name, len(vals)))
            try:
                return convert_to(vals[0], conv[1])
            except (TypeError, ValueError) as e:
                raise InterpError("第 %d 行：%s 转换失败：%s" % (line, name, e)) from e
        table = {
            "ABS": lambda x: abs(x),
            "SQRT": lambda x: x ** 0.5,
            "EXPT": lambda a, b: a ** b,
            "MIN": lambda *x: min(x),
            "MAX": lambda *x: max(x),
            "LIMIT": lambda lo, v, hi: max(lo, min(v, hi)),
            "SEL": lambda g, a, b: a if g else b,
            "MUX": lambda k, *rest: rest[int(k)],
            "TRUNC": lambda x: int(x),
            "SHL": lambda a, n: a << int(n),
            "SHR": lambda a, n: a >> int(n),
        }
        if fname not in table:
            raise InterpError("第 %d 行：不支持或未定义的函数 %s（可用：%s；以及 X_TO_Y 转换）"
                              % (line, name, ", ".join(sorted(table))))
        try:
            return table[fname](*vals)
        except Exception as e:      # noqa: BLE001 - 统一转成解释器错误
            raise InterpError("第 %d 行调用 %s 失败：%s" % (line, name, e)) from e

    # ------------------------------------------------------------ 左值
    def _resolve(self, node):
        """返回 (容器, 键, 类型)，容器[key] 可写。"""
        if isinstance(node, VarRef):
            key = node.name.upper()
            if key not in self.store.values:
                raise InterpError("第 %d 行：未声明的变量 %s" % (node.line, node.name))
            return self.store.values, key, self.store.types[key]
        if isinstance(node, FieldRef):
            cont, key, ts = self._resolve(node.base)
            if ts.kind != "struct":
                raise InterpError("第 %d 行：%s 不是结构体，不能写字段"
                                  % (node.line, node.name))
            fname, fts = field_of(struct_fields(self.structs, ts.name), node.name)
            return cont[key], fname, fts
        if isinstance(node, IndexRef):
            cont, key, ts = self._resolve(node.base)
            if ts.kind != "array":
                raise InterpError("第 %d 行：对非数组取下标" % node.line)
            idx = int(self._eval(node.index))
            off = self._index_offset(ts, idx, len(cont[key]), node.line)
            return cont[key], off, ts.elem
        raise InterpError("第 %d 行：赋值左侧不合法" % getattr(node, "line", 0))

    @staticmethod
    def _index_offset(ts, idx, n, line):
        """把 ST 下标换成 Python 偏移；变长数组（ARRAY[*]）按实际长度判界。"""
        lo = 1 if ts.dynamic else ts.lo
        hi = n if ts.dynamic else ts.hi
        if not (lo <= idx <= hi):
            raise InterpError("第 %d 行：下标 %d 越界（%d..%d）" % (line, idx, lo, hi))
        return idx - lo


def _trunc_div(a, b):
    """IEC 整数除法：向 0 截断（不是 Python 的向下取整）。"""
    q = abs(a) // abs(b)
    return q if (a >= 0) == (b >= 0) else -q

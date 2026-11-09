"""语法分析：ST 子集 -> AST。

只解析解释器真正会执行的结构（见 docs/interp.md）：

    TYPE ... STRUCT ... END_STRUCT END_TYPE
    FUNCTION_BLOCK / PROGRAM / FUNCTION
    VAR / VAR_INPUT / VAR_OUTPUT / VAR_IN_OUT / VAR_TEMP
    :=  IF  CASE  FOR  WHILE  REPEAT  RETURN  EXIT  以及 FB 实例调用

遇到不支持的写法（VAR_EXTERNAL、METHOD、AT %I*、指针等）会抛 ParseError，
并指明行号——宁可明确报"不支持"，也不要静默算错。
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .lexer import LexError, Token, tokenize
from .st_types import StTypeError, TypeSpec, parse_time_ms, parse_type

VAR_KINDS = {
    "VAR": "local",
    "VAR_INPUT": "input",
    "VAR_OUTPUT": "output",
    "VAR_IN_OUT": "inout",
    "VAR_TEMP": "temp",
}
_UNSUPPORTED = {
    "VAR_EXTERNAL", "VAR_ACCESS", "VAR_CONFIG", "VAR_GLOBAL",
    "METHOD", "PROPERTY", "INTERFACE", "ACTION", "TRANSITION",
}
_END_OF_POU = {"END_FUNCTION_BLOCK", "END_PROGRAM", "END_FUNCTION"}


class ParseError(Exception):
    """语法错误（带行号）。"""


# ---------------------------------------------------------------- AST

@dataclass
class Program:
    structs: dict = field(default_factory=dict)    # "ST_PUMP" -> [(字段名大写, TypeSpec)]
    blocks: dict = field(default_factory=dict)     # "FB_P03" -> FbDef
    order: list = field(default_factory=list)


@dataclass
class FbDef:
    name: str
    kind: str
    vars: list = field(default_factory=list)
    body: list = field(default_factory=list)
    line: int = 0


@dataclass
class VarDecl:
    name: str
    ts: TypeSpec
    scope: str
    init: object = None
    line: int = 0


# ---- 语句 ----

@dataclass
class Assign:
    target: object
    value: object
    line: int = 0


@dataclass
class IfStmt:
    branches: list      # [(cond, [stmt]), ...]
    else_body: list
    line: int = 0


@dataclass
class CaseStmt:
    selector: object
    branches: list      # [(labels, [stmt]), ...]  labels 是常量列表
    else_body: list
    line: int = 0


@dataclass
class ForStmt:
    var: str
    start: object
    end: object
    step: object
    body: list
    line: int = 0


@dataclass
class WhileStmt:
    cond: object
    body: list
    line: int = 0


@dataclass
class RepeatStmt:
    body: list
    cond: object
    line: int = 0


@dataclass
class ReturnStmt:
    line: int = 0


@dataclass
class ExitStmt:
    line: int = 0


@dataclass
class CallStmt:
    name: str
    args: list          # [(形参名或 None, expr), ...]
    line: int = 0


# ---- 表达式 ----

@dataclass
class Lit:
    value: object
    line: int = 0


@dataclass
class VarRef:
    name: str
    line: int = 0


@dataclass
class FieldRef:
    base: object
    name: str
    line: int = 0


@dataclass
class IndexRef:
    base: object
    index: object
    line: int = 0


@dataclass
class Unary:
    op: str
    operand: object
    line: int = 0


@dataclass
class Binary:
    op: str
    left: object
    right: object
    line: int = 0


@dataclass
class FuncCall:
    name: str
    args: list
    line: int = 0


# ---------------------------------------------------------------- 解析器

class _Parser:
    def __init__(self, tokens):
        self.toks = tokens
        self.pos = 0
        self.structs = {}

    # ---- 基础 ----
    def peek(self, off=0) -> Token:
        return self.toks[min(self.pos + off, len(self.toks) - 1)]

    def next(self) -> Token:
        tok = self.toks[self.pos]
        self.pos += 1
        return tok

    def at(self, text) -> bool:
        tok = self.peek()
        return tok.kind in ("OP", "IDENT") and tok.text.upper() == text.upper()

    def accept(self, text) -> bool:
        if self.at(text):
            self.next()
            return True
        return False

    def expect(self, text) -> Token:
        if not self.at(text):
            self.fail("期望 %r，实际 %r" % (text, self.peek().text))
        return self.next()

    def expect_ident(self) -> str:
        tok = self.peek()
        if tok.kind != "IDENT":
            self.fail("期望标识符，实际 %r" % tok.text)
        self.next()
        return tok.text

    def fail(self, msg):
        raise ParseError("第 %d 行：%s" % (self.peek().line, msg))

    def skip_semi(self):
        while self.accept(";"):
            pass

    # ---- 顶层 ----
    def parse(self) -> Program:
        prog = Program()
        while self.peek().kind != "EOF":
            if self.accept(";"):
                continue
            tok = self.peek()
            word = tok.text.upper() if tok.kind == "IDENT" else ""
            if word == "TYPE":
                self.parse_type_block(prog)
            elif word in ("FUNCTION_BLOCK", "PROGRAM", "FUNCTION"):
                fb = self.parse_pou()
                key = fb.name.upper()
                if key in prog.blocks:
                    self.fail("重复定义的块：%s" % fb.name)
                prog.blocks[key] = fb
                prog.order.append(key)
            elif word in _UNSUPPORTED:
                self.fail("%s 不在解释器支持范围内（见 docs/interp.md）" % word)
            else:
                self.fail("无法解析的顶层结构：%r" % tok.text)
        prog.structs = self.structs
        return prog

    def parse_type_block(self, prog):
        self.expect("TYPE")
        while True:
            name = self.expect_ident()
            self.expect(":")
            if not self.at("STRUCT"):
                self.fail("只支持 TYPE ... STRUCT，不支持别名类型 %s" % name)
            self.next()
            fields = []
            while not self.at("END_STRUCT"):
                fields.extend(self.parse_field_decls())
            self.expect("END_STRUCT")
            self.skip_semi()
            if name.upper() in self.structs:
                self.fail("结构体重复定义：%s" % name)
            self.structs[name.upper()] = fields
            if self.accept("END_TYPE"):
                self.skip_semi()
                return
            if not self.at_kind_ident():
                self.fail("TYPE 块缺 END_TYPE")

    def at_kind_ident(self):
        return self.peek().kind == "IDENT"

    def parse_field_decls(self):
        decls = []
        names = [self.expect_ident()]
        while self.accept(","):
            names.append(self.expect_ident())
        self.expect(":")
        ts = self.parse_type()
        self.expect(";")
        for n in names:
            decls.append((n, ts))
        return decls

    def parse_pou(self):
        kind_tok = self.next()
        kind = kind_tok.text.upper()
        name = self.expect_ident()
        fb = FbDef(name=name, kind=kind, line=kind_tok.line)
        while True:
            tok = self.peek()
            word = tok.text.upper() if tok.kind == "IDENT" else ""
            if word in VAR_KINDS:
                fb.vars.extend(self.parse_var_block())
            elif word in _UNSUPPORTED:
                self.fail("%s 不在解释器支持范围内" % word)
            else:
                break
        fb.body = self.parse_stmts(stop=set(_END_OF_POU))
        end = self.peek()
        if end.text.upper() not in _END_OF_POU:
            self.fail("块 %s 没有以 END_FUNCTION_BLOCK/END_PROGRAM/END_FUNCTION 结束" % name)
        self.next()
        self.skip_semi()
        return fb

    def parse_var_block(self):
        tok = self.next()
        scope = VAR_KINDS[tok.text.upper()]
        decls = []
        while True:
            if self.accept("END_VAR"):
                self.skip_semi()
                return decls
            if self.peek().kind == "EOF":
                self.fail("VAR 块没有 END_VAR")
            # 修饰符
            while self.peek().kind == "IDENT" and \
                    self.peek().text.upper() in ("RETAIN", "PERSISTENT", "CONSTANT", "NON_RETAIN"):
                self.next()
            names = [self.expect_ident()]
            if self.at("AT"):
                self.fail("不支持直接地址声明（AT %%I/%%Q），题目用接口变量")
            while self.accept(","):
                names.append(self.expect_ident())
            self.expect(":")
            ts = self.parse_type()
            init = None
            if self.accept(":="):
                init = self.parse_expr()
            self.expect(";")
            for n in names:
                decls.append(VarDecl(name=n, ts=ts, scope=scope,
                                     init=init, line=tok.line))

    def parse_type(self) -> TypeSpec:
        if self.at("ARRAY"):
            self.next()
            self.expect("[")
            if self.at("*"):
                self.next()
                self.expect("]")
                self.expect("OF")
                elem = self.parse_type()
                return TypeSpec("array", elem=elem, lo=1, hi=0, dynamic=True)
            lo = self.parse_signed_int()
            self.expect("..")
            hi = self.parse_signed_int()
            self.expect("]")
            self.expect("OF")
            elem = self.parse_type()
            try:
                return TypeSpec("array", elem=elem, lo=lo, hi=hi)
            except StTypeError as e:
                self.fail(str(e))
        name = self.expect_ident()
        # STRING(254) / STRING[10] / WSTRING[20]
        if name.upper() in ("STRING", "WSTRING") and \
                (self.at("[") or self.at("(")):
            open_tok = self.next().text
            close = "]" if open_tok == "[" else ")"
            self.parse_signed_int()
            self.expect(close)
        try:
            return parse_type(name, self.structs)
        except StTypeError as e:
            self.fail(str(e))

    def parse_signed_int(self):
        sign = 1
        if self.accept("-"):
            sign = -1
        elif self.accept("+"):
            pass
        tok = self.next()
        if tok.kind != "INT":
            self.fail("期望整数，实际 %r" % tok.text)
        try:
            return sign * int(tok.text, 10) if "#" not in tok.text else \
                sign * int(tok.text.split("#", 1)[1], int(tok.text.split("#", 1)[0]))
        except ValueError:
            self.fail("非法整数 %r" % tok.text)

    # ---- 语句 ----
    def parse_stmts(self, stop):
        out = []
        while True:
            tok = self.peek()
            if tok.kind == "EOF":
                break
            word = tok.text.upper() if tok.kind == "IDENT" else ""
            if word in stop:
                break
            st = self.parse_stmt()
            if st is not None:
                out.append(st)
        return out

    def parse_stmt(self):
        if self.accept(";"):
            return None
        tok = self.peek()
        word = tok.text.upper() if tok.kind == "IDENT" else ""
        if word == "IF":
            return self.parse_if()
        if word == "CASE":
            return self.parse_case()
        if word == "FOR":
            return self.parse_for()
        if word == "WHILE":
            return self.parse_while()
        if word == "REPEAT":
            return self.parse_repeat()
        if word == "RETURN":
            self.next()
            self.skip_semi()
            return ReturnStmt(line=tok.line)
        if word == "EXIT":
            self.next()
            self.skip_semi()
            return ExitStmt(line=tok.line)
        if word in _UNSUPPORTED:
            self.fail("%s 语句不支持" % word)
        return self.parse_simple_stmt()

    def parse_simple_stmt(self):
        tok = self.peek()
        if tok.kind != "IDENT":
            self.fail("无法解析的语句：%r" % tok.text)
        name = self.expect_ident()
        if self.at("("):
            args = self.parse_call_args()
            self.skip_semi()
            return CallStmt(name=name, args=args, line=tok.line)
        target = self.parse_postfix(VarRef(name, line=tok.line))
        self.expect(":=")
        value = self.parse_expr()
        self.skip_semi()
        return Assign(target=target, value=value, line=tok.line)

    def parse_call_args(self):
        self.expect("(")
        args = []
        if not self.at(")"):
            while True:
                if self.peek().kind == "IDENT" and self.peek(1).kind == "OP" \
                        and self.peek(1).text == ":=":
                    pname = self.next().text
                    self.next()
                    args.append((pname, self.parse_expr()))
                else:
                    args.append((None, self.parse_expr()))
                if not self.accept(","):
                    break
        self.expect(")")
        return args

    def parse_if(self):
        tok = self.next()
        branches, else_body = [], []
        cond = self.parse_expr()
        self.expect("THEN")
        body = self.parse_stmts(stop={"ELSIF", "ELSE", "END_IF"})
        branches.append((cond, body))
        while self.accept("ELSIF"):
            cond = self.parse_expr()
            self.expect("THEN")
            body = self.parse_stmts(stop={"ELSIF", "ELSE", "END_IF"})
            branches.append((cond, body))
        if self.accept("ELSE"):
            else_body = self.parse_stmts(stop={"END_IF"})
        self.expect("END_IF")
        self.skip_semi()
        return IfStmt(branches=branches, else_body=else_body, line=tok.line)

    def parse_case(self):
        tok = self.next()
        selector = self.parse_expr()
        self.expect("OF")
        branches, else_body = [], []
        while not self.at("END_CASE"):
            if self.accept("ELSE"):
                else_body = self.parse_case_body(stop_else=False)
                break
            labels = [self.parse_const_expr()]
            while self.accept(","):
                labels.append(self.parse_const_expr())
            self.expect(":")
            body = self.parse_case_body(stop_else=True)
            branches.append((labels, body))
        self.expect("END_CASE")
        self.skip_semi()
        return CaseStmt(selector=selector, branches=branches,
                        else_body=else_body, line=tok.line)

    def parse_case_body(self, stop_else=True):
        """CASE 的分支体：遇到下一个标签 / ELSE / END_CASE 就停。"""
        out = []
        while True:
            if self.peek().kind == "EOF":
                self.fail("CASE 没有 END_CASE")
            if self.at("END_CASE") or (stop_else and self.at("ELSE")):
                break
            if self.at("ELSE") and not stop_else:
                break
            if self._looks_like_label():
                break
            st = self.parse_stmt()
            if st is not None:
                out.append(st)
        return out

    def _looks_like_label(self):
        t1 = self.peek()
        if t1.kind not in ("INT", "REAL", "IDENT"):
            return False
        t2 = self.peek(1)
        return t2.kind == "OP" and t2.text in (":", ",")

    def parse_for(self):
        tok = self.next()
        var = self.expect_ident()
        self.expect(":=")
        start = self.parse_expr()
        self.expect("TO")
        end = self.parse_expr()
        step = Lit(1)
        if self.accept("BY"):
            step = self.parse_expr()
        self.expect("DO")
        body = self.parse_stmts(stop={"END_FOR"})
        self.expect("END_FOR")
        self.skip_semi()
        return ForStmt(var=var, start=start, end=end, step=step, body=body, line=tok.line)

    def parse_while(self):
        tok = self.next()
        cond = self.parse_expr()
        self.expect("DO")
        body = self.parse_stmts(stop={"END_WHILE"})
        self.expect("END_WHILE")
        self.skip_semi()
        return WhileStmt(cond=cond, body=body, line=tok.line)

    def parse_repeat(self):
        tok = self.next()
        body = self.parse_stmts(stop={"UNTIL"})
        self.expect("UNTIL")
        cond = self.parse_expr()
        self.expect("END_REPEAT")
        self.skip_semi()
        return RepeatStmt(body=body, cond=cond, line=tok.line)

    # ---- 表达式（优先级按 IEC：OR < XOR < AND < 比较 < +- < */MOD < 一元 < 后缀）----
    def parse_expr(self):
        return self.parse_or()

    def parse_or(self):
        node = self.parse_xor()
        while self.at("OR"):
            tok = self.next()
            node = Binary(tok.text.upper(), node, self.parse_xor(), line=tok.line)
        return node

    def parse_xor(self):
        node = self.parse_and()
        while self.at("XOR"):
            tok = self.next()
            node = Binary("XOR", node, self.parse_and(), line=tok.line)
        return node

    def parse_and(self):
        node = self.parse_cmp()
        while self.at("AND") or self.at("&"):
            tok = self.next()
            node = Binary("AND", node, self.parse_cmp(), line=tok.line)
        return node

    def parse_cmp(self):
        node = self.parse_add()
        while True:
            tok = self.peek()
            if tok.kind == "OP" and tok.text in ("=", "<>", "<", ">", "<=", ">="):
                self.next()
                node = Binary(tok.text, node, self.parse_add(), line=tok.line)
            else:
                return node

    def parse_add(self):
        node = self.parse_mul()
        while True:
            tok = self.peek()
            if tok.kind == "OP" and tok.text in ("+", "-"):
                self.next()
                node = Binary(tok.text, node, self.parse_mul(), line=tok.line)
            else:
                return node

    def parse_mul(self):
        node = self.parse_unary()
        while True:
            tok = self.peek()
            if tok.kind == "OP" and tok.text in ("*", "/"):
                self.next()
                node = Binary(tok.text, node, self.parse_unary(), line=tok.line)
            elif self.at("MOD"):
                self.next()
                node = Binary("MOD", node, self.parse_unary(), line=tok.line)
            else:
                return node

    def parse_unary(self):
        tok = self.peek()
        if tok.kind == "OP" and tok.text in ("-", "+"):
            self.next()
            return Unary(tok.text, self.parse_unary(), line=tok.line)
        if self.at("NOT"):
            self.next()
            return Unary("NOT", self.parse_unary(), line=tok.line)
        return self.parse_postfix(self.parse_primary())

    def parse_postfix(self, node):
        while True:
            if self.accept("."):
                name = self.expect_ident()
                node = FieldRef(node, name, line=self.peek().line)
            elif self.accept("["):
                idx = self.parse_expr()
                self.expect("]")
                node = IndexRef(node, idx)
            elif self.at("(") and isinstance(node, VarRef):
                args = self.parse_call_args()
                node = FuncCall(node.name, args, line=node.line)
            else:
                return node

    def parse_primary(self):
        tok = self.next()
        if tok.kind == "INT":
            text = tok.text.replace("_", "")
            if "#" in text:
                base, digits = text.split("#", 1)
                return Lit(int(digits, int(base)), line=tok.line)
            return Lit(int(text, 10), line=tok.line)
        if tok.kind == "REAL":
            return Lit(float(tok.text.replace("_", "")), line=tok.line)
        if tok.kind == "TIME":
            return Lit(parse_time_ms(tok.text), line=tok.line)
        if tok.kind == "STRING":
            return Lit(tok.text, line=tok.line)
        if tok.kind == "IDENT":
            word = tok.text.upper()
            if word == "TRUE":
                return Lit(True, line=tok.line)
            if word == "FALSE":
                return Lit(False, line=tok.line)
            if word == "NULL":
                return Lit(None, line=tok.line)
            return VarRef(tok.text, line=tok.line)
        if tok.text == "(":
            node = self.parse_expr()
            self.expect(")")
            return node
        self.fail("表达式中出现无法解析的记号 %r" % tok.text)

    def parse_const_expr(self):
        """CASE 的标签：只允许常量（含无符号整数与 BOOL）。"""
        node = self.parse_add()
        if not isinstance(node, Lit):
            self.fail("CASE 标签必须是常量")
        return node.value


def parse(src: str) -> Program:
    try:
        return _Parser(tokenize(src)).parse()
    except LexError as e:
        raise ParseError(str(e)) from e

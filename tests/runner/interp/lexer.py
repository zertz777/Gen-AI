"""词法分析：把 ST 源码切成 token。

支持的注释：`(* ... *)`（可嵌套）、`//` 行注释。
支持的记号：标识符、十进制/16#/2#/8# 整数、带小数或指数的实数、
`T#500ms` 一类时间字面量、单/双引号字符串、以及 IEC 的运算符。

第 0 行是"文件级"约定：所有 token 都带 1 起的行号与列号，报错时能定位。
"""
from __future__ import annotations

import re
from dataclasses import dataclass

#: 这些关键字后面跟 `#` 时按时间字面量处理
_TIME_HEADS = {"T", "TIME", "LTIME", "TIME_OF_DAY", "TOD", "LTIME_OF_DAY"}
_MULTI_OPS = (":=", "=>", "<>", "<=", ">=", "..", "**")
_SINGLE_OPS = set("=<>+-*/(),;:.[]#&^")
_IDENT_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


class LexError(Exception):
    """词法错误（带行列号）。"""


@dataclass
class Token:
    kind: str      # IDENT | INT | REAL | TIME | STRING | OP | EOF
    text: str
    line: int
    col: int

    def __repr__(self):
        return "Token(%s,%r,%d:%d)" % (self.kind, self.text, self.line, self.col)


def tokenize(src: str) -> list:
    toks, i, n = [], 0, len(src)
    line, line_start = 1, 0

    def _col(pos):
        return pos - line_start + 1

    while i < n:
        ch = src[i]

        # 换行与空白
        if ch == "\n":
            i += 1
            line += 1
            line_start = i
            continue
        if ch in " \t\r":
            i += 1
            continue

        # (* 嵌套块注释 *)
        if src.startswith("(*", i):
            depth, j = 1, i + 2
            while j < n and depth:
                if src.startswith("(*", j):
                    depth, j = depth + 1, j + 2
                elif src.startswith("*)", j):
                    depth, j = depth - 1, j + 2
                else:
                    if src[j] == "\n":
                        line += 1
                        line_start = j + 1
                    j += 1
            if depth:
                raise LexError("第 %d 行的块注释没有闭合" % line)
            i = j
            continue

        # // 行注释
        if src.startswith("//", i):
            while i < n and src[i] != "\n":
                i += 1
            continue

        # 字符串：'...' 或 "..."，内部重复引号表示转义
        if ch in "'\"":
            q, j, buf = ch, i + 1, []
            while j < n:
                if src[j] == q:
                    if j + 1 < n and src[j + 1] == q:
                        buf.append(q)
                        j += 2
                        continue
                    break
                if src[j] == "\n":
                    raise LexError("第 %d 行的字符串没有闭合" % line)
                buf.append(src[j])
                j += 1
            else:
                raise LexError("第 %d 行的字符串没有闭合" % line)
            toks.append(Token("STRING", "".join(buf), line, _col(i)))
            i = j + 1
            continue

        # 标识符 / 时间字面量
        m = _IDENT_RE.match(src, i)
        if m:
            word = m.group(0)
            j = m.end()
            if j < n and src[j] == "#" and word.upper() in _TIME_HEADS:
                k = j + 1
                while k < n and (src[k].isalnum() or src[k] in "._"):
                    k += 1
                if k == j + 1:
                    raise LexError("第 %d 行的时间字面量缺内容" % line)
                toks.append(Token("TIME", src[i:k], line, _col(i)))
                i = k
                continue
            toks.append(Token("IDENT", word, line, _col(i)))
            i = j
            continue

        # 数字：16#FF / 2#1010 / 8#17 / 123 / 1.5 / 1.0E-3
        if ch.isdigit():
            j = i
            while j < n and (src[j].isalnum() or src[j] in "_#"):
                j += 1
            text = src[i:j]
            if "#" in text:
                toks.append(Token("INT", text, line, _col(i)))
                i = j
                continue
            # 实数：小数点或指数
            k = j
            is_real = False
            if k < n and src[k] == "." and k + 1 < n and src[k + 1].isdigit():
                is_real = True
                k += 1
                while k < n and src[k].isdigit():
                    k += 1
            if k < n and src[k] in "eE":
                m2 = re.match(r"[eE][+-]?\d+", src[k:k + 8])
                if m2:
                    is_real = True
                    k += m2.end()
            toks.append(Token("REAL" if is_real else "INT", src[i:k], line, _col(i)))
            i = k
            continue

        # 多字符运算符
        for op in _MULTI_OPS:
            if src.startswith(op, i):
                toks.append(Token("OP", op, line, _col(i)))
                i += len(op)
                break
        else:
            if ch in _SINGLE_OPS:
                toks.append(Token("OP", ch, line, _col(i)))
                i += 1
                continue
            raise LexError("第 %d 行第 %d 列出现无法识别的字符 %r" % (line, _col(i), ch))

    toks.append(Token("EOF", "", line, _col(i)))
    return toks

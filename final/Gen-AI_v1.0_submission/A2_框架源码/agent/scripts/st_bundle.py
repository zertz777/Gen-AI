# encoding: utf-8
"""把平面 ST 中的 TYPE 和单一 POU 分离为 CODESYS 文本对象。

这是受控的导入适配器，不是 ST 编译器。不支持 METHOD/ACTION/INTERFACE/
多POU源文件；遇到这些输入拒绝导入，避免只编译源文件的一部分。
同时可在 CPython 3 和 CODESYS IronPython 2.7 使用。
"""
from __future__ import print_function
import re


def mask_literals_comments(text):
    chars = list(text)
    index, depth, quote = 0, 0, None
    while index < len(text):
        pair = text[index:index + 2]
        char = text[index]
        if depth:
            if pair == "(*":
                depth += 1
                chars[index:index + 2] = "  "
                index += 2
                continue
            if pair == "*)":
                depth -= 1
                chars[index:index + 2] = "  "
                index += 2
                continue
            if char not in "\r\n":
                chars[index] = " "
        elif quote:
            if char == "$" and index + 1 < len(text):
                chars[index:index + 2] = "  "
                index += 2
                continue
            if char == quote:
                if index + 1 < len(text) and text[index + 1] == quote:
                    chars[index:index + 2] = "  "
                    index += 2
                    continue
                quote = None
            if char not in "\r\n":
                chars[index] = " "
        elif pair == "(*":
            depth = 1
            chars[index:index + 2] = "  "
            index += 2
            continue
        elif pair == "//":
            stop = text.find("\n", index)
            if stop < 0:
                stop = len(text)
            chars[index:stop] = " " * (stop - index)
            index = stop
            continue
        elif char in ("'", '"'):
            quote = char
            chars[index] = " "
        index += 1
    if depth or quote:
        raise ValueError("Unterminated ST comment or string")
    return "".join(chars)


def split_source(text):
    mask = mask_literals_comments(text)
    # Only flat TYPE declarations and one POU are supported by this bridge.
    if re.search(r"^\s*(METHOD|ACTION|INTERFACE|CLASS|PROPERTY|TRANSITION)\b", mask, re.I | re.M):
        raise ValueError("Object-oriented/member ST is unsupported by this bridge")
    pattern = re.compile(r"\bTYPE\s+([A-Za-z_]\w*)\s*:.*?\bEND_TYPE\b\s*;?", re.I | re.S)
    types = []
    rest_mask = list(mask)
    for match in pattern.finditer(mask):
        types.append({"name": match.group(1), "declaration": text[match.start():match.end()]})
        rest_mask[match.start():match.end()] = [c if c in "\r\n" else " " for c in mask[match.start():match.end()]]
    remaining = "".join(rest_mask)
    heads = list(re.finditer(r"^[ \t]*(FUNCTION_BLOCK|PROGRAM|FUNCTION)\s+([A-Za-z_]\w*)[^\n]*", remaining, re.I | re.M))
    if len(heads) != 1:
        raise ValueError("Exactly one PROGRAM, FUNCTION_BLOCK or FUNCTION is required")
    head = heads[0]
    kind, name = head.group(1).upper(), head.group(2)
    end = re.search(r"\bEND_" + kind + r"\b\s*;?", remaining[head.end():], re.I)
    if not end:
        raise ValueError("Missing END_" + kind)
    end_start, end_stop = head.end() + end.start(), head.end() + end.end()
    # Nontrivial content outside the one POU is rejected rather than silently dropped.
    outside = remaining[:head.start()] + remaining[end_stop:]
    outside = re.sub(r"\{[^}]*\}", "", outside)
    if outside.strip():
        raise ValueError("Unsupported content outside TYPE/POU")
    vars_end = list(re.finditer(r"\bEND_VAR\b", remaining[head.end():end_start], re.I))
    split = head.end() + vars_end[-1].end() if vars_end else head.end()
    declaration = text[head.start():split].strip()
    implementation = text[split:end_start].strip()
    return {"types": types, "kind": kind, "name": name,
            "declaration": declaration, "implementation": implementation}

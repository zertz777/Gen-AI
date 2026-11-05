"""yaml_io.py -- 极简 YAML 读写器（无第三方依赖）

本仓库的题面文件全部使用同一套受控子集：
  * 映射：``key: value``，子项缩进 2 空格
  * 序列：``- item``，或 "键 + 缩进序列"
  * 多行文本：``key: |-`` 块标量（统一 2 空格基准缩进）
  * 标量：字符串、整数、布尔（true/false）

不支持的写法：锚点、标签、流式集合 ``{}`` / ``[]``、多文档。
一旦文件里出现这些写法，load() 会直接报错，而不是悄悄读错——
"读不出来"比"读错一行"安全。

之所以不用 PyYAML：课程交付要求"在没装过项目的电脑上按 README 三条
命令能出结果"，少一个第三方依赖就少一处装不上的风险。
"""

from __future__ import annotations

import re

__all__ = ["dump", "load", "dumps", "loads", "YamlError"]


class YamlError(ValueError):
    """YAML 子集之外的写法。"""


# --------------------------------------------------------------------------
# 写
# --------------------------------------------------------------------------

_PLAIN_SAFE = re.compile(r"^[^\s\-?:,\[\]{}#&*!|>'\"%@`][^#]*$")


def _scalar(value) -> str:
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, (int, float)):
        return repr(value)
    s = str(value)
    if s and _PLAIN_SAFE.match(s) and not s.endswith(":") and "\n" not in s:
        if ": " not in s and not s.startswith((" ", "\t")):
            return s
    # 双引号是 JSON 的子集，转义可靠
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _is_block_scalar(s: str) -> bool:
    return "\n" in str(s)


def _emit(obj, indent: int, out: list, key_prefix: str | None = None) -> None:
    pad = "  " * indent

    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, dict):
                if not v:
                    out.append(f"{pad}{k}: {{}}")
                else:
                    out.append(f"{pad}{k}:")
                    _emit(v, indent + 1, out)
            elif isinstance(v, list):
                if not v:
                    out.append(f"{pad}{k}: []")
                else:
                    out.append(f"{pad}{k}:")
                    _emit(v, indent + 1, out)
            elif isinstance(v, str) and _is_block_scalar(v):
                out.append(f"{pad}{k}: |-")
                for line in v.split("\n"):
                    out.append(f"{pad}  {line}" if line else "")
            else:
                out.append(f"{pad}{k}: {_scalar(v)}")
        return

    if isinstance(obj, list):
        for item in obj:
            if isinstance(item, dict):
                first = True
                for k, v in item.items():
                    if first:
                        if isinstance(v, str) and _is_block_scalar(v):
                            out.append(f"{pad}- {k}: |-")
                            for line in v.split("\n"):
                                out.append(f"{pad}    {line}" if line else "")
                        elif isinstance(v, (dict, list)):
                            out.append(f"{pad}- {k}:")
                            _emit(v, indent + 2, out)
                        else:
                            out.append(f"{pad}- {k}: {_scalar(v)}")
                        first = False
                    else:
                        if isinstance(v, str) and _is_block_scalar(v):
                            out.append(f"{pad}  {k}: |-")
                            for line in v.split("\n"):
                                out.append(f"{pad}    {line}" if line else "")
                        elif isinstance(v, (dict, list)):
                            out.append(f"{pad}  {k}:")
                            _emit(v, indent + 2, out)
                        else:
                            out.append(f"{pad}  {k}: {_scalar(v)}")
            elif isinstance(item, list):
                raise YamlError("不支持嵌套序列")
            else:
                out.append(f"{pad}- {_scalar(item)}")
        return

    out.append(f"{pad}{_scalar(obj)}")


def dumps(obj) -> str:
    out: list[str] = []
    _emit(obj, 0, out)
    return "\n".join(out) + "\n"


def dump(obj, path) -> None:
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(dumps(obj))


# --------------------------------------------------------------------------
# 读
# --------------------------------------------------------------------------

_KEY_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_\-]*):(?:\s+(.*))?$")


def _strip_comment(line: str) -> str:
    """去掉未加引号的行尾注释（`# ` 前有空白的才当注释）。"""
    if "#" not in line:
        return line
    in_s = in_d = False
    for i, ch in enumerate(line):
        if ch == '"' and not in_s:
            in_d = not in_d
        elif ch == "'" and not in_d:
            in_s = not in_s
        elif ch == "#" and not in_s and not in_d and i > 0 and line[i - 1] in " \t":
            return line[:i].rstrip()
    return line


def _unquote(s: str):
    s = s.strip()
    if len(s) >= 2 and s[0] == s[-1] == '"':
        body = s[1:-1]
        return (
            body.replace("\\\\", "\x00")
            .replace('\\"', '"')
            .replace("\\n", "\n")
            .replace("\\t", "\t")
            .replace("\x00", "\\")
        )
    if len(s) >= 2 and s[0] == s[-1] == "'":
        return s[1:-1].replace("''", "'")
    if s in ("true", "True"):
        return True
    if s in ("false", "False"):
        return False
    if s in ("null", "~", ""):
        return None if s else ""
    if re.fullmatch(r"-?\d+", s):
        return int(s)
    if re.fullmatch(r"-?\d+\.\d+", s):
        return float(s)
    return s


def loads(text: str):
    raw = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    # 逐行记录缩进与去注释后的正文
    lines: list[tuple[int, str]] = []
    for ln in raw:
        if not ln.strip():
            lines.append((-1, ""))
            continue
        body = _strip_comment(ln)
        if not body.strip():
            continue
        indent = len(body) - len(body.lstrip(" "))
        if "\t" in body[:indent]:
            raise YamlError("缩进里不能出现制表符")
        lines.append((indent, body.strip()))

    pos = 0

    def parse_block(indent: int):
        nonlocal pos
        # 跳过空行
        while pos < len(lines) and lines[pos][0] == -1:
            pos += 1
        if pos >= len(lines):
            return None

        cur_indent, cur = lines[pos]
        if cur.startswith("- "):
            seq = []
            while pos < len(lines):
                while pos < len(lines) and lines[pos][0] == -1:
                    pos += 1
                if pos >= len(lines):
                    break
                ind, body = lines[pos]
                if ind != indent or not body.startswith("- "):
                    break
                item = body[2:].strip()
                pos += 1
                if _KEY_RE.match(item):
                    # - key: value 形式的映射项
                    item_indent = indent + 2
                    sub = {}
                    k, v = _KEY_RE.match(item).group(1), _KEY_RE.match(item).group(2)
                    sub[k] = _parse_value(v, item_indent)
                    # 同层其余键从当前行继续
                    rest = parse_block(item_indent)
                    if isinstance(rest, dict):
                        sub.update(rest)
                    seq.append(sub)
                elif item in ("|-", "|", ">-", ">"):
                    seq.append(_parse_block_scalar(indent, item))
                else:
                    seq.append(_unquote(item))
            return seq

        if _KEY_RE.match(cur):
            mapping = {}
            while pos < len(lines):
                while pos < len(lines) and lines[pos][0] == -1:
                    pos += 1
                if pos >= len(lines):
                    break
                ind, body = lines[pos]
                if ind != indent:
                    break
                m = _KEY_RE.match(body)
                if not m:
                    raise YamlError(f"无法解析的行（第 {pos + 1} 行）：{body!r}")
                k, v = m.group(1), m.group(2)
                pos += 1
                mapping[k] = _parse_value(v, indent)
            return mapping

        # 纯标量块
        pos += 1
        return _unquote(cur)

    def _parse_block_scalar(parent_indent: int, style: str) -> str:
        nonlocal pos
        buf = []
        base = None
        while pos < len(lines):
            ind, body = lines[pos]
            if ind == -1:
                buf.append("")
                pos += 1
                continue
            if ind <= parent_indent:
                break
            if base is None:
                base = ind
            buf.append(" " * (ind - base) + body)
            pos += 1
        while buf and buf[-1] == "":
            buf.pop()
        text_ = "\n".join(buf)
        if style.startswith(">"):
            text_ = " ".join(x for x in text_.split("\n") if x)
        return text_

    def _parse_value(v, parent_indent: int):
        if v is None:
            # 键后面没有值：可能是嵌套映射或序列，也可能是空串
            nxt = None
            p = pos
            while p < len(lines) and lines[p][0] == -1:
                p += 1
            if p < len(lines):
                nxt = lines[p]
            if nxt is not None and nxt[0] > parent_indent:
                return parse_block(nxt[0])
            return ""
        v = v.strip()
        if v in ("|-", "|", ">-", ">"):
            return _parse_block_scalar(parent_indent, v)
        if v in ("{}", "[]"):
            return {} if v == "{}" else []
        return _unquote(v)

    result = parse_block(0)
    while pos < len(lines) and lines[pos][0] == -1:
        pos += 1
    if pos < len(lines):
        raise YamlError(f"文件在第 {pos + 1} 行后仍有未归属的内容：{lines[pos][1]!r}")
    return result


def load(path):
    with open(path, encoding="utf-8") as fh:
        return loads(fh.read())

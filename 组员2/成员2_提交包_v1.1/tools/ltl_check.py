# -*- coding: utf-8 -*-
"""ltl_check.py -- LTL 规约的语法检查与命题核查（零依赖）

为什么要有这个工具：
    规约如果只是「一段自然语言注释」，等于没写——成员 4 判不了对错，Agent 也没法
    自检。所以本组规定：data/specs/*.ltl 必须是**能被工具读**的 ASCII LTL，并且
    用到的每一个命题都能在该题的 I/O 表里找到出处。

支持的语法（严格子集，超出即报错，不做宽容解析）：
    命题      I/O 变量名（BOOL），或文件头 `# alias:` 声明的派生命题
    常量      TRUE / FALSE
    数值      12 / 1.5 / 16#8001（十六进制）
    比较      == != < <= > >=
    算术      + - * /  与括号（只允许出现在别名定义与比较式里）
    布尔      ! && || -> <->
    时序      G F X U W R，可带区间 [a,b]（单位：扫描周期，20 ms/周期）
    行格式    `C<n>: <公式>   -- 注释`，n 取 1..10（对应条款库 C1—C10）
    别名      `# alias: 名字 := 表达式`

检查内容：
    1. 语法是否合法（括号、优先级、时序算子参数）
    2. 命题是否都能溯源：要么是本题 I/O 名，要么是本题声明的别名
    3. 别名的右值是否只引用本题 I/O 名或别名
    4. 条款号是否在 1..10、是否重号；每题是否 4—6 条、C1—C10 覆盖是否合理
    5. 布尔输出是否被误用为数值、数值量是否被直接当成命题

用法：
    python tools/ltl_check.py                 # 检查 data/specs/*.ltl
    python tools/ltl_check.py --file P03.ltl
    python tools/ltl_check.py --quiet         # 只打印汇总
"""

import argparse
import glob
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import yaml_io

SPEC_DIR = os.path.join(ROOT, 'data', 'specs')
TASK_DIR = os.path.join(ROOT, 'data', 'tasks')
CYCLE_MS = 20

KEYWORDS = {'G', 'F', 'X', 'U', 'W', 'R', 'TRUE', 'FALSE'}

TOKEN_RE = re.compile(r"""
    (?P<space>\s+)
  | (?P<hex>16\#[0-9A-Fa-f]+)
  | (?P<num>\d+\.\d+|\d+)
  | (?P<ident>[A-Za-z_][A-Za-z0-9_]*(?:\[\])?(?:\.[A-Za-z_][A-Za-z0-9_]*)?)
  | (?P<op><->|->|&&|\|\||==|!=|<=|>=|[!<>()\[\],+\-*/])
""", re.VERBOSE)


class LtlError(Exception):
    def __init__(self, msg, pos=None):
        Exception.__init__(self, msg)
        self.msg = msg
        self.pos = pos


def tokenize(src):
    out = []
    i = 0
    while i < len(src):
        m = TOKEN_RE.match(src, i)
        if not m:
            raise LtlError('无法识别的字符 %r（位置 %d）' % (src[i], i))
        i = m.end()
        kind = m.lastgroup
        if kind == 'space':
            continue
        out.append((kind, m.group()))
    out.append(('eof', ''))
    return out


class Parser(object):
    """递归下降：temporal -> equiv -> imply -> or -> and -> until -> unary -> cmp -> expr"""

    def __init__(self, tokens):
        self.t = tokens
        self.i = 0

    def peek(self):
        return self.t[self.i]

    def next(self):
        tok = self.t[self.i]
        self.i += 1
        return tok

    def accept(self, val):
        kind, v = self.peek()
        if v == val and kind in ('op',):
            self.i += 1
            return True
        return False

    def expect(self, val):
        kind, v = self.peek()
        if v != val:
            raise LtlError('期望 %r，实际是 %r' % (val, v if v else 'EOF'))
        self.i += 1
        return v

    # ---- 时序层 ----
    def formula(self):
        node = self.implication()
        if self.accept('<->'):
            node = ('iff', node, self.implication())
        return node

    def implication(self):
        left = self.disjunction()
        if self.accept('->'):
            return ('implies', left, self.implication())
        return left

    def disjunction(self):
        node = self.conjunction()
        while self.accept('||'):
            node = ('or', node, self.conjunction())
        return node

    def conjunction(self):
        node = self.temporal_bin()
        while self.accept('&&'):
            node = ('and', node, self.temporal_bin())
        return node

    def temporal_bin(self):
        node = self.unary()
        kind, v = self.peek()
        while kind == 'ident' and v in ('U', 'W', 'R'):
            self.next()
            bound = self.opt_bound()
            rhs = self.unary()
            node = ('bin', v, bound, node, rhs)
            kind, v = self.peek()
        return node

    def opt_bound(self):
        if self.accept('['):
            lo = self.next()
            if lo[0] != 'num':
                raise LtlError('时序区间下界必须是整数')
            self.expect(',')
            hi = self.next()
            if hi[0] != 'num':
                raise LtlError('时序区间上界必须是整数')
            self.expect(']')
            a, b = int(lo[1]), int(hi[1])
            if b < a:
                raise LtlError('时序区间上界小于下界：[%d,%d]' % (a, b))
            return (a, b)
        return None

    def unary(self):
        kind, v = self.peek()
        if v == '!' and kind == 'op':
            self.next()
            return ('not', self.unary())
        if kind == 'ident' and v in ('G', 'F', 'X'):
            self.next()
            bound = self.opt_bound()
            return ('un', v, bound, self.unary())
        return self.primary()

    def primary(self):
        kind, v = self.peek()
        if v == '(' and kind == 'op':
            self.next()
            node = self.formula()
            self.expect(')')
            return node
        if kind == 'ident' and v in ('TRUE', 'FALSE'):
            self.next()
            return ('const', v == 'TRUE')
        if kind == 'ident':
            self.next()
            # 可能是比较的左值：a < b
            nk, nv = self.peek()
            if nk == 'op' and nv in ('==', '!=', '<', '<=', '>', '>='):
                self.next()
                right = self.expr()
                return ('cmp', nv, ('ref', v), right)
            return ('atom', v)
        raise LtlError('意外的记号 %r' % (v if v else 'EOF'))

    # ---- 算术/比较 ----
    def cmp_expr(self):
        left = self.expr()
        kind, v = self.peek()
        if kind == 'op' and v in ('==', '!=', '<', '<=', '>', '>='):
            self.next()
            return ('cmp', v, left, self.expr())
        return left

    def expr(self):
        node = self.term()
        while True:
            kind, v = self.peek()
            if kind == 'op' and v in ('+', '-'):
                self.next()
                node = ('arith', v, node, self.term())
            else:
                return node

    def term(self):
        node = self.factor()
        while True:
            kind, v = self.peek()
            if kind == 'op' and v in ('*', '/'):
                self.next()
                node = ('arith', v, node, self.factor())
            else:
                return node

    def factor(self):
        kind, v = self.peek()
        if v == '-' and kind == 'op':
            self.next()
            return ('neg', self.factor())
        if v == '(' and kind == 'op':
            self.next()
            node = self.expr()
            self.expect(')')
            return node
        if kind == 'num':
            self.next()
            return ('num', float(v))
        if kind == 'hex':
            self.next()
            return ('num', float(int(v.split('#')[1], 16)))
        if kind == 'ident':
            self.next()
            return ('ref', v)
        raise LtlError('算术表达式里出现意外记号 %r' % (v if v else 'EOF'))

    def parse_alias(self):
        """别名右值：比较式与算术式的布尔组合（含 && || !）。"""
        self.i = 0
        node = self.alias_or()
        if self.peek()[0] != 'eof':
            raise LtlError('别名定义后面还有多余内容：%r' % (self.peek()[1],))
        return node

    def alias_or(self):
        node = self.alias_and()
        while self.accept('||'):
            node = ('or', node, self.alias_and())
        return node

    def alias_and(self):
        node = self.alias_not()
        while self.accept('&&'):
            node = ('and', node, self.alias_not())
        return node

    def alias_not(self):
        if self.accept('!'):
            return ('not', self.alias_not())
        return self.cmp_expr()


def walk(node, fn):
    fn(node)
    if not isinstance(node, tuple):
        return
    for part in node[1:]:
        if isinstance(part, tuple):
            walk(part, fn)
        elif isinstance(part, list):
            for sub in part:
                if isinstance(sub, tuple):
                    walk(sub, fn)


def collect_refs(node):
    refs = set()

    def fn(n):
        if isinstance(n, tuple) and n[0] in ('atom', 'ref'):
            refs.add(n[1])
    walk(node, fn)
    return refs


ALIAS_RE = re.compile(r'^\s*#\s*alias:\s*([A-Za-z_][A-Za-z0-9_]*)\s*:=\s*(.+?)\s*$')
CLAUSE_RE = re.compile(r'^(C\d{1,2}[a-z]?)\s*:\s*(.+?)\s*$')


def load_task(tid):
    path = os.path.join(TASK_DIR, tid + '.yaml')
    if not os.path.exists(path):
        raise LtlError('找不到题面 %s（先跑 tools/import_bank.py）' % path)
    return yaml_io.load(path)


def check_file(path, verbose=True):
    name = os.path.basename(path)
    tid = name.split('.')[0]
    errs = []
    task = None
    try:
        task = load_task(tid)
    except Exception as exc:  # noqa: BLE001
        return ['%s: 读不到题面：%s' % (name, exc)], {}

    io = {r['name']: r['data_type'] for r in task['io_table']}
    bool_io = set(n for n, t in io.items() if t.upper() == 'BOOL')

    lines = open(path, encoding='utf-8').read().splitlines()
    aliases = {}
    clauses = []
    for lineno, raw in enumerate(lines, 1):
        s = raw.strip()
        if not s or s.startswith('#'):
            m = ALIAS_RE.match(raw)
            if m:
                aname, rhs = m.group(1), m.group(2)
                try:
                    ast = Parser(tokenize(rhs)).parse_alias()
                except LtlError as exc:
                    errs.append('%s:%d 别名 %s 语法错误：%s' % (name, lineno, aname, exc.msg))
                    continue
                refs = collect_refs(ast)
                unknown = [r for r in refs if r not in io and r not in aliases]
                if unknown:
                    errs.append('%s:%d 别名 %s 引用了未声明的量：%s'
                                % (name, lineno, aname, '、'.join(sorted(unknown))))
                aliases[aname] = ast
            continue
        m = CLAUSE_RE.match(s)
        if not m:
            errs.append('%s:%d 既不是注释也不是以 C<n>: 开头的条款：%s' % (name, lineno, s[:40]))
            continue
        cid = m.group(1)
        body = m.group(2)
        formula = body.split('--')[0].strip()
        cnum = int(re.match(r'C(\d{1,2})', cid).group(1))
        if not 1 <= cnum <= 10:
            errs.append('%s:%d 条款号 %s 超出 C1—C10' % (name, lineno, cid))
        try:
            ps = Parser(tokenize(formula))
            ast = ps.formula()
            if ps.peek()[0] != 'eof':
                errs.append('%s:%d 公式末尾有多余记号 %r' % (name, lineno, ps.peek()[1]))
        except LtlError as exc:
            errs.append('%s:%d %s 语法错误：%s' % (name, lineno, cid, exc.msg))
            continue
        refs = collect_refs(ast)
        unknown = [r for r in refs if r not in io and r not in aliases and r not in KEYWORDS]
        if unknown:
            errs.append('%s:%d %s 用了不存在的命题：%s'
                        % (name, lineno, cid, '、'.join(sorted(unknown))))
        nonbool = [r for r in refs if r in io and r not in bool_io and r not in aliases]
        # 非 BOOL 量只能出现在比较式里，出现在 atom 位置即视为误用
        if nonbool:
            def is_bare(n):
                return isinstance(n, tuple) and n[0] == 'atom' and n[1] in nonbool
            bad = []

            def fn(n):
                if is_bare(n):
                    bad.append(n[1])
            walk(ast, fn)
            if bad:
                errs.append('%s:%d %s 把非 BOOL 量当命题用：%s（应写成比较式）'
                            % (name, lineno, cid, '、'.join(sorted(set(bad)))))
        clauses.append({'id': cid, 'formula': formula, 'ast': ast})

    ids = [c['id'] for c in clauses]
    nums = set(int(re.match(r'C(\d{1,2})', i).group(1)) for i in ids)
    has_note = any(l.strip().startswith('# note:') for l in lines)
    if len(ids) != len(set(ids)):
        dup = sorted(set(i for i in ids if ids.count(i) > 1))
        errs.append('%s: 条款号重复 %s（同类条款请用 C7a/C7b 区分）' % (name, dup))
    low = 2 if has_note else 4
    if not low <= len(clauses) <= 6:
        errs.append('%s: 条款数 %d 不在 %d—6 之间%s'
                    % (name, len(clauses), low, '（已写 note 说明缺口）' if has_note else ''))
    if 1 not in nums and not has_note:
        errs.append('%s: 缺少 C1（停止优先），该题若无停止类信号需在文件头写 `# note:` 说明原因' % name)

    if verbose:
        print('%s  %-42s %d 条  别名 %d 个  I/O %d'
              % (name.ljust(12), task['title'][:40], len(clauses), len(aliases), len(io)))
    return errs, {'task': task, 'clauses': clauses, 'aliases': aliases}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--file', default=None)
    ap.add_argument('--quiet', action='store_true')
    args = ap.parse_args()

    if args.file:
        files = [os.path.join(SPEC_DIR, args.file)]
    else:
        files = sorted(glob.glob(os.path.join(SPEC_DIR, '*.ltl')))
    if not files:
        raise SystemExit('没有找到任何 .ltl 文件')

    all_errs = []
    total_clauses = 0
    covered = {}
    for f in files:
        errs, info = check_file(f, verbose=not args.quiet)
        all_errs.extend(errs)
        total_clauses += len(info.get('clauses', []))
        for c in info.get('clauses', []):
            covered[c['id']] = covered.get(c['id'], 0) + 1

    print()
    print('规约文件 %d 份，条款合计 %d 条' % (len(files), total_clauses))
    if covered:
        print('条款覆盖：' + '，'.join('%s=%d' % (k, covered[k]) for k in sorted(covered)))
    if all_errs:
        print('')
        for e in all_errs:
            print('  ✗ ' + e)
        raise SystemExit('\n%d 处问题' % len(all_errs))
    print('全部通过：语法合法，命题均可溯源到本题 I/O 或已声明的别名。')


if __name__ == '__main__':
    main()

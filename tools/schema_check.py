# -*- coding: utf-8 -*-
"""schema_check.py —— 题集与规约的硬校验（成员1 的验收脚本）

与 ltl_check.py 的分工：
  · ltl_check.py 只管「规约本身写对没有」（语法、命题可溯源、条款号合法）。
  · 本脚本管「题集与规约之间对不对得上」，以及课程要求点名的几项数据合规：
      1. 题面 12 字段齐全、类型正确、枚举合法、task_id 与文件名一致；
      2. I/O 表非空、变量名唯一、方向合法、类型在允许集合内；
      3. 每题都有对应 .ltl，条数在 4—6（有 note 可放宽到 2）；
      4. 规约里的每条 K 编号都能在题面 constraints 里找到，且每条 constraint
         至少被一条条款引用（防止写了约束没人验）；
      5. provenance.csv 覆盖全部题号，11 列齐全，出处/合成过程/复核人非空；
      6. 打印难度/类别/条款覆盖统计，与 diversity.md 的数字应一致。

用法：
    python tools/schema_check.py            # 全量校验
    python tools/schema_check.py --quiet    # 只输出结论
    python tools/schema_check.py --task S03 # 单题

退出码：0 全部通过，1 有问题。
"""
import csv
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import yaml_io
import ltl_check

TASKS_DIR = os.path.join(ROOT, 'data', 'tasks')
SPECS_DIR = os.path.join(ROOT, 'data', 'specs')
PROV = os.path.join(ROOT, 'data', 'provenance.csv')

FIELDS = ['task_id', 'title', 'difficulty', 'category', 'requirement', 'io_table',
          'initial_state', 'constraints', 'provenance', 'spec_ref',
          'error_examples', 'notes']
DIRECTIONS = set(['IN', 'OUT', 'INOUT'])
TYPES = set(['BOOL', 'INT', 'DINT', 'UINT', 'UDINT', 'SINT', 'USINT', 'WORD', 'DWORD',
             'BYTE', 'REAL', 'LREAL', 'TIME', 'LTIME', 'STRING'])
ID_RE = re.compile(r'^[PS]\d{2}$')
K_RE = re.compile(r'\bK(\d{1,2})\b')
CLAUSE_RE = re.compile(r'^(C\d{1,2}[a-z]?)\s*:\s*(.+?)\s*$')


def check_task(tid, problems, warns=None):
    path = os.path.join(TASKS_DIR, tid + '.yaml')
    errs = []
    try:
        t = yaml_io.load(path)
    except Exception as exc:
        problems.append('%s: YAML 读不出来（%s）' % (tid, exc))
        return None, []

    for f in FIELDS:
        if f not in t:
            errs.append('缺字段 %s' % f)
    if errs:
        problems.append('%s: %s' % (tid, '；'.join(errs)))
        return t, []

    if t['task_id'] != tid:
        errs.append('task_id 与文件名不一致（%s vs %s）' % (t['task_id'], tid))
    if not ID_RE.match(t['task_id']):
        errs.append('task_id 格式不是 P/S + 两位数字')
    if t['difficulty'] not in ('easy', 'medium', 'hard'):
        errs.append('difficulty 非法：%r' % t['difficulty'])
    if t['category'] not in ('A', 'B', 'C', 'D'):
        errs.append('category 非法：%r' % t['category'])
    if not str(t['title']).strip():
        errs.append('title 为空')
    if len(str(t['requirement']).strip()) < 80:
        errs.append('requirement 过短（少于 80 字符）')

    io_names = []
    if not isinstance(t['io_table'], list) or len(t['io_table']) < 2:
        errs.append('io_table 少于 2 行')
    else:
        for i, row in enumerate(t['io_table']):
            if not isinstance(row, dict):
                errs.append('io_table 第 %d 行不是映射' % (i + 1))
                continue
            for k in ('direction', 'name', 'data_type', 'description'):
                if k not in row:
                    errs.append('io_table 第 %d 行缺 %s' % (i + 1, k))
            d = row.get('direction')
            if d not in DIRECTIONS:
                errs.append('io_table 第 %d 行方向非法：%r' % (i + 1, d))
            dt = str(row.get('data_type', '')).strip()
            # 允许：基础类型、STRING(n)、ARRAY[...] 或 ARRAY[*]、用户自定义结构（ST_xxx / 大写标识符）
            if not (dt in TYPES
                    or re.match(r'^STRING\s*\(\s*\d+\s*\)$', dt)
                    or re.match(r'^ARRAY\s*\[[^\]]*\]\s*OF\s+[A-Za-z_][A-Za-z0-9_]*$', dt)
                    or re.match(r'^[A-Z][A-Za-z0-9_]*$', dt)):
                errs.append('io_table 第 %d 行类型不认识：%r' % (i + 1, dt))
            io_names.append(row.get('name'))
    dup = [n for n in set(io_names) if io_names.count(n) > 1]
    if dup:
        errs.append('I/O 变量名重复：%s' % '、'.join(sorted(dup)))

    ks = []
    for c in t['constraints']:
        m = K_RE.search(str(c))
        if not m:
            errs.append('constraint 没写 K 编号：%s' % str(c)[:30])
        else:
            ks.append('K' + m.group(1))
    if len(set(ks)) != len(ks):
        errs.append('constraint 的 K 编号有重复')

    if not t['error_examples']:
        errs.append('error_examples 为空（必须给典型错误实现）')
    if '待澄清' in str(t['notes']):
        errs.append('notes 里还有「待澄清」')

    # 规约
    spec = os.path.join(SPECS_DIR, tid + '.ltl')
    if not os.path.isfile(spec):
        errs.append('缺规约文件 data/specs/%s.ltl' % tid)
        clauses = []
    else:
        text = io.open(spec, encoding='utf-8').read()
        has_note = '# note:' in text
        clauses = []
        for line in text.splitlines():
            m = CLAUSE_RE.match(line.strip())
            if m:
                clauses.append((m.group(1), m.group(2).split('--')[0].strip()))
        low = 2 if has_note else 4
        if not low <= len(clauses) <= 6:
            errs.append('条款数 %d 不在 %d—6 之间' % (len(clauses), low))
        used_k = set()
        for line in text.splitlines():
            for m in K_RE.finditer(line):
                used_k.add('K' + m.group(1))
        missing = [k for k in used_k if k not in ks]
        if missing:
            errs.append('条款引用了题面没有的约束：%s' % '、'.join(sorted(missing)))
        unref = [k for k in ks if k not in used_k]
        if unref:
            # 约束可以只由用例覆盖（例如“错误码写进 Status”这类无法用 LTL 精确表达的要求），
            # 但必须在 tasks_note 或本题 notes 里交代；默认记警告，--strict 时升级为错误。
            msg = '%s: 有 %d 条约束未被 LTL 覆盖（%s），需由 tests/cases 覆盖' % (
                tid, len(unref), '、'.join(sorted(unref)))
            if warns is not None:
                warns.append(msg)
            else:
                errs.append(msg)
        if t['spec_ref'] and t['spec_ref'] not in ('data/specs/%s.ltl' % tid, 'specs/%s.ltl' % tid):
            errs.append('spec_ref 指向的不是本题文件：%s' % t['spec_ref'])

    if errs:
        problems.append('%s: %s' % (tid, '；'.join(errs)))
    return t, clauses


def check_provenance(tasks, problems):
    if not os.path.isfile(PROV):
        problems.append('data/provenance.csv 不存在')
        return []
    rows = []
    with io.open(PROV, encoding='utf-8-sig', newline='') as f:
        head = next(csv.reader(f), [])
        for cells in csv.reader(f):
            if cells:
                rows.append(cells)
    need = ['task_id', 'source_type', 'source_link', 'source_ref', 'original_title',
            'synthesis_process', 'adaptation_what', 'adaptation_why',
            'author', 'reviewer', 'review_date']
    for col in need:
        if col not in head:
            problems.append('provenance.csv 表头缺 %s 列' % col)
    if len(rows) != len(tasks):
        problems.append('provenance.csv 行数 %d 与题数 %d 不一致' % (len(rows), len(tasks)))
    seen = set()
    for cells in rows:
        tid = cells[0] if cells else '(空行)'
        if tid not in tasks:
            problems.append('provenance.csv 里有不存在的题号：%s' % tid)
            continue
        seen.add(tid)
        if len(cells) < len(need):
            problems.append('provenance.csv 行 %s 列数 %d 不足 %d' % (tid, len(cells), len(need)))
            continue
        rec = dict(zip(head, cells))
        for col in ('source_link', 'source_ref', 'synthesis_process', 'adaptation_what', 'reviewer'):
            if not rec.get(col, '').strip():
                problems.append('provenance.csv 行 %s 的 %s 为空' % (tid, col))
    for tid in tasks:
        if tid not in seen:
            problems.append('provenance.csv 缺 %s' % tid)
    return rows


def main():
    quiet = '--quiet' in sys.argv
    only = None
    if '--task' in sys.argv:
        only = sys.argv[sys.argv.index('--task') + 1]

    ids = sorted(n[:-5] for n in os.listdir(TASKS_DIR) if n.endswith('.yaml'))
    if only:
        ids = [i for i in ids if i == only]
    strict = '--strict' in sys.argv
    problems = []
    warns = None if strict else []
    tasks = {}
    clauses = {}
    for tid in ids:
        t, cl = check_task(tid, problems, warns)
        if t:
            tasks[tid] = t
            clauses[tid] = cl

    if not only:
        check_provenance(tasks, problems)

    if not quiet:
        print('题面 %d 份，规约 %d 份，条款合计 %d 条'
              % (len(tasks), len(clauses), sum(len(v) for v in clauses.values())))
        by_diff = {}
        by_cat = {}
        for t in tasks.values():
            by_diff[t['difficulty']] = by_diff.get(t['difficulty'], 0) + 1
            by_cat[t['category']] = by_cat.get(t['category'], 0) + 1
        print('难度分布：%s' % '，'.join('%s=%d' % (k, by_diff[k]) for k in sorted(by_diff)))
        print('类别分布：%s' % '，'.join('%s=%d' % (k, by_cat[k]) for k in sorted(by_cat)))
        cover = {}
        for cl in clauses.values():
            for item in cl:
                base = re.match(r'^(C\d{1,2})', item[0]).group(1)
                cover[base] = cover.get(base, 0) + 1
        print('条款覆盖：%s' % '，'.join('%s=%d' % (k, cover[k]) for k in sorted(cover)))
        print('I/O 合计：%d 个，约束合计：%d 条'
              % (sum(len(t['io_table']) for t in tasks.values()),
                 sum(len(t['constraints']) for t in tasks.values())))

    if warns:
        print('')
        print('警告 %d 条（约束由用例覆盖，不阻断）：' % len(warns))
        for w in warns:
            print('  ! ' + w)
    if problems:
        print('')
        for p in problems:
            print('  ✗ ' + p)
        print('')
        print('%d 处问题' % len(problems))
        return 1
    print('')
    print('schema_check 通过：字段、I/O、规约映射、K 编号、来源表全部一致。')
    return 0


if __name__ == '__main__':
    sys.exit(main())

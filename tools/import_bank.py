# -*- coding: utf-8 -*-
"""import_bank.py -- 把官方题库 JSON 与选题记录合成为 32 份任务卡（YAML）

输入：
  refs/tiku_json/大作业题库json/大作业题库.json   （官方说明书原文，含 I/O 表）
  tools/curation_public.py                       （20 道公共题的人工校对字段）
  tools/curation_self.py                         （12 道自编题的完整内容）
输出：
  data/tasks/P01.yaml ... P20.yaml, S01.yaml ... S12.yaml

设计原则：
1. 变量名、数据类型、英文需求**逐字保留**，不翻译、不改大小写——Agent 生成的
   代码要与 I/O 表对得上，改名就是下游全部返工。
2. 机器只做搬运，人做三件事：补中文摘要、补初始态与约束、写错误示例。
3. 输出的每一份都必须通过 tools/schema_check.py，否则不许进 data/tasks/。

用法：
    python tools/import_bank.py            # 生成全部 32 份
    python tools/import_bank.py --check    # 只校验不写盘
"""

import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import yaml_io
from curation_public import PUBLIC, COMMON_SCAN
from curation_self import SELF

BANK = os.path.join(ROOT, 'refs', 'tiku_json', '大作业题库json', '大作业题库.json')
OUT_DIR = os.path.join(ROOT, 'data', 'tasks')

REQUIRED = ['task_id', 'title', 'difficulty', 'category', 'requirement', 'io_table',
            'initial_state', 'constraints', 'provenance', 'spec_ref',
            'error_examples', 'notes']

DIRECTION_ZH = {'IN': '输入', 'OUT': '输出', 'INOUT': '输入输出'}


def strip_ticks(s):
    return s.replace('`', '').strip()


def norm_direction(raw, desc):
    """把题库里五花八门的方向列归一成 IN / OUT / INOUT。

    题库实际出现过的写法：Input、Output、Input/Output、Input field、
    Output field，以及只有 Field/Data Type/Description 三列的表（方向靠
    描述里的 Read-only to the function block / written by the function
    block 判断）。
    """
    d = strip_ticks(raw).lower()
    if d.startswith('input/output') or d.startswith('inout'):
        return 'INOUT'
    if d.startswith('input'):
        return 'IN'
    if d.startswith('output'):
        return 'OUT'
    # 三列表：方向写在描述里
    low = desc.lower()
    if 'written by the function block' in low:
        return 'OUT'
    if 'read-only to the function block' in low:
        return 'IN'
    return 'IN'


def parse_task(md):
    """从一份 markdown 里抽出标题、难度、需求正文、I/O 表。"""
    lines = md.splitlines()
    title = ''
    difficulty = ''
    for ln in lines:
        s = ln.strip()
        if s.startswith('# ') and not title:
            title = s[2:].strip()
        m = re.search(r'Difficulty:\*{0,2}\s*([A-Za-z]+)', s)
        if m and not difficulty:
            difficulty = m.group(1).lower()

    # 需求正文：## Requirements 之后、## Interface Definition 之前
    req_start = md.find('## Requirements')
    req_end = md.find('## Interface Definition')
    if req_start < 0 or req_end < 0:
        raise ValueError('题库条目缺少 Requirements 或 Interface Definition 段：%s' % title)
    body = md[req_start + len('## Requirements'):req_end]
    req_lines = []
    for ln in body.splitlines():
        s = ln.rstrip()
        if s.strip().startswith('- **Difficulty'):
            continue
        req_lines.append(s)
    req_text = '\n'.join(req_lines).strip()
    req_text = re.sub(r'\n{3,}', '\n\n', req_text)

    # I/O 表：所有以 | 开头的行，跳过表头与分隔行
    io_rows = []
    for ln in md[req_end:].splitlines():
        s = ln.strip()
        if not s.startswith('|'):
            continue
        cells = [c.strip() for c in s.strip('|').split('|')]
        if not cells or set(''.join(cells)) <= set('-: '):
            continue
        head = strip_ticks(cells[0]).lower()
        if head in ('direction', 'field', 'input', 'output') and len(cells) >= 4 and \
                strip_ticks(cells[2]).lower() in ('data type',):
            continue
        if head == 'direction':
            continue
        if len(cells) == 4:
            name, dtype, desc = cells[1], cells[2], cells[3]
            direction = norm_direction(cells[0], desc)
        elif len(cells) == 3:
            name, dtype, desc = cells[0], cells[1], cells[2]
            direction = norm_direction('', desc)
        else:
            continue
        name = strip_ticks(name)
        dtype = strip_ticks(dtype)
        if not name or not dtype:
            continue
        # 三列表里偶有第二行表头漏进来（Field | Data Type | Description）
        if dtype.lower() in ('data type', 'datatype') or name.lower() in ('field', 'variable/field', 'name'):
            continue
        io_rows.append({
            'direction': direction,
            'name': name,
            'data_type': dtype,
            'description': strip_ticks(desc),
        })
    if not io_rows:
        raise ValueError('题库条目没有解析出 I/O：%s' % title)
    return {
        'title': title,
        'difficulty': difficulty,
        'requirement': req_text,
        'io_table': io_rows,
    }


def build_public():
    data = json.load(open(BANK, encoding='utf-8'))
    tasks = []
    idx = 0
    for level in ('easy', 'medium', 'hard'):
        for md in data[level]:
            idx += 1
            tid = 'P%02d' % idx
            parsed = parse_task(md['en'])
            cur = PUBLIC.get(tid)
            if cur is None:
                raise KeyError('curation_public.py 缺少 %s' % tid)
            if parsed['difficulty'] and parsed['difficulty'] != level:
                raise ValueError('%s 难度不一致：题库标 %s，分层键为 %s' % (tid, parsed['difficulty'], level))
            tasks.append({
                'task_id': tid,
                'title': parsed['title'],
                'difficulty': level,
                'category': cur['category'],
                'requirement': parsed['requirement'] + '\n\n中文摘要：' + cur['zh_summary'] + '\n\n扫描周期：' + COMMON_SCAN,
                'io_table': parsed['io_table'],
                'initial_state': cur['initial_state'],
                'constraints': cur['constraints'],
                'provenance': '课程公共题库 %s（%s）；原文导入、变量名与需求未做任何改动；来源与审核记录见 data/provenance.csv 第 %d 行'
                              % (tid, parsed['title'], idx + 1),
                'spec_ref': 'data/specs/%s.ltl' % tid,
                'error_examples': cur['error_examples'],
                'notes': cur['notes'],
            })
    return tasks


def _clip(text):
    """去掉句末标点，避免拼接出「。；」这种双标点。"""
    return text.strip().rstrip('。；;.')


def build_self():
    tasks = []
    for tid in sorted(SELF):
        s = SELF[tid]
        io_table = [{
            'direction': d,
            'name': n,
            'data_type': t,
            'description': desc,
        } for (d, n, t, desc) in s['io_table']]
        row = int(tid[1:]) + 21
        tasks.append({
            'task_id': tid,
            'title': s['title'],
            'difficulty': s['difficulty'],
            'category': s['category'],
            'requirement': s['requirement'].strip() + '\n\n扫描周期：' + COMMON_SCAN,
            'io_table': io_table,
            'initial_state': s['initial_state'],
            'constraints': s['constraints'],
            'provenance': '%s（%s）；改编点：%s；为什么这样改：%s；来源与审核记录见 data/provenance.csv 第 %d 行'
                          % (s['source_type'], s['source_ref'],
                             _clip(s['adaptation_what']), _clip(s['adaptation_why']), row),
            'spec_ref': 'data/specs/%s.ltl' % tid,
            'error_examples': s['error_examples'],
            'notes': s['notes'],
        })
    return tasks


def validate(t):
    problems = []
    for k in REQUIRED:
        if k not in t:
            problems.append('缺字段 %s' % k)
    if t.get('difficulty') not in ('easy', 'medium', 'hard'):
        problems.append('difficulty 非法：%r' % t.get('difficulty'))
    if t.get('category') not in ('A', 'B', 'C', 'D'):
        problems.append('category 非法：%r' % t.get('category'))
    if not re.match(r'^(P\d{2}|S\d{2})$', t.get('task_id', '')):
        problems.append('task_id 不合规')
    io = t.get('io_table') or []
    if len(io) < 2:
        problems.append('I/O 少于 2 个')
    names = [r['name'] for r in io]
    if len(names) != len(set(names)):
        problems.append('I/O 变量重名')
    for r in io:
        if r['direction'] not in DIRECTION_ZH:
            problems.append('方向非法：%r' % r['direction'])
        if not r['data_type']:
            problems.append('数据类型为空：%s' % r['name'])
    if not t.get('constraints'):
        problems.append('constraints 为空')
    if not t.get('error_examples'):
        problems.append('error_examples 为空')
    if '待澄清' in (t.get('notes') or ''):
        problems.append('notes 里还有待澄清项')
    return problems


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true', help='只校验，不写盘')
    args = ap.parse_args()

    tasks = build_public() + build_self()
    if len(tasks) != len(PUBLIC) + len(SELF):
        raise SystemExit('题目数 %d 与选题记录 %d 不一致' % (len(tasks), len(PUBLIC) + len(SELF)))

    bad = 0
    for t in tasks:
        pros = validate(t)
        if pros:
            bad += 1
            print('!! %s: %s' % (t['task_id'], '；'.join(pros)))
    if bad:
        raise SystemExit('%d 份题面不合格，未写盘' % bad)

    if not args.check:
        os.makedirs(OUT_DIR, exist_ok=True)
        for t in tasks:
            path = os.path.join(OUT_DIR, t['task_id'] + '.yaml')
            yaml_io.dump(t, path)

    by_cat = {}
    by_diff = {}
    io_total = 0
    cons_total = 0
    for t in tasks:
        by_cat[t['category']] = by_cat.get(t['category'], 0) + 1
        by_diff[t['difficulty']] = by_diff.get(t['difficulty'], 0) + 1
        io_total += len(t['io_table'])
        cons_total += len(t['constraints'])
    print('题面 %d 份（P %d + S %d）' % (
        len(tasks), len([t for t in tasks if t['task_id'].startswith('P')]),
        len([t for t in tasks if t['task_id'].startswith('S')])))
    print('类别分布：' + '，'.join('%s=%d' % (k, by_cat[k]) for k in sorted(by_cat)))
    print('难度分布：' + '，'.join('%s=%d' % (k, by_diff[k]) for k in ('easy', 'medium', 'hard')))
    print('I/O 变量合计 %d 个，约束合计 %d 条' % (io_total, cons_total))
    if not args.check:
        print('已写入 %s' % OUT_DIR)


if __name__ == '__main__':
    main()

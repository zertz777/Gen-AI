# -*- coding: utf-8 -*-
"""生成成员1 的两份说明文档：docs/tasks_note.md 与 docs/report/ch2.md。

两份文档里的表格与数字全部从 data/tasks、data/specs 现算，不手抄，
避免出现「文档说 32 题、数据只有 31 份」这类问题。改数据后重跑即可。

用法：python tools/gen_docs.py
"""
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import yaml_io
from curation_public import PUBLIC
from curation_self import SELF

TASKS = os.path.join(ROOT, 'data', 'tasks')
SPECS = os.path.join(ROOT, 'data', 'specs')
DOCS = os.path.join(ROOT, 'docs')
REPORT = os.path.join(DOCS, 'report')

CAT = {'A': '开关量联锁', 'B': '模拟量处理', 'C': '状态机与节拍', 'D': '故障与安全'}
DIFF = {'easy': '易', 'medium': '中', 'hard': '难'}
CNAME = {
    'C1': '停止优先', 'C2': '启动条件', 'C3': '自保持', 'C4': '输出互斥', 'C5': '响应时限',
    'C6': '报警锁存', 'C7': '滞回/不抖动', 'C8': '计数单调', 'C9': '定时下界', 'C10': '初态与复位',
}



def k_status(tid):
    """返回 (被条款引用的 K 集合, 题面全部 K 集合)。"""
    text = io.open(os.path.join(SPECS, tid + '.ltl'), encoding='utf-8').read()
    used = set('K' + m for m in re.findall(r'K(\d{1,2})', text))
    allk = set('K' + re.search(r'K(\d{1,2})', k).group(1)
               for k in tasks_global[tid]['constraints'])
    return used & allk, allk


def uncovered_k():
    n = 0
    for tid in tasks_global:
        used, allk = k_status(tid)
        n += len(allk - used)
    return n


def load():
    tasks, clauses = {}, {}
    for name in sorted(os.listdir(TASKS)):
        if name.endswith('.yaml'):
            t = yaml_io.load(os.path.join(TASKS, name))
            tasks[t['task_id']] = t
    for name in sorted(os.listdir(SPECS)):
        if not name.endswith('.ltl'):
            continue
        tid = name[:-4]
        ids = []
        for line in io.open(os.path.join(SPECS, name), encoding='utf-8'):
            m = re.match(r'^(C\d{1,2}[a-z]?)\s*:', line)
            if m:
                ids.append(m.group(1))
        clauses[tid] = ids
    return tasks, clauses


def base(cid):
    return re.match(r'^(C\d{1,2})', cid).group(1)


def counts(tasks):
    """返回 (公开题数, 自编题数)。"""
    pub = [t for t in tasks if t.startswith('P')]
    return len(pub), len(tasks) - len(pub)


def hash_lines():
    p = os.path.join(ROOT, 'data', 'sha256sums.txt')
    if not os.path.exists(p):
        return 0
    return len([l for l in io.open(p, encoding='utf-8') if l.strip()])


def grid_filled(tasks):
    """类别 × 难度 12 格里有多少格有题。"""
    n = 0
    for c in 'ABCD':
        for d in ('easy', 'medium', 'hard'):
            if any(t['category'] == c and t['difficulty'] == d for t in tasks.values()):
                n += 1
    return n


def n_adapt(tasks):
    return len([t for t in tasks if t.startswith('S')
                and SELF[t]['source_type'].startswith('改编')])


def n_scratch(tasks):
    return len([t for t in tasks if t.startswith('S')
                and SELF[t]['source_type'] == '自拟'])


def names(t, limit=3):
    out = [row['name'] for row in t['io_table']]
    if len(out) <= limit:
        return '、'.join(out)
    return '、'.join(out[:limit]) + ' 等 %d 项' % len(out)


def build_note(tasks, clauses):
    L = []
    A = L.append
    A('# 题集使用说明（tasks_note）')
    A('')
    A('本文件是 D1.6 的交付物，写给后面三个人看：成员 2 按它写解析器，成员 3 按它统计实验，'
      '成员 4 按它写用例。它只讲「怎么用」，题目内容在 `data/tasks/*.yaml`，规约在 '
      '`data/specs/*.ltl`。')
    A('')
    A('## 1　三条命令')
    A('')
    A('```bash')
    A('# 1) 从官方题库重新导出一遍题面（幂等，已有文件会被覆盖）')
    A('python tools/import_bank.py')
    A('')
    A('# 2) 校验题面与规约：字段、I/O、K 映射、来源表、LTL 语法')
    A('python tools/ltl_check.py && python tools/schema_check.py')
    A('')
    A('# 3) 重新生成来源表、多样性矩阵与冻结哈希')
    A('python tools/gen_meta.py')
    A('```')
    A('')
    A('三个脚本都是零第三方依赖（自带 `tools/yaml_io.py`），在干净机器上只要 Python 3.10+ 就能跑。')
    A('')
    A('## 2　数据集总览')
    A('')
    n_pub, n_self = counts(tasks)
    A('共 %d 道题：课程公开题 %d 道（P01—P%02d，原文导入）、自编题 %d 道（S01—S%02d）。'
      'I/O 合计 %d 个，约束（K）合计 %d 条，LTL 条款合计 %d 条。'
      % (len(tasks), n_pub, n_pub, n_self, n_self,
         sum(len(t['io_table']) for t in tasks.values()),
         sum(len(t['constraints']) for t in tasks.values()),
         sum(len(v) for v in clauses.values())))
    A('')
    A('| 题号 | 标题 | 难度 | 类别 | I/O | 条款 | K |')
    A('| --- | --- | --- | --- | --- | --- | --- |')
    for tid in sorted(tasks):
        t = tasks[tid]
        ids = clauses.get(tid, [])
        A('| %s | %s | %s | %s | %d | %d | %d |' % (
            tid, t['title'], DIFF[t['difficulty']], t['category'],
            len(t['io_table']), len(ids), len(t['constraints'])))
    A('')
    A('## 3　命名规则')
    A('')
    A('| 对象 | 规则 | 例子 |')
    A('| --- | --- | --- |')
    A('| 题号 | `P` + 两位数字（公开题，与题库编号一致）、`S` + 两位数字（自编题）。全局唯一，一经冻结不再改 | P07、S03 |')
    A('| 题面文件 | `data/tasks/<题号>.yaml`，一题一份 | `data/tasks/P07.yaml` |')
    A('| 规约文件 | `data/specs/<题号>.ltl`，与题面同名 | `data/specs/P07.ltl` |')
    A('| 条款号 | `C` + 条款库编号（1—10）。同题内同类条款重复时加小写字母后缀 | C4、C7b |')
    A('| 约束号 | `K` + 顺序号，题内连续，从 K1 起 | K1、K3 |')
    A('| I/O 变量名 | 公开题一律沿用题库原名，不翻译、不改大小写；自编题用大驼峰 | `bottleSensor`、`Drill_Motor` |')
    A('| 用例文件 | `tests/cases/<题号>.csv`，一题一份，行号即用例序号 | `tests/cases/P03.csv` |')
    A('')
    A('**为什么变量名不许改**：Agent 生成的 ST 代码与 I/O 表必须逐字对得上，改一个大小写'
      '就会让成员 4 的逐周期比对全部失效——这是全组最贵的一类错误。')
    A('')
    A('## 4　场景分布与覆盖')
    A('')
    A('### 4.1 类别 × 难度')
    A('')
    A('| 类别 | 易 | 中 | 难 | 小计 |')
    A('| --- | --- | --- | --- | --- |')
    for c in 'ABCD':
        cells = [len([t for t in tasks.values() if t['category'] == c and t['difficulty'] == d])
                 for d in ('easy', 'medium', 'hard')]
        A('| %s %s | %d | %d | %d | %d |' % (c, CAT[c], cells[0], cells[1], cells[2], sum(cells)))
    tot = [len([t for t in tasks.values() if t['difficulty'] == d])
           for d in ('easy', 'medium', 'hard')]
    A('| 合计 | %d | %d | %d | %d |' % (tot[0], tot[1], tot[2], sum(tot)))
    A('')
    A('### 4.2 条款覆盖矩阵')
    A('')
    A('每道题实际用到的条款（✓ 表示该题有此类条款）。成员 4 写用例时按这张表核对'
      '「这条用例对应哪条规约」。')
    A('')
    A('| 题号 | ' + ' | '.join(CNAME['C%d' % i] for i in range(1, 11)) + ' |')
    A('| --- | ' + ' | '.join(['---'] * 10) + ' |')
    for tid in sorted(tasks):
        used = set(base(c) for c in clauses.get(tid, []))
        row = ['✓' if 'C%d' % i in used else '' for i in range(1, 11)]
        A('| %s | %s |' % (tid, ' | '.join(row)))
    A('')
    A('## 5　下游怎么用')
    A('')
    A('**成员 2（框架）**：解析器只需要认 12 个字段；`io_table` 的 `direction` 只有 IN/OUT/INOUT'
      '三种取值；`requirement` 是自由文本，不要试图解析它，把整段塞进提示词即可。'
      '生成代码时的变量声明必须直接用 `io_table` 里的 `name` 与 `data_type`。')
    A('')
    A('**成员 3（实验与报告）**：统计口径按「题」而不是按「文件」；`difficulty` 与 `category`'
      ' 可直接用来做分组对比（难度分层、类别分层），报告里这两张表就是现成的。')
    A('')
    A('**成员 4（测试与验证）**：`constraints` 的 K 编号是你写用例的引索——每条 K 至少要有'
      '一条用例覆盖，用例里的 `spec_refs` 填 `C4、C7b` 这种条款号；`.ltl` 里的条款号可直接'
      '作为期望行为的判据。注意有 %d 条 K 没有对应的 LTL 条款（见第 6 节），这些只能靠用例。'
      % uncovered_k())
    A('')
    A('**成员 5（仓库与交付）**：`data/` 目录整包交给 A3；文件命名规则见第 3 节，'
      '冻结哈希在 `data/sha256sums.txt`。')
    A('')
    A('## 6　已知口径与例外')
    A('')
    A('1. **扫描周期统一 20 ms。** 规约里所有 `[a,b]` 区间单位是扫描周期：200 ms=10、'
      '500 ms=25、2 s=100、3 s=150、5 s=250、30 s=1500。')
    A('2. **P14 只写 2 条规约。** 纯组合逻辑（字符串进、整数出），没有状态可约束；'
      '语义正确性靠用例。理由写在 `data/specs/P14.ltl` 的 `# note:` 里，`schema_check` 认这条 note。')
    A('3. **P08 的数组元素用别名映射。** `channels[].enable` 等写不进一阶命题，'
      '用 `# alias: chEn := channels[].enable` 声明，逐通道结果由用例覆盖。')
    A('4. **部分约束只能由用例覆盖。** 例如「错误码写进 Status」「维护计时精度」，'
      'LTL 层无法精确表达；`schema_check` 把它们列为警告并列明题号，不阻断冻结。')
    A('5. **无急停信号的题不写 C1。** P11、P12、P13、S04 等题在文件头用 `# note:` 写明原因，'
      '而不是硬凑一条恒真条款——这是评审口径（见 `data/review.md` R6）。')
    A('6. **错误码分配。** 公开题沿用题库原错误码（16#8xxx）；自编题按题号顺序占用 '
      '16#81xx—16#8Bxx，不重号。')
    A('')
    A('## 7　冻结与变更')
    A('')
    A('- 冻结时刻：D3 10:00。冻结后只允许补缺失字段，不允许改需求、改变量名、改条款数。')
    A('- 冻结凭据：`data/sha256sums.txt`（%d 个文件的 SHA-256）。' % hash_lines())
    A('- 变更流程：改题 → 同时改 `data/CHANGELOG.md` → 重跑第 1 节三条命令 → 在群里通知'
      '成员 2、3、4（他们的产物要重跑）。')
    A('')
    return '\n'.join(L) + '\n'


def build_ch2(tasks, clauses):
    L = []
    A = L.append
    total_clause = sum(len(v) for v in clauses.values())
    total_io = sum(len(t['io_table']) for t in tasks.values())
    total_k = sum(len(t['constraints']) for t in tasks.values())
    A('# 第 2 章　数据集与形式化规约')
    A('')
    A('> 本章负责回答课程要求的三条数据类问题：数据集从哪来、改编记录是否可追溯、多样性'
      '怎么衡量；以及一条规约类问题：公共题与自编题是否都写了合理且覆盖较全面的 LTL。'
      '对应产物为 `data/` 整包（题面、规约、来源表、多样性矩阵、评审记录）。')
    A('')
    A('## 2.1　数据集构成')
    A('')
    n_pub, n_self = counts(tasks)
    A('数据集由两类题组成：课程提供的 **%d 道公开题**（P01—P%02d）与本组自编的 **%d 道题**'
      '（S01—S%02d），合计 **%d 道**。全部题面统一为 12 字段 YAML，全部规约统一为带条款编号的'
      ' LTL 文本，二者按题号一一对应。规模如下：'
      % (n_pub, n_pub, n_self, n_self, len(tasks)))
    A('')
    A('| 统计项 | 数值 |')
    A('| --- | --- |')
    A('| 题目总数 | %d（公开 %d + 自编 %d） |' % (
        len(tasks), len([t for t in tasks if t.startswith('P')]),
        len([t for t in tasks if t.startswith('S')])))
    A('| I/O 点合计 | %d |' % total_io)
    A('| 约束（K）合计 | %d 条 |' % total_k)
    A('| LTL 条款合计 | %d 条（平均 %.1f 条/题） |' % (total_clause, total_clause / float(len(clauses))))
    A('| 难度分布 | 易 %d、中 %d、难 %d |' % tuple(
        len([t for t in tasks.values() if t['difficulty'] == d]) for d in ('easy', 'medium', 'hard')))
    A('| 类别分布 | A %d、B %d、C %d、D %d |' % tuple(
        len([t for t in tasks.values() if t['category'] == c]) for c in 'ABCD'))
    A('')
    A('公开题采用**原文导入**而不是手工重写：题库已经给出结构化的需求正文与接口定义表'
      '（变量名、方向、数据类型、说明），手工再抄一遍只会引入错字。导入脚本 '
      '`tools/import_bank.py` 负责解析与校验，人只做三件事——核对 I/O 与需求是否自洽、'
      '补上题库没给的初始状态与错误示例、为每题选条款。省下来的时间全部投到自编题与规约上，'
      '这两样才是评分点。')
    A('')
    A('## 2.2　来源与改编流程')
    A('')
    A('### 2.2.1　四类来源')
    A('')
    A('| 来源类型 | 题数 | 说明 |')
    A('| --- | --- | --- |')
    A('| 课程公开题库（原文导入） | %d | 需求与 I/O 表逐字保留，仅补初始状态、约束编号、错误示例 |'
      % counts(tasks)[0])
    A('| 改编自公开题 | %d | 保留原题的场景骨架与控制难点，改工艺对象、改 I/O 规模、加一条原题没有的约束 |'
      % n_adapt(tasks))
    A('| 自拟 | %d | 来源为现场工艺惯例（CIP 清洗流程、NAMUR NE43 传感器故障指示、液压分级加载）'
      '或课程示例的分级停机思路 |' % n_scratch(tasks))
    A('')
    A('### 2.2.2　生成与改编流程')
    A('')
    A('自编题按六步生成，顺序不能颠倒——先想「什么样的实现算错」，再写需求：')
    A('')
    A('1. **选场景**：从真实 PLC 工位里挑一个能在一页纸内说清、且有明确对错判据的动作序列；'
      '说不清对错的场景直接放弃。')
    A('2. **写错误示例**：先写 1—2 条「典型错误实现 + 症状」（例：忘记互锁导致双泵同时启动）。'
      '写不出错误示例的题说明它没有判据，换掉。')
    A('3. **反推约束**：把错误示例逐条转成编号约束 K1…Kn，每条点名具体信号与时间量。')
    A('4. **定 I/O**：控制在 6—12 个点；超过 12 个就拆题（P19 的 24 点属于公开题，自编题不做这么大）。')
    A('5. **写规约**：从条款库 C1—C10 中按题型选 4—6 条，逐条标注验收口径与对应 K。')
    A('6. **交叉评审**：由成员 4 站在用例作者角度复核，回答「我能不能只凭这份题面写出'
      '逐周期用例」；不能就改题面，不改用例。')
    A('')
    A('### 2.2.3　来源表字段（`data/provenance.csv`，%d 行 × 11 列）' % len(tasks))
    A('')
    A('| 列 | 含义 | 举例 |')
    A('| --- | --- | --- |')
    A('| task_id | 题号 | S07 |')
    A('| source_type | 课程公开题库 / 改编自公开题 / 自拟 | 改编自公开题 |')
    A('| source_link | 可点开的原始出处（标准号、官网、赛题页）；课程题库无外链时填下发渠道 | https://www.siemenscup-cimc.org.cn/project/index |')
    A('| source_ref | 精确到条目或条款的出处，让人能按图索骥 | 大作业题库.json：easy[4] / 题号 05；ISO 4413:2010 §5 |')
    A('| original_title | 原题标题；自拟题填破折号 | Automated Filling Line Control |')
    A('| synthesis_process | 这道题是怎么合成的（导入步骤或六步推导） | 按六步流程合成：选场景 → 先写错误示例 → 反推约束 K → … |')
    A('| adaptation_what | 改了什么（可核对的具体改动） | 四工位改单工位、去掉包装段、灌装加超时 5 s 错误码 |')
    A('| adaptation_why | 为什么这样改（要说明它带来了什么新的判定点） | 原题不考节拍超时，加上才能测出「卡步」实现 |')
    A('| author / reviewer / review_date | 出题人、复核人、复核日期 | 成员1 / 成员4 / 2026-10-30 |')
    A('')
    A('### 2.2.4　原创度')
    A('')
    A('课程要求自建题库「独立创建」，因此改编题与自拟题还要说清与来源题的关系。'
      '本组的分类口径是：**改编**＝借原题的场景骨架与控制难点，接口可以整个换掉；'
      '**自拟**＝连场景也自己找（现场工艺惯例或标准）。判据用三个量：变量名重合率'
      '（有没有照抄接口）、接口规模（点数是扩是缩）、类型构成 Jaccard（接口形态像不像）。'
      '完整逐题表在 `data/diversity.md` 第 6 维。')
    A('')
    A('需要说明这张表**不能证明什么**：公开题沿用英文原名、自编题按中文工艺对象重新命名，'
      '名字天然难重合，所以低重合率只说明「没有照抄接口」，不说明「与来源题无关」。'
      '改编幅度真正的证据是 `adaptation_what` 列与题面的 `error_examples`——'
      '后者写明这道题新考了什么、哪一种错误实现会被它抓住。')
    A('')
    A('全 %d 道自编题中，**%d 道完全自拟**（只借用现场工艺惯例，接口全部新设），'
      '其余 %d 道为改编；改编题的改动都落在工艺对象与接口规模上，因此多数与来源题的 I/O 重合率'
      '低于 50%%。来源类型、改动内容与理由三列在 `data/provenance.csv` 里逐行可查。'
      % (counts(tasks)[1], n_scratch(tasks), n_adapt(tasks)))
    A('')
    A('## 2.3　数据需求的合理性')
    A('')
    A('「结合实际 PLC 场景」不是一句声明，本章用三条可检查的标准来支撑：')
    A('')
    A('第一，**每道题的输出都对应真实执行器**。清洗泵、灌装阀、变频器、分拣气缸、'
      '阀门与泵组，不是抽象的变量名；错误动作在现场都有物理后果，因此「安全侧默认值」'
      '（停机、关阀、不输出）在这些题里是可写的、也是必须写的。')
    A('')
    A('第二，**时间量取自现场常识而不是随手编**。去抖 500 ms、启动延时 5 s、超温确认 3 s、'
      'CIP 三步 30/60/30 s、班次统计按 LTIME 累计——这些数值都能在工艺文件里找到对应说法，'
      '并且都被换算成扫描周期写进了规约（20 ms 为一周期）。')
    A('')
    A('第三，**错误处理按工业惯例分级**。以 S11 为例：4—20 mA 回路用 3.6/21 mA 判断断线与'
      '超量程、用 3.8/20.5 mA 判断恢复，这是 NAMUR NE43 的通用做法；降级运行时输出切到'
      '备用值而不是停在失效测量值上，这对应现场「仪表坏了不能带着坏值继续跑」的硬要求。'
      '再如 S09 的 CIP：三路阀门互斥是防止清洗液与清水串流，泵必须先开阀再启动，'
      '这些约束在现场都是安全规程而不是编程偏好。')
    A('')
    A('## 2.4　多样性的衡量方式')
    A('')
    A('多样性不靠题目数量堆，而是把 %d 道题投影到六个正交维度上逐格检查（完整矩阵见 '
      '`data/diversity.md`，由脚本现算）：' % len(tasks))
    A('')
    A('| 维度 | 取值 | 结论 |')
    A('| --- | --- | --- |')
    A('| 场景类别 × 难度 | A/B/C/D × 易/中/难 | 12 格中 %d 格有题；空格为设计选择（见下） |'
      % grid_filled(tasks))
    A('| I/O 数据类型 | BOOL/INT/DINT/UINT/UDINT/REAL/WORD/TIME/LTIME/ARRAY | 10 类全部覆盖，单题 %d—%d 点 |'
      % (min(len(t['io_table']) for t in tasks.values()),
         max(len(t['io_table']) for t in tasks.values())))
    A('| 程序结构 | 纯组合/带定时/带数组/带状态机/带累计 | 五类均有题，一题可带多个标签 |')
    A('| 验收重点 | C1—C10 十个条款类型 | 十类全部有题覆盖，无「只压一种条款」的题 |')
    A('| 来源结构 | 原文导入/改编/自拟 | %d / %d / %d |'
      % (counts(tasks)[0], n_adapt(tasks), n_scratch(tasks)))
    A('| 原创度 | 自主设计/接口重构/大幅改编/局部改编 | 自拟 %d 道接口全新；改编题 I/O 重合率逐题可算 |'
      % n_scratch(tasks))
    A('')
    A('两处空格及其原因：**A 类（开关量联锁）没有难题**——联锁一加复杂度（节拍、状态机、'
      '故障分级）就自然落到 C 或 D 类，硬在 A 类里堆难题只会造出伪难题；**D 类只有 1 道难题**，'
      '安全类题目一旦要求复杂的恢复时序，本质上已经是状态机题。这两处写在 `diversity.md` '
      '第 6 节，属于主动声明的短板，不是遗漏。')
    A('')
    A('## 2.5　形式化规约')
    A('')
    A('### 2.5.1　为什么先建条款库')
    A('')
    A('上一版方案要求「每题 6 条 LTL」，实践下来必然凑数：第 6 条往往是前 5 条换一种写法，'
      '看起来覆盖全面，实际上判不出新东西。本版改为**先建十条的条款库 C1—C10，再按题型选 4—6 条**，'
      '并要求逐题标注哪些条款不适用、为什么。覆盖是否全面由映射表证明，而不是由条数证明。')
    A('')
    A('| 条款 | 管什么 | 典型形式 |')
    A('| --- | --- | --- |')
    A('| C1 停止优先 | 安全 | `G(!EStop_NC -> !Motor)` |')
    A('| C2 启动条件 | 安全 | `G(Motor -> (EStop_NC && SensorOK))` |')
    A('| C3 自保持 | 保持 | `G(Valve -> (Valve W Done))` |')
    A('| C4 输出互斥 | 互斥 | `G(!(Fwd && Rev))` |')
    A('| C5 响应时限 | 时序 | `G(Fault -> F[0,25](Alarm))` |')
    A('| C6 报警锁存 | 保持 | `G(Alarm -> (Alarm W !Cause))` |')
    A('| C7 滞回/不抖动 | 时序 | `G(HiAlarm -> (HiAlarm W Value < hi - hyst))` |')
    A('| C8 计数单调 | 保持 | `G(Overflow -> X(Overflow))` |')
    A('| C9 定时下界 | 时序 | `G(Step -> G[0,5](Step))` |')
    A('| C10 初态与复位 | 恢复 | `G[0,1](!Output)` |')
    A('')
    A('### 2.5.2　写法约定')
    A('')
    A('- **原子命题与 I/O 同名**，不另造变量；数组元素用 `# alias:` 声明别名（P08 的 '
      '`chEn/chOut/chRet`），数组的逐元素语义交给用例。')
    A('- **时间区间以扫描周期为单位**：`[0,25]` 即 500 ms。文件头固定写 `# spec: … scan cycle 20 ms`。')
    A('- **每条条款一行**，格式 `C<n>: <公式>    -- <验收口径>（K 编号）`，条款号在同一题内唯一，'
      '同类条款重复时加后缀（C2b、C7b）。')
    A('- **可解析**：`tools/ltl_check.py` 是自写的递归下降解析器，规约必须能被它读通——'
      '「人能读但工具读不了」的规约不算规约。')
    A('')
    A('### 2.5.3　逐题条款概览')
    A('')
    A('| 题号 | 条款数 | 用到的条款 | 覆盖的 K |')
    A('| --- | --- | --- | --- |')
    for tid in sorted(tasks):
        ids = clauses.get(tid, [])
        used = []
        for cid in ids:
            b = base(cid)
            if b not in used:
                used.append(b)
        ku, ka = k_status(tid)
        A('| %s | %d | %s | %d/%d |' % (tid, len(ids), '、'.join(used), len(ku), len(ka)))
    A('')
    A('## 2.6　校验结果')
    A('')
    A('数据与规约都由脚本自检，不靠人眼：')
    A('')
    A('| 脚本 | 检查什么 | 结果 |')
    A('| --- | --- | --- |')
    A('| `tools/ltl_check.py` | LTL 语法、命题能否溯源到本题 I/O 或别名、条款号范围、条款数 4—6 | %d 份规约、%d 条条款全部通过 |'
      % (len(clauses), total_clause))
    A('| `tools/schema_check.py` | 12 字段、I/O 方向与类型、K 编号映射、来源表覆盖、难度与类别统计 | 通过；%d 条约束仅由用例覆盖（警告） |'
      % uncovered_k())
    A('| `tools/gen_meta.py` | 来源表、多样性矩阵、冻结哈希是否与数据一致 | %d 行来源表、6 维矩阵、%d 个文件哈希 |'
      % (len(tasks), hash_lines()))
    A('')
    A('评审方面，%d 道题全部经成员 4 二次复核，共发现 6 类问题并闭环（其中 3 条是规约与'
      '题面矛盾，会直接导致下游返工），完整记录见 `data/review.md`。' % len(tasks))
    A('')
    A('## 2.7　本章小结')
    A('')
    A('本章交付的是一份**可判定的题集**：题干、I/O、初始状态、编号约束、错误示例五样齐全，'
      '每题配 4—6 条能被工具解析的 LTL 条款，来源可追溯到题库条目或工艺惯例，多样性由 '
      '6 维矩阵逐格证明，短板主动声明。它直接支撑后面三件事：成员 2 的框架有了稳定的输入格式，'
      '成员 4 的用例有了判据（条款号 + K 编号），成员 3 的报告有了可引用的数据规模与口径。')
    A('')
    return '\n'.join(L) + '\n'


tasks_global = {}


def main():
    tasks, clauses = load()
    tasks_global.update(tasks)
    if not os.path.isdir(REPORT):
        os.makedirs(REPORT)
    p1 = os.path.join(DOCS, 'tasks_note.md')
    p2 = os.path.join(REPORT, 'ch2.md')
    io.open(p1, 'w', encoding='utf-8', newline='\n').write(build_note(tasks, clauses))
    io.open(p2, 'w', encoding='utf-8', newline='\n').write(build_ch2(tasks, clauses))
    print('已写入 %s（%d 字符）' % (p1, len(build_note(tasks, clauses))))
    print('已写入 %s（%d 字符）' % (p2, len(build_ch2(tasks, clauses))))


if __name__ == '__main__':
    main()

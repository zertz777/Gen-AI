# 基于 Agent 的 PLC ST 代码生成与逐周期验证

课程期末大作业实验报告

[[TOC]]

# 摘要

本作业研究大语言模型能否在工业控制系统约束下生成可编译、可逐周期验证的 PLC Structured Text 程序。团队构建了 34 道题的数据集，其中 20 道来自课程公共题库，14 道为改编或自拟题；每题具有统一 YAML 字段、I/O 表、初始状态、编号约束和 LTL 规约，共形成 316 个 I/O、144 条约束和 177 条形式化条款。测试层包含 214 条正常、边界、异常和安全用例，以 20 ms 扫描周期逐拍比对，并使用缺陷单、变异测试和可选形式验证跟踪失败。

实验采用 2 x 2 设置：Aider 与自研 Agent 分别搭配 `deepseek-v4.1-flash` 和 `gpt-6.1-sol`，四组均覆盖全部 34 题，最终矩阵为 136 个 run。严格整题通过数分别为 E1 18/34、E2 16/34、E3 8/34、E4 7/34。结果说明，在这套题目、本机工具链和本次配置下，编译通过仍明显高于逐周期功能通过，Aider 组的严格整题通过数更高。该差异不能直接解释为算法普遍优劣：E3 有 24 题受预算终止影响，自研框架还存在字节长度误当 token 的预算实现问题；P19、S11、S05-06 的判据争议也尚未全部消除。

本作业的可复核贡献包括统一题集与形式化条款、具备生成与反馈闭环的 Agent、逐周期测试和缺陷追踪、四组可回指原始记录的实验，以及 Word/PDF、PPT 和 A1-A7 提交包。已知限制是换机完整复现尚未完成，精简实验包不包含全部逐拍 actual 中间文件，单次运行也不足以估计模型随机波动。结论只适用于当前冻结版本和实验条件。

关键词：工业编程；PLC；Structured Text；大语言模型；Agent；形式化规约；逐周期验证

# 报告内容与课程要求对照

本报告按课程要求组织为四部分，并在附录保留逐题形式化规约。

| 课程要求 | 报告位置 | 主要内容 |
| --- | --- | --- |
| 实验环境 | 第1章、3.3、3.5、3.9 | 软件与工具版本、两个模型配置、DMXAPI 与 Aider 接入、时间/上下文/token/并发限制 |
| 数据集与 Spec | 第2章、附录A | 34 题来源、导入与改编流程、五维/六维多样性、177 条 LTL 的逐题全文 |
| 自研框架设计 | 第3章、图3-1、图3-2 | 七模块架构、候选生成、双通道编译、局部修复、回归保护、终止条件和设计依据 |
| 实验结果与分析 | 第4章、图4-1至图4-4 | 2 框架 x 2 模型四组结果、难度分层、状态分布、耗时、token、失败归因和局限 |

# 第 1 章　实验环境与复现边界

本章登记正式实验实际使用的软件、模型和工具链。复现的目标不是让另一台电脑无条件产生完全相同的模型文本，而是让读者能判断当时用了什么、哪些步骤可以重算、哪些中间证据只存在于实验机，以及改变环境后哪些结论必须重新验证。

## 1.1 软件与模型

正式实验使用 CODESYS x64 3.5.22.40（V3.5 SP22 Patch 4）作为权威编译环境，目标设备为 CODESYS Control Win V3 x64。模板工程包含 Application、MainTask 和 20 ms 任务，核心库为 Standard 3.5.22.0 与 IoStandard 3.5.22.0。MATIEC 使用固定官方提交构建，承担快速语法检查；它不替代 CODESYS 的最终编译状态。

表 1-1 环境与版本

| 项目 | 版本或配置 |
| --- | --- |
| 操作系统 | Windows 64 位，10.0.26200 |
| Python | Agent 核心支持 3.10+；编译验收记录为 3.12.14 |
| CODESYS | 3.5.22.40，V3.5 SP22 Patch 4 |
| CODESYS Scripting | 4.2.0.0，IronPython 2.7 |
| 目标设备 | CODESYS Control Win V3 x64，type 4096，id 0000 0004 |
| 核心库 | Standard 3.5.22.0、IoStandard 3.5.22.0 |
| 扫描周期 | 20 ms |
| 基线 | Aider 0.86.2 |
| 模型 A | `deepseek-v4.1-flash` |
| 模型 B | `gpt-6.1-sol` |
| 模型接口 | DMXAPI Chat Completions |
| 单题超时 | 900 s |
| 权威编译超时 | 90 s |

硬件型号、CPU、内存和磁盘信息未在成员交接材料中留下可核对记录，因此本文不补写。正式实验在同一实验机上完成。换机复现需要重新记录硬件和软件，不能把本表直接视为已完成跨机验证。

## 1.2 编译工具链

编译器接入分两层。快通道调用 MATIEC，目标是在 3 s 内给出语法和类型诊断；权威通道复制专用 CODESYS 模板，导入 TYPE 和单个 POU，强制链接、重新构建并读取结构化消息。每个诊断统一为 `code / severity / line / message / raw`，警告与错误分开保存。

CODESYS 验收包括 6 个诊断探针和 34 个声明骨架。正确例、常量死分支和 4 个故意错误例均符合预期；34 个骨架中 33 个通过并生成目标代码，P18 因当前 profile 不支持 `VARIANT` 失败。该结果只证明接口与方言兼容性，不属于模型生成程序的编译通过率。

## 1.3 模型与基线

模型调用通过 DMXAPI 的 Chat Completions 格式完成。Key 从 `DMXAPI_API_KEY` 环境变量读取，不写入配置或日志。两个模型 ID 在正式矩阵中固定，不在不同组别间替换。Aider 0.86.2 作为现成 CLI Agent 基线，经 OpenAI-compatible 路由接入；它保留自身的上下文、编辑和反思策略，自研框架保留候选、局部补丁和回归保护策略。

公平比较依靠共同输入和共同判定：两框架使用同一 34 题、同一 I/O 与 LTL、同一 CODESYS 权威编译、同一成员4逐周期测试器、同一 900 s 外部超时和同一 22 字段日志契约。两种框架内部策略无法完全相同，这属于研究对象的一部分，也是结论必须限制在“本版配置”上的原因。

## 1.4 复现流程

无费用的最小验收包含三步：安装依赖、运行单题 fixture、运行 34 题 fixture。三条命令检查解析、上下文、候选、修复、终止和日志流程，不调用模型或 CODESYS，不能计入实验通过率。

真实重跑需要另外准备模型 Key、Aider 独立环境、CODESYS profile、模板工程和测试执行器。换机后必须先做声明骨架和诊断探针，再跑少量含失败样本，最后才可按四组配置生成新批次。新批次应使用新的目录和 run_id，不能覆盖本作业的 136 条最终记录。

## 1.5 证据边界

正式实验交付 136 个最终 run、32 个判据修订补跑和 104 个沿用首轮记录。每个 run 保留 result、metadata、候选评估、事件摘要和最终 ST；完整逐拍 actual 与编译中间工程只保存在实验机，精简包中没有。因此本仓库能重算汇总、定位到 run 和具体失配记录，但不能仅靠提交包重新执行全部 CODESYS 周期。

这一边界直接影响结论：编译与逐周期测试的结果可核验，模型服务端的状态和 complete actual 不能在本仓库内独立复现。报告中的 token、时延和通过数必须与这些限制一起阅读。

## 1.6 接入方式与资源限制

模型接入采用 DMXAPI 的 Chat Completions 兼容接口：base URL 为 `https://www.dmxapi.cn/v1`，请求路径为 `/chat/completions`，使用 `model/messages/stream=false` 的 JSON 请求，响应从 `choices[0].message.content` 提取 ST 源码。密钥只从环境变量 `DMXAPI_API_KEY` 读取。Aider 0.86.2 通过 OpenAI-compatible provider 和 `openai/` 模型路由进入同一判定流程。CODESYS 与成员4测试器通过命令行桥接入，分别提供权威编译结果和逐周期用例结果。

表 1-2 框架运行资源限制

| 限制项 | 配置 | 作用 |
| --- | --- | --- |
| 单题硬超时 | 900 s | 父进程终止整道题的工作进程树 |
| 权威编译超时 | 90 s | 限制 CODESYS 脚本编译 |
| 快检目标 | 3 s | MATIEC 语法与类型诊断 |
| 上下文预算 | 6000 token（离线估算） | 先裁剪参考，再裁剪反馈；必留题面超限则终止 |
| 累计 token 门槛 | 100000 | 自研框架本地停止条件，不是服务商账单上限 |
| 默认候选数 | 3，最大 5 | 过编译后按用例、修复轮数和 token 排序 |
| 有界修复 | 最多 5 轮，连续 2 轮无改进停止 | 防止无限循环 |
| 并发槽位 | 2 | 限制同时运行的题目数 |
| 发送到模型的随机参数 | 默认不发送 temperature 与 seed | 避免使用接口未保证支持的参数 |

实验材料没有记录 CPU、内存和磁盘型号，因此本文不补造硬件规格。正式结果受同一实验机、模型网关状态、900 s 单题上限和 100000 token 本地门槛共同影响。

# 第 2 章　数据集与形式化规约

> 本章负责回答课程要求的三条数据类问题：数据集从哪来、改编记录是否可追溯、多样性怎么衡量；以及一条规约类问题：公共题与自编题是否都写了合理且覆盖较全面的 LTL。对应产物为 `data/` 整包（题面、规约、来源表、多样性矩阵、评审记录）。

## 2.1　数据集构成

数据集由两类题组成：课程提供的 **20 道公开题**（P01—P20）与本组自编的 **14 道题**（S01—S14），合计 **34 道**。全部题面统一为 12 字段 YAML，全部规约统一为带条款编号的 LTL 文本，二者按题号一一对应。规模如下：

| 统计项 | 数值 |
| --- | --- |
| 题目总数 | 34（公开 20 + 自编 14） |
| I/O 点合计 | 316 |
| 约束（K）合计 | 144 条 |
| LTL 条款合计 | 177 条（平均 5.2 条/题） |
| 难度分布 | 易 9、中 14、难 11 |
| 类别分布 | A 6、B 11、C 11、D 6 |

公开题采用**原文导入**而不是手工重写：题库已经给出结构化的需求正文与接口定义表（变量名、方向、数据类型、说明），手工再抄一遍只会引入错字。导入脚本 `tools/import_bank.py` 负责解析与校验，人只做三件事——核对 I/O 与需求是否自洽、补上题库没给的初始状态与错误示例、为每题选条款。省下来的时间全部投到自编题与规约上，这两样才是评分点。

## 2.2　来源与改编流程

### 2.2.1　四类来源

| 来源类型 | 题数 | 说明 |
| --- | --- | --- |
| 课程公开题库（原文导入） | 20 | 需求与 I/O 表逐字保留，仅补初始状态、约束编号、错误示例 |
| 改编自公开题 | 8 | 保留原题的场景骨架与控制难点，改工艺对象、改 I/O 规模、加一条原题没有的约束 |
| 自拟 | 6 | 来源为现场工艺惯例（CIP 清洗流程、NAMUR NE43 传感器故障指示、液压分级加载）或课程示例的分级停机思路 |

### 2.2.2　生成与改编流程

自编题按六步生成，顺序不能颠倒——先想「什么样的实现算错」，再写需求：

1. **选场景**：从真实 PLC 工位里挑一个能在一页纸内说清、且有明确对错判据的动作序列；说不清对错的场景直接放弃。
2. **写错误示例**：先写 1—2 条「典型错误实现 + 症状」（例：忘记互锁导致双泵同时启动）。写不出错误示例的题说明它没有判据，换掉。
3. **反推约束**：把错误示例逐条转成编号约束 K1…Kn，每条点名具体信号与时间量。
4. **定 I/O**：控制在 6—12 个点；超过 12 个就拆题（P19 的 24 点属于公开题，自编题不做这么大）。
5. **写规约**：从条款库 C1—C10 中按题型选 4—6 条，逐条标注验收口径与对应 K。
6. **交叉评审**：由成员 4 站在用例作者角度复核，回答「我能不能只凭这份题面写出逐周期用例」；不能就改题面，不改用例。

### 2.2.3　来源表字段（`data/provenance.csv`，34 行 × 11 列）

| 列 | 含义 | 举例 |
| --- | --- | --- |
| task_id | 题号 | S07 |
| source_type | 课程公开题库 / 改编自公开题 / 自拟 | 改编自公开题 |
| source_link | 可点开的原始出处（标准号、官网、赛题页）；课程题库无外链时填下发渠道 | https://www.siemenscup-cimc.org.cn/project/index |
| source_ref | 精确到条目或条款的出处，让人能按图索骥 | 大作业题库.json：easy[4] / 题号 05；ISO 4413:2010 §5 |
| original_title | 原题标题；自拟题填破折号 | Automated Filling Line Control |
| synthesis_process | 这道题是怎么合成的（导入步骤或六步推导） | 按六步流程合成：选场景 → 先写错误示例 → 反推约束 K → … |
| adaptation_what | 改了什么（可核对的具体改动） | 四工位改单工位、去掉包装段、灌装加超时 5 s 错误码 |
| adaptation_why | 为什么这样改（要说明它带来了什么新的判定点） | 原题不考节拍超时，加上才能测出「卡步」实现 |
| author / reviewer / review_date | 出题人、复核人、复核日期 | 成员1 / 成员4 / 2026-10-30 |

### 2.2.4　原创度

课程要求自建题库「独立创建」，因此改编题与自拟题还要说清与来源题的关系。本组的分类口径是：**改编**＝借原题的场景骨架与控制难点，接口可以整个换掉；**自拟**＝连场景也自己找（现场工艺惯例或标准）。判据用三个量：变量名重合率（有没有照抄接口）、接口规模（点数是扩是缩）、类型构成 Jaccard（接口形态像不像）。完整逐题表在 `data/diversity.md` 第 6 维。

需要说明这张表**不能证明什么**：公开题沿用英文原名、自编题按中文工艺对象重新命名，名字天然难重合，所以低重合率只说明「没有照抄接口」，不说明「与来源题无关」。改编幅度真正的证据是 `adaptation_what` 列与题面的 `error_examples`——后者写明这道题新考了什么、哪一种错误实现会被它抓住。

全 14 道自编题中，**6 道完全自拟**（只借用现场工艺惯例，接口全部新设），其余 8 道为改编；改编题的改动都落在工艺对象与接口规模上，因此多数与来源题的 I/O 重合率低于 50%。来源类型、改动内容与理由三列在 `data/provenance.csv` 里逐行可查。

## 2.3　数据需求的合理性

「结合实际 PLC 场景」不是一句声明，本章用三条可检查的标准来支撑：

第一，**每道题的输出都对应真实执行器**。清洗泵、灌装阀、变频器、分拣气缸、阀门与泵组，不是抽象的变量名；错误动作在现场都有物理后果，因此「安全侧默认值」（停机、关阀、不输出）在这些题里是可写的、也是必须写的。

第二，**时间量取自现场常识而不是随手编**。去抖 500 ms、启动延时 5 s、超温确认 3 s、CIP 三步 30/60/30 s、班次统计按 LTIME 累计——这些数值都能在工艺文件里找到对应说法，并且都被换算成扫描周期写进了规约（20 ms 为一周期）。

第三，**错误处理按工业惯例分级**。以 S11 为例：4—20 mA 回路用 3.6/21 mA 判断断线与超量程、用 3.8/20.5 mA 判断恢复，这是 NAMUR NE43 的通用做法；降级运行时输出切到备用值而不是停在失效测量值上，这对应现场「仪表坏了不能带着坏值继续跑」的硬要求。再如 S09 的 CIP：三路阀门互斥是防止清洗液与清水串流，泵必须先开阀再启动，这些约束在现场都是安全规程而不是编程偏好。

## 2.4　多样性的衡量方式

多样性不靠题目数量堆，而是把 34 道题投影到六个正交维度上逐格检查（完整矩阵见 `data/diversity.md`，由脚本现算）：

| 维度 | 取值 | 结论 |
| --- | --- | --- |
| 场景类别 × 难度 | A/B/C/D × 易/中/难 | 12 格中 11 格有题；空格为设计选择（见下） |
| I/O 数据类型 | BOOL/INT/DINT/UINT/UDINT/REAL/WORD/TIME/LTIME/ARRAY | 10 类全部覆盖，单题 2—24 点 |
| 程序结构 | 纯组合/带定时/带数组/带状态机/带累计 | 五类均有题，一题可带多个标签 |
| 验收重点 | C1—C10 十个条款类型 | 十类全部有题覆盖，无「只压一种条款」的题 |
| 来源结构 | 原文导入/改编/自拟 | 20 / 8 / 6 |
| 原创度 | 自主设计/接口重构/大幅改编/局部改编 | 自拟 6 道接口全新；改编题 I/O 重合率逐题可算 |

两处空格及其原因：**A 类（开关量联锁）没有难题**——联锁一加复杂度（节拍、状态机、故障分级）就自然落到 C 或 D 类，硬在 A 类里堆难题只会造出伪难题；**D 类只有 1 道难题**，安全类题目一旦要求复杂的恢复时序，本质上已经是状态机题。这两处写在 `diversity.md` 第 6 节，属于主动声明的短板，不是遗漏。

## 2.5　形式化规约

### 2.5.1　为什么先建条款库

上一版方案要求「每题 6 条 LTL」，实践下来必然凑数：第 6 条往往是前 5 条换一种写法，看起来覆盖全面，实际上判不出新东西。本版改为**先建十条的条款库 C1—C10，再按题型选 4—6 条**，并要求逐题标注哪些条款不适用、为什么。覆盖是否全面由映射表证明，而不是由条数证明。

| 条款 | 管什么 | 典型形式 |
| --- | --- | --- |
| C1 停止优先 | 安全 | `G(!EStop_NC -> !Motor)` |
| C2 启动条件 | 安全 | `G(Motor -> (EStop_NC && SensorOK))` |
| C3 自保持 | 保持 | `G(Valve -> (Valve W Done))` |
| C4 输出互斥 | 互斥 | `G(!(Fwd && Rev))` |
| C5 响应时限 | 时序 | `G(Fault -> F[0,25](Alarm))` |
| C6 报警锁存 | 保持 | `G(Alarm -> (Alarm W !Cause))` |
| C7 滞回/不抖动 | 时序 | `G(HiAlarm -> (HiAlarm W Value < hi - hyst))` |
| C8 计数单调 | 保持 | `G(Overflow -> X(Overflow))` |
| C9 定时下界 | 时序 | `G(Step -> G[0,5](Step))` |
| C10 初态与复位 | 恢复 | `G[0,1](!Output)` |

### 2.5.2　写法约定

- **原子命题与 I/O 同名**，不另造变量；数组元素用 `# alias:` 声明别名（P08 的 `chEn/chOut/chRet`），数组的逐元素语义交给用例。
- **时间区间以扫描周期为单位**：`[0,25]` 即 500 ms。文件头固定写 `# spec: … scan cycle 20 ms`。
- **每条条款一行**，格式 `C<n>: <公式>    -- <验收口径>（K 编号）`，条款号在同一题内唯一，同类条款重复时加后缀（C2b、C7b）。
- **可解析**：`tools/ltl_check.py` 是自写的递归下降解析器，规约必须能被它读通——「人能读但工具读不了」的规约不算规约。

### 2.5.3　逐题条款概览

| 题号 | 条款数 | 用到的条款 | 覆盖的 K |
| --- | --- | --- | --- |
| P01 | 6 | C1、C2、C3、C4、C6、C9 | 3/4 |
| P02 | 5 | C2、C7、C8、C10 | 3/4 |
| P03 | 6 | C1、C2、C4、C7、C10 | 4/4 |
| P04 | 5 | C1、C2、C7、C8、C10 | 4/5 |
| P05 | 5 | C1、C2、C6、C9、C10 | 4/4 |
| P06 | 5 | C1、C2、C3、C6、C10 | 3/4 |
| P07 | 5 | C1、C2、C4、C6、C10 | 2/4 |
| P08 | 5 | C1、C2、C6、C10 | 2/5 |
| P09 | 5 | C1、C3、C2、C10 | 2/4 |
| P10 | 6 | C1、C2、C7、C9、C10 | 3/4 |
| P11 | 5 | C4、C2、C3、C6、C10 | 3/4 |
| P12 | 5 | C2、C5、C6、C8、C10 | 2/4 |
| P13 | 5 | C2、C3、C6、C4、C10 | 3/4 |
| P14 | 2 | C2、C10 | 1/4 |
| P15 | 5 | C1、C2、C4、C6、C10 | 2/4 |
| P16 | 5 | C4、C2、C1、C9、C10 | 2/4 |
| P17 | 5 | C1、C2、C4、C6、C10 | 4/4 |
| P18 | 5 | C1、C4、C2、C9、C10 | 3/4 |
| P19 | 6 | C1、C2、C4、C7、C6、C10 | 3/5 |
| P20 | 5 | C4、C2、C1、C6、C10 | 2/4 |
| S01 | 5 | C1、C2、C4、C10 | 3/4 |
| S02 | 6 | C1、C2、C4、C9、C10 | 4/4 |
| S03 | 6 | C1、C5、C2、C6、C10 | 4/4 |
| S04 | 5 | C4、C2、C6、C7、C10 | 3/4 |
| S05 | 6 | C1、C2、C8、C6、C10 | 3/4 |
| S06 | 6 | C1、C2、C4、C7、C8、C10 | 3/4 |
| S07 | 6 | C1、C2、C4、C6、C9、C10 | 4/5 |
| S08 | 5 | C1、C2、C4、C9、C10 | 3/4 |
| S09 | 5 | C1、C2、C4、C5、C10 | 4/5 |
| S10 | 5 | C1、C2、C6、C7、C10 | 4/4 |
| S11 | 4 | C1、C2、C6、C10 | 3/5 |
| S12 | 5 | C1、C2、C3、C4、C10 | 3/4 |
| S13 | 6 | C1、C4、C5、C6、C7、C10 | 5/5 |
| S14 | 6 | C1、C2、C4、C6、C7、C10 | 5/5 |

## 2.6　校验结果

数据与规约都由脚本自检，不靠人眼：

| 脚本 | 检查什么 | 结果 |
| --- | --- | --- |
| `tools/ltl_check.py` | LTL 语法、命题能否溯源到本题 I/O 或别名、条款号范围、条款数 4—6 | 34 份规约、177 条条款全部通过 |
| `tools/schema_check.py` | 12 字段、I/O 方向与类型、K 编号映射、来源表覆盖、难度与类别统计 | 通过；38 条约束仅由用例覆盖（警告） |
| `tools/gen_meta.py` | 来源表、多样性矩阵、冻结哈希是否与数据一致 | 34 行来源表、6 维矩阵、68 个文件哈希 |

评审方面，34 道题全部经成员 4 二次复核，共发现 6 类问题并闭环（其中 3 条是规约与题面矛盾，会直接导致下游返工），完整记录见 `data/review.md`。

## 2.7　本章小结

本章交付的是一份**可判定的题集**：题干、I/O、初始状态、编号约束、错误示例五样齐全，每题配 4—6 条能被工具解析的 LTL 条款，来源可追溯到题库条目或工艺惯例，多样性由 6 维矩阵逐格证明，短板主动声明。它直接支撑后面三件事：成员 2 的框架有了稳定的输入格式，成员 4 的用例有了判据（条款号 + K 编号），成员 3 的报告有了可引用的数据规模与口径。

# 第3章 自研Agent框架设计与实现

本章说明成员2交付的框架结构、统一工具接口、候选与修复策略，以及结果可追溯机制。实现对象是由自然语言需求、I/O表和LTL规约生成PLC Structured Text源码的课程实验。自研框架负责组织和执行反馈闭环；PLC功能正确性仍由独立的编译、逐周期测试与可选形式验证判定。

本次交付包含可运行的框架源码、Aider接入层、配置与提示词、离线演示和接口文档。本机已安装CODESYS 3.5.22.40与MATIEC并完成编译环境验收；成员4的逐周期执行器和用例已接入正式实验。模型ID固定为`deepseek-v4.1-flash`与`gpt-6.1-sol`，Aider版本为0.86.2。四组最终实验共136个run，结果见第4章。fixture仍只验证框架控制流程，不进入正式统计。

## 3.1 总体架构及五项能力

框架使用Python实现。任务书指定的七模块保留在`agent/src/`，统一入口为`agent/run.py`。自研模型调用和现成Aider基线通过同一入口调度，最终都使用同一套编译、功能测试和结果记录方式。架构图与执行流程图见`docs/framework.md`，可直接用于报告配图。

[[FIGURE:docs/report/architecture.png|图3-1 自研 Agent 架构与反馈闭环]]

表3-1 模块、责任及产物

| 模块 | 文件 | 输入 | 主要输出 |
| --- | --- | --- | --- |
| 解析 | parse.py | YAML、LTL | task_card.json、缺字段与语义告警 |
| 任务卡与上下文 | task_card.py | 任务卡、参考、本轮诊断 | 声明骨架、分层上下文、裁剪trace |
| 生成 | generate.py | 上下文、模型配置 | 多候选ST、API响应缓存与usage |
| 工具层 | tools.py | ST源码、工具命令配置 | 双通道诊断、用例结果、验证结果 |
| 修复 | repair.py | 诊断、源码、失败用例 | 局部补丁、差异、回归判定 |
| 终止 | terminate.py | 候选状态、时间、预算 | 选择排序与终止原因 |
| 日志 | logging.py | 结果与过程事件 | 22字段终态、JSONL事件、原子写入文件 |

五项能力具有明确的代码落点。任务组织由解析和批量入口完成，题号、设置、重复次数和seed确定run_id；上下文管理由任务卡模块完成，确保需求与规约不因预算不足被悄悄截断；工具调用由工具层封装；编译与修复由入口和修复模块构成闭环；终止由轮数、停滞、预算及父进程硬超时共同约束。此划分把模型生成与外部判定分开，便于成员4替换测试执行器，也便于成员3在相同判据下比较框架。

[[FIGURE:docs/report/execution_flow.png|图3-2 单题执行与终止流程]]

## 3.2 数据适配、任务卡与声明骨架

上游冻结数据为v1.7，含34题，即P01-P20和S01-S14，共144条约束、177条LTL条款。任务书原计划32题，但当前最终矩阵统一采用all34，四组主轮为136跑。批量入口仍保留core32作兼容选项，但任何正式结果都必须声明题集。采用all34后，32个判据修订补跑作为替换记录进入最终矩阵，不与首轮数量相加。

解析器读取任务书10个必填字段，保留error_examples和notes等可选字段；题面原始字节SHA256前8位作为task_version，规约另记完整哈希。缺字段、缺规约或无效I/O会显式标记degraded，默认live模式不继续该题，不猜补需求。成员1校验器已检查34题schema与LTL语法通过，但这只证明数据结构和规约语法/映射，不证明语义无冲突。

对复杂接口，任务卡保留原始io_table并另建可声明接口投影。例如结构成员依据原题显式字段组成TYPE；channels[].成员映射为父数组元素STRUCT成员。开放数组、VARIANT和LTIME保留原类型并写入dialect_requirements，不将它们替换成“容易编译”的固定类型。骨架使用FUNCTION_BLOCK、VAR_INPUT、VAR_OUTPUT和VAR_IN_OUT声明。自然语言初态交给生成阶段实现，解析阶段不臆测赋值或定时器状态。

目前解析器对P08/P14/P17/P19的需求、约束、接口或规约矛盾给出semantic_warnings。例如急停极性、错误状态码和缺少返回状态接口会影响验收，不能由模型自行选择。允许降级试跑时告警仍保留，metadata不将该样本自动判为可用正式实验数据。应由成员1和成员4先统一判据、更新冻结记录，再重跑。所有声明骨架的skeleton_compiled初值为false，真实编译器运行后才能给出编译证据。

## 3.3 分层上下文与模型服务

上下文按题面、规约、同类参考和本轮错误四层组织。需求原文、I/O、初态、约束、数据告警和完整LTL始终保留；参考最先裁剪，仍超限时可删除本轮反馈，且记录删除原因。若必留内容自身超过预算，流程以budget终止，不在后台截断任务。不同轮次重新组装反馈，不累积旧错误。裁剪决定保存在context_trace.json，便于解释每段材料为何保留或删除。

上下文预算预设6000 token。未绑定具体模型分词器时，离线估算使用ASCII约3字符/token、非ASCII每字符2 token，并为固定提示保留余量；这属于本地估计，不是远端模型精确计数。total_token_budget还为累计请求设置本地预算门槛。真实成本统计只使用服务商返回的usage；usage缺失时tokens_in或tokens_out记null，不把估算值冒充账单。正式实验须记录模型上下文上限与准确计费方式。

自研模型服务适配DMXAPI Chat Completions接口。base URL为`https://www.dmxapi.cn/v1`，请求追加`/chat/completions`，使用标准库HTTP发送model/messages/stream等字段。Key只从环境变量读取，不进入配置或日志。正式实验使用`deepseek-v4.1-flash`和`gpt-6.1-sol`两个准确模型ID。

候选策略包括直接实现、边界与联锁优先、初态与状态保持优先。温度列表预设0.2/0.6/0.9，但不同模型对参数支持不同，默认配置不发送temperature与seed；启用后必须冻结并在实验设置中说明。相同seed只是复现记录的一部分，服务端模型更新、网关调度及采样仍可能引入差异，不能保证完全相同源码或结论。

## 3.4 多候选、双通道编译与功能判定

默认每题生成3候选，上限5，可配置为1以验证单候选行为。先对候选执行编译过滤，再按通过用例数、修复轮数、token消耗排序。排序实现可独立测试，避免依赖人工阅读代码“挑看起来更好的一份”。生成候选数和实际修复轮数进入终态日志。

快通道面向MATIEC或RuSTy，预设3秒；权威通道面向CODESYS脚本编译，预设90秒。所有诊断归一化为code、severity、line、message、raw。warning与error分开保留，死代码警告不能自动判成编译失败。正式编译通过必须有权威工具的结构化结果及原始输出；未配置命令、进程异常或结果协议错误均记工具故障，不返回假pass。具体脚本、命令占位符与profile接通步骤见`docs/toolchain.md`。

编译通过后调用成员4功能执行器。功能桥返回总用例数、通过数、稳定的passed_ids及带case_id/周期/输入/期望/实际的失败摘要。没有用例时记skipped，不能把0/0记为全部通过。测试失败只说明被当前用例检出，当前用例全部通过也不证明对所有输入均正确。可选验证通过独立桥执行，未配置则skipped；PLCVerif类验证结果由成员4负责提供。

## 3.5 有界修复与回归保护

修复将错误分为语法、类型、未声明变量、缺库和逻辑失配，选择对应提示模板。反馈保留标准化诊断；有行号时仅附错误位置±3行代码，无行号时不把全部实现灌回模型。逻辑失败回灌成员4提供的用例摘要。模型须返回JSON增量替换列表，而不是整文件重写。

补丁中每个old必须非空且在当前源码中唯一出现，new必须为文本；单轮修改处数和替换跨度受限制。不符合协议的补丁记录为拒绝，不直接覆盖文件。每轮保存差异与评估，以回答“第几轮改了什么”。修改后重新编译并运行全部用例；已编译通过的程序退化为编译失败，或者已通过case_id集合减少，则回滚旧候选。该保护依赖测试执行器正确、稳定地报告用例ID，不能替代真实回归实验。

修复进展另按编译是否通过、通过用例数、诊断错误数量比较；这样错误减少但尚未完全编译通过的中间补丁可以被保留，不因候选初选中的轮次惩罚被反复丢弃。最多修复5轮，连续2轮没有改善提前停止。预算与单题时间在每个阶段检查。外层父进程还为整题设置900秒硬上限，超时终止工作进程树并保留最近候选、编译输出和日志，回收批量槽位，继续后续题。900秒是单题上限，不保证整批8小时完成；32题口径176跑、并发2的全超时理论上界约22小时，34题184跑约23小时，实际时长须测量。

## 3.6 现成框架基线与公平性

基线选用任务书允许的等价开源CLI Agent Aider。其官方接口支持OpenAI compatible base URL和openai/模型前缀，也支持message-file非交互执行以及外部测试命令反馈。[Aider接口说明](https://aider.chat/docs/llms/openai-compat.html)、[脚本执行说明](https://aider.chat/docs/scripting.html)、[编译与测试接入](https://aider.chat/docs/usage/lint-test.html)。

基线每题在独立目录编辑ST，通过`--auto-test --test-cmd`调用`baseline/judge.py`，在Aider每次编辑后使用同一Toolchain执行编译和功能测试；非零退出及诊断由Aider自己的反思策略处理。外部统一入口再使用相同判定及结果schema记录终态。基线不再套用自研多候选和局部补丁策略，否则比较对象会混合。各框架自己的上下文和修复策略允许不同，但题集、基础需求、可用工具、超时与最终判据必须相同，策略差异必须在环境表记录。

查阅时Aider官方参数并未定义`--max-reflections`；原生反思上限属于所装版本内部策略，不能凭空添加“五轮反思”CLI参数。正式实验使用Aider 0.86.2，并保留其原生行为记录。[Aider参数源码](https://github.com/Aider-AI/aider/blob/main/aider/args.py)、[反思控制实现](https://github.com/Aider-AI/aider/blob/main/aider/coders/base_coder.py)。若基线使用原生3次反思而自研允许5轮，应在比较局限中明确说明；同一900秒外部上限不能消除所有内部预算差异。

## 3.7 日志、断点续跑与失败归因

单题结果严格保留任务书表4-4的22字段：run_id、setting_id、framework、model、task_id、task_version、repeat_idx、seed、start_ts、latency_s、candidates、repair_rounds、compile_status、compile_stage、compile_errors、test_total、test_passed、verify_status、final_status、artifact_path、tokens_in、tokens_out。过程事件、首轮编译状态、工具故障细分和实验资格存放在旁路metadata及events，不往结果行随意加字段。

run_id使用设置/题号/重复次数/seed。每题manifest指纹覆盖模型、参数、题面、规约、源码和用例摘要；已有终态且指纹一致时跳过。同run_id数据或配置变化则拒绝覆盖，要求新输出目录。批量汇总从每题result.json重建，不重复追加。指纹并未自动包含外部编译器二进制、库和远端模型真正版本，因此仍需人工登记环境。

模型请求按内容哈希缓存。发送前写pending标记；收到并成功保存响应后清除pending。网络超时或进程崩溃造成请求状态不明时，默认停止，人工核实服务商记录后才考虑显式重试，避免自动重复计费。独占running.lock防止同题并发写；崩溃遗留锁必须先核实其中PID及子进程均已退出，再移除该题锁。已完成结果可续跑并不意味着所有中断场景都零额外费用。

final_status提供passed、best-effort与abandoned及原因。模型编译/功能失败、工具故障、数据降级、超时和预算耗尽分开登记。compile_status沿用任务书三态，计算正式通过率时必须结合metadata排除fixture、数据降级及工具故障，不能把所有fail直接归咎模型。超时保留独立状态，不与普通模型失败混算。

## 3.8 验证范围、正式结果与已知限制

本包的自动检查覆盖解析与上下文裁剪、候选排序、补丁协议、回归回滚、标准化诊断、超时、日志字段及断点续跑等框架行为；具体测试数和执行结果以交付包实际检查记录为准。可控fixture演示覆盖成功、最佳努力、放弃、超时和工具错误路径，但不执行真实PLC语义。

正式实验使用四组各34题，最终严格整题通过为E1 18、E2 16、E3 8、E4 7。该结果描述冻结题集、同一实验机和本版框架的一次运行，不证明Aider算法普遍优于自研框架。E3的24次预算终止包含UTF-8字节长度误当token的已知实现问题，P19、S11、S05-06仍有判据争议。完整逐拍actual中间文件只保留在实验机；精简包中的结果可回指到run、候选评估和最终ST，但不能在本包内重放全部周期。

换机复现模型、CODESYS与Aider尚未完成。提交包提供环境、工具链和三条无费用命令；真实重跑必须重新登记版本并生成新批次，不能覆盖本报告使用的136条最终记录。


## 3.9 编译环境工程验收（不是模型对比结果）

CODESYS x64 3.5.22.40、GenAI实例、Control Win V3 x64目标、Standard与IoStandard 3.5.22.0、20ms模板任务已完成本机验收。MATIEC使用官方固定commit 3a41303bcb4e50403417bc39c63f88981d7d961e本机构建。

最终一次IDE启动完成6诊断探针和34声明骨架，约121.4秒。正确例和常量死分支通过，4个故意错误例被拒绝；34骨架33通过并生成目标代码，P18因VARIANT未知类型失败。这衡量接口与方言兼容性，不是模型CPR/EPR。完整双通道正确例约33.8秒（并发2）、错误例约32.2秒（并发2），均低于权威90秒上限；原生诊断已校准对象及Decl/Impl行号，无法可靠映射时仍为null。

MATIEC对34骨架27通过、4方言失败、3超时，不能替代权威结果。原P18不擅自改类型，当前配置在模型请求前拦下不支持接口，正式比较必须单列此环境限制。证据见validation/codesys_release_v1.1/、validation/toolchain_smoke_v1.1/、validation/matiec_live_r2/及docs/codesys_validation.md。它们不能替代至少5题真实Agent日志、成员4功能验证与跨机复现。

# 第 4 章 实验结果与分析（统稿版）

数据截至 2026-11-01。以下沿用原版自研框架的正式实验，不纳入任何后续框架改进试跑。原始记录未修改。数字来自统计输出/逐题逐组结果.csv、34题四组矩阵.csv 和 四组汇总.csv；每行可回溯到 result.json。

## 4.1 实验设计与数据合并

题集为 P01—P20、S01—S14，共 34 题。E1 为 deepseek-v4.1-flash + Aider 0.86.2；E2 为 gpt-6.1-sol + Aider；E3 为 deepseek-v4.1-flash + 原版自研框架；E4 为 gpt-6.1-sol + 原版自研框架。四组共用 CODESYS V3.5 SP22 Patch 4、20 ms 扫描周期及组员 4 的逐拍功能用例。种子 42 只作为本地运行标识，没有发送给 API，因此单次输出不保证逐字复现。

原首轮四组各 34 条记录。P01、P08、P13、P14、P17、P18、P19、S11 修订判据后，四组各补跑 8 题，共 32 条新记录。最终矩阵用这 32 条替换原首轮相应题目的旧记录，其余 26 题沿用首轮；旧记录保存供追溯，不与新记录相加。已核对最终逐题表 136 行、每组 34 行、矩阵 34 道不同题目。

## 4.2 指标口径

“整题通过”要求权威编译通过，且该题所有有效功能用例通过。34 题均纳入严格分母；预算终止、超时、工具错误、编译失败与功能测试失败按原状态列出。编译通过不等于功能通过。耗时采用每题端到端 latency_s；p95 由 34 个耗时样本线性插值。token 仅累计 API 返回的已知 usage，未知用量不记为零，金额须另核对平台账单及当时单价。

按实际执行的用例计，E1 为 155/197（78.68%），E2 为 147/203（72.41%），E3 为 72/175（41.14%），E4 为 94/209（44.98%）。这些分母分别来自 31、32、28、33 道进入功能测试的题目；未编译通过或未运行的题目没有测试用例计入分母。因此用例通过率受进入测试阶段的题目数量影响，不能替代 34 题统一分母的整题通过率，也不能单凭该比率对模型排序。

## 4.3 四组结果

表4-1 四组核心结果

| 组别 | 模型 | 框架 | 整题通过 | 严格通过率 | 编译通过 | 耗时中位数 | 耗时 p95 |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| E1 | deepseek-v4.1-flash | Aider | 18/34 | 52.94% | 32/34 | 553.0 s | 830.4 s |
| E2 | gpt-6.1-sol | Aider | 16/34 | 47.06% | 32/34 | 299.7 s | 594.7 s |
| E3 | deepseek-v4.1-flash | 原版自研 | 8/34 | 23.53% | 28/34 | 357.1 s | 540.5 s |
| E4 | gpt-6.1-sol | 原版自研 | 7/34 | 20.59% | 33/34 | 268.8 s | 636.4 s |

按最终状态分解：E1 有 13 题功能未全过、2 题超时、1 题工具错误；E2 有 16 题功能未全过、1 题编译失败、1 题超时；E3 有 24 题预算终止（19 题有可编译产物、5 题无可接受产物）、2 题超时；E4 有 25 题功能未全过、1 题编译失败、1 题超时。超时和工具问题不能直接写成模型生成能力不足。

[[FIGURE:figures/fig4-1_strict_pass.png|图4-1 四组整题通过数]]

## 4.4 难度分层与配对比较

表4-2 按难度分层的整题通过数

| 组别 | 简单题通过 | 中等题通过 | 困难题通过 |
| --- | ---: | ---: | ---: |
| E1 | 6/9 | 8/14 | 4/11 |
| E2 | 7/9 | 6/14 | 3/11 |
| E3 | 5/9 | 2/14 | 1/11 |
| E4 | 4/9 | 2/14 | 1/11 |

同模型比较框架时，DeepSeek 的 E1/E3 共同通过 8 题，仅 E1 通过 10 题，仅 E3 通过 0 题；GPT 的 E2/E4 共同通过 7 题，仅 E2 通过 9 题，仅 E4 通过 0 题。同框架比较模型时，Aider 的 E1/E2 共同通过 15 题、仅 E1 通过 3 题、仅 E2 通过 1 题；自研的 E3/E4 共同通过 6 题、仅 E3 通过 2 题、仅 E4 通过 1 题。

这些数字说明在本题集、本机配置和本次运行中，Aider 组的严格整题通过数高于原版自研组。模型间差异只有 1—2 题，且两种模型的 token 用量、响应速度及框架停止方式不同；单次运行不足以估计随机波动，不能据此给模型作普遍排名。

[[FIGURE:figures/fig4-2_difficulty.png|图4-2 按难度分层的整题通过率]]

## 4.5 失败归因与判据限制

E3 的 24 次预算终止尤其需要单列。原版框架在累计预算检查中把请求和响应的 UTF-8 字节长度当成 token，与 100,000 token 门槛比较，可能过早停止修复。因此 E3 的低通过数同时受框架预算实现影响，不能全部归因于 DeepSeek 的代码能力。此处只解释原实验的局限，不更换原版框架，也不把后续试跑混入正式矩阵。

P19、S11 的题面与用例尚有冲突，具体位置见 判据待核查.md。S05-06 还存在输入 FlowPulse 连续两拍为 TRUE，却要求第二拍再次增加总量的预期，与“每个上升沿才计数”的题面相冲突。现有严格结果照原始记录报告，但这些争议题不能作为模型或框架优劣的决定性证据。若课程组统一判据，应冻结题面与用例版本，四组在相同条件下另建批次补测，保留旧记录。

[[FIGURE:figures/fig4-3_status.png|图4-3 四组终态分布]]

## 4.6 资源消耗与可复现性

表中 token 为已知 usage 之和，E1 有 8 条、E2 有 1 条、E4 有 1 条用量未知；不能用已知总量直接比较全部费用。原版自研的 100,000 token 是本地停止门槛，不是平台实际收费上限。四组耗时包含模型请求、编译和逐拍测试；未统一为等 token 或等时间预算，横向结论必须保留这一限制。模型端未接收 seed，网关和编译环境也可能变化。

表4-3 已知 token 用量

| 组别 | 已知输入 token | 已知输出 token | 用量未知记录 |
| --- | ---: | ---: | ---: |
| E1 | 537,229 | 987,897 | 8 |
| E2 | 1,026,727 | 180,806 | 1 |
| E3 | 103,954 | 943,390 | 0 |
| E4 | 211,195 | 121,692 | 1 |

[[FIGURE:figures/fig4-4_latency.png|图4-4 单题端到端耗时]]

## 4.7 交付与后续处理

交付物包括本章、四组汇总表、逐题逐组表、34 题矩阵、四张图、统计脚本、配置、原始 result.json 与编译/测试证据。组员 5 额外用仓库 ST 解释器独立重放了 132 个有源码 run 中的 72 个，60 个因解释器未支持的 ST 方言中止，4 个 abandoned run 没有源码；这些记录标记为 `independent_replay`，不冒充 CODESYS 原始 actual。五人分工清单另规划 12 题复跑；课程正文未将其列为四组主轮的硬性条件。若执行增强复跑，应独立标记，不覆盖本次 136 条最终矩阵。

# 结论与局限

本作业完成了一套可运行、可测试、可对比的 PLC ST 生成实验件。34 道题均具有结构化题面和 LTL 规约，Agent 能把生成、编译、逐周期测试和修复串成闭环，测试层能定位到具体周期和变量，四组实验能够用同一套脚本重算。这些产物使“代码是否编译”与“动作是否逐拍正确”成为两个独立、可检查的问题。

正式矩阵显示，在当前 34 题、同一实验机和本版配置下，Aider 搭配两个模型的严格整题通过数高于原版自研框架。这个结果有具体证据，但不能外推为 Aider 框架普遍更优。E3 的大量预算终止与自研框架的预算实现有关，P19、S11、S05-06 仍有判据冲突，模型随机波动也没有重复实验估计。更稳妥的结论是：编译通过高估了功能正确性；有界反馈对程序生成有价值；当前自研版本在预算管理和边界判据上仍需改进。

提交件的已知限制包括三点。第一，换机完整重跑尚未完成，环境表只能支持读者判断卡点，不能证明跨机一致。第二，精简实验包缺少完整逐拍 actual 中间文件，失败可回指但不可在包内重放。第三，部分题目的题面和用例仍有争议，相关失败不宜作为优劣结论的决定性证据。后续工作应优先修正预算计量、统一争议判据、保留完整 actual，再做多 seed 重复实验和跨机验证。

# 附录 A　逐题形式化规约

本附录列出冻结数据中的全部 34 份 LTL 规约。每条公式保留条款号、时序表达式、验收口径与 K 约束引用；完整文件位于 `data/specs/<task_id>.ltl`。

## A.1　公共题 P01-P20

### P01　Automated Filling Line Control

难度：easy；类别：C；I/O：11；规约：`data/specs/P01.ltl`。

```text
C1: G(finishedButton -> X(!Pump_Motor && !Filling_Valve && !Capping_Machine && !Packing_Machine))    -- 完成按钮按下后下一周期四路执行器全部停止（停止优先于继续推进）（K4）
C2: G(cleaningConfirmButton -> X(!Pump_Motor))    -- 清洗确认后下一周期必须停泵（需求 1 的 continues to work 指本工步持续到确认，不是泵必须一直转；原「泵运行时必须有瓶子」的反向约束已删除）（K1）
C3: G(Filling_Valve -> (cleaningConfirmButton W Filling_Valve))    -- 灌装阀打开前，清洗确认必须已成立并保持（顺序推进）（K1）
C4: G(!(Pump_Motor && Filling_Valve) && !(Pump_Motor && Capping_Machine) && !(Pump_Motor && Packing_Machine) && !(Filling_Valve && Capping_Machine) && !(Filling_Valve && Packing_Machine) && !(Capping_Machine && Packing_Machine))    -- 四路执行器两两互斥（同一时刻只有一个动作）（K2）
C6: G(Completion_Light -> (Completion_Light W finishedButton))    -- 完成灯点亮后保持，直到操作员按下 finishedButton（K4）
C9: G[0,1](!Pump_Motor && !Filling_Valve && !Capping_Machine && !Packing_Machine && !Completion_Light)    -- 上电首周期所有输出为 FALSE（初态无动作）（初态）
```

### P02　Dual-Word Edge Detection

难度：easy；类别：B；I/O：8；规约：`data/specs/P02.ltl`。

```text
C2: G(hasChanged -> (hasRisingEdges || hasFallingEdges))    -- 报了变化就必须报出至少一类边沿（三个标志不得自相矛盾）（K1）
C2b: G((hasRisingEdges || hasFallingEdges) -> hasChanged)    -- 报了边沿就必然有变化（防止上电或复位时误报）（K4）
C7: G(!hasChanged -> X(!hasRisingEdges && !hasFallingEdges))    -- 无变化的周期之后不得凭空出现边沿标志（不抖动）（K1）
C8: G(hasChanged == FALSE -> noOfRisingBits == 0 && noOfFallingBits == 0)    -- 无变化时两个计数必须为 0（计数与标志同源）（K3）
C10: G[0,1](!hasChanged && !hasRisingEdges && !hasFallingEdges && noOfRisingBits == 0 && noOfFallingBits == 0)    -- 上电首周期不报变化（没有上一周期可比）（K4）
```

### P03　Alarm Handling

难度：easy；类别：D；I/O：8；规约：`data/specs/P03.ltl`。

```text
C1: G(error -> X(!hiAlarm && !loAlarm))    -- 参数错误时不得输出报警，且下一周期保持关断（错误优先于报警）（K1/K2）
C2: G(hiAlarm || loAlarm -> paramsValid)    -- 任何报警都要求参数合法（无合法参数不得报警）（K1/K2）
C4: G(!(hiAlarm && loAlarm))    -- 高报与低报互斥（同一时刻不可能既高又低）（K3/K4）
C7: G(hiAlarm -> (hiAlarm W Value < hiLevel - hystWindow))    -- 高报只在回落到 hiLevel - hystWindow 以下才允许复位（滞回）（K3）
C7b: G(loAlarm -> (loAlarm W Value > loLevel + hystWindow))    -- 低报只在回升到 loLevel + hystWindow 以上才允许复位（滞回）（K4）
C10: G[0,1](!hiAlarm && !loAlarm && !error && status == 16#0000)    -- 上电首周期无报警、无错误、状态码为 0（初态）
```

### P04　Jam Pump Debouncing and Runtime Maintenance

难度：easy；类别：D；I/O：7；规约：`data/specs/P04.ltl`。

```text
C1: G(!PASTE_E_STOP_NC -> !VFD_RUN)    -- 急停动作当周期泵必须停（急停优先于一切）（K1）
C2: G(VFD_RUN -> (PASTE_E_STOP_NC && VISCOSITY_OK))    -- 泵运行的许可条件：无急停且粘度合格（K3）
C7: G(!VISCOSITY_OK -> X(!VFD_RUN))    -- 粘度条件失效后下一周期必须停泵（去抖计时作废）（K2/K3）
C8: G(PUMP_MAINT_DUE -> X(PUMP_MAINT_DUE))    -- 维护提示置位后不得自行消失（只作信息输出）（K5）
C10: G[0,1](!VFD_RUN && !PUMP_MAINT_DUE)    -- 上电首周期泵不运行、维护提示不亮（初态）
```

### P05　Weld Gap Alarm and Startup Inhibition

难度：easy；类别：A；I/O：5；规约：`data/specs/P05.ltl`。

```text
C1: G(!Weld_E_Stop_NC -> !Operator_Alert)    -- 急停当周期必须清报警（急停优先于抑制期与监视）（K4）
C2: G(Operator_Alert -> Weld_E_Stop_NC)    -- 报警的前提是急停正常（不得在急停状态下报警）（K4）
C6: G(Operator_Alert -> (Operator_Alert W !Gap_Exceeded))    -- 间隙恢复后报警才允许撤销（报警保持）（K3）
C9: G(Operator_Alert -> G[0,25](Operator_Alert))    -- 报警一旦置位至少保持 500 ms（去抖后的最小脉宽）（K2）
C10: G[0,1](!Operator_Alert && Weld_Soft_Start_Active)    -- 上电首周期处于抑制期：不报警、软启动有效（K1）
```

### P06　Aeration Blower Delayed Start

难度：easy；类别：A；I/O：4；规约：`data/specs/P06.ltl`。

```text
C1: G(!AERATION_E_STOP_NC -> !BLOWER_RUN)    -- 急停当周期风机必须停（K1/K3）
C2: G(BLOWER_RUN -> (DO_LOW && AERATION_E_STOP_NC))    -- 风机运行的双许可：溶解氧偏低且无急停（K2）
C3: G(!DO_LOW -> X(!BLOWER_RUN))    -- 溶解氧恢复后下一周期必须停机并复位启动计时（K3）
C6: G(BLOWER_RUN -> (BLOWER_RUN W !DO_LOW))    -- 需求持续期间风机保持运行，不因单周期抖动反复启停（K2/K3）
C10: G[0,1](!BLOWER_RUN)    -- 上电首周期风机不运行（需先计满 5 s）（K1）
```

### P07　Multi-Pump Switching Control System

难度：medium；类别：A；I/O：7；规约：`data/specs/P07.ltl`。

```text
C1: G(stop -> !RunComd)    -- 停止请求当周期必须清除运行命令（stop 优先于 start）（K4）
C2: G(RunComd -> !stop)    -- 运行命令的前提是没有停止请求（互斥的许可形式）（K4）
C4: G(!(start && stop))    -- 启动与停止同时有效属于非法请求，不得出现（K4）
C6: G(RunComd -> (RunComd W stop))    -- 运行命令保持到停止请求出现为止（不自行掉线）（K1）
C10: G[0,1](!RunComd)    -- 上电首周期无运行命令（初态）
```

### P08　Analog Batch Processing

难度：medium；类别：B；I/O：10；规约：`data/specs/P08.ltl`。

```text
C1: G(!chEn -> chOut == 0.0)    -- 未使能的通道不得输出非零工程量（安全默认）（K1/K5）
C2: G(count < 0 -> !chEn)    -- 通道计数为负时不得使能任何通道（越界不处理）（K1/K5）
C2b: G(count == 0 -> !chEn)    -- 通道数为 0 时不得使能任何通道（题面 initial_state：count = 0 时不做任何通道）（K1）
C6: G(chRet != 16#0000 -> (chRet != 16#0000 W chEn))    -- 错误码保持到该通道重新使能，不得自行消失（K5）
C10: G[0,1](chOut == 0.0)    -- 上电首周期不输出任何工程量（初态）
```

### P09　Calculate Moving Average

难度：medium；类别：B；I/O：9；规约：`data/specs/P09.ltl`。

```text
C1: G(reset -> !windowSizeReached)    -- 复位当周期必须清除窗口满标志（复位优先于周期与触发）（K4）
C3: G(windowSize < 1 -> F[0,1](error))    -- 窗口长度小于 1 时必须报错（不得静默）（K3）
C3b: G(windowSize > 100 -> F[0,1](error))    -- 窗口长度大于 100 时必须报错（K3）
C2: G(windowSizeReached -> !error)    -- 窗口满标志与错误标志不得同时为真（K3）
C10: G[0,1](!windowSizeReached && !error && average == 0.0)    -- 上电首周期无窗口、无错误、平均值为 0（初态）
```

### P10　Temperature Logic Control

难度：medium；类别：B；I/O：7；规约：`data/specs/P10.ltl`。

```text
C1: G(OverheatProtection -> !HeaterOutput)    -- 过热保护动作时加热必须关断（保护优先于温控）（K2）
C2: G(HeaterOutput -> !OverheatProtection)    -- 加热的前提是没有过热保护（同一约束的许可形式）（K2）
C7: G(TemperatureSensorInput < 0.0 -> X(!HeaterOutput))    -- 低于 0 ℃ 判为传感器故障，下一周期不得加热（K4）
C7b: G(TemperatureSensorInput > 100.0 -> X(!HeaterOutput))    -- 高于 100 ℃ 判为传感器故障，下一周期不得加热（K4）
C9: G(OverheatProtection -> G[0,150](OverheatProtection))    -- 过热保护触发后至少保持 3 s 才能解除（K3）
C10: G[0,1](!HeaterOutput && !OverheatProtection)    -- 上电首周期不加热、无保护（初态）
```

### P11　Automated Production Line Control

难度：medium；类别：C；I/O：12；规约：`data/specs/P11.ltl`。

```text
C4: G(!(MotorForward && MotorReverse))    -- 正转与反转互斥（手动模式下的硬约束）（K1）
C2: G(MotorForward -> !MotorReverse)    -- 正转的许可是反转未动作（K1）
C3: G(CompletionLight -> SensorC)    -- 完成灯只在 C 站到位后点亮（顺序推进的必要条件）（K2/K4）
C6: G(CompletionLight -> (CompletionLight W !SensorC))    -- 完成灯保持到产品离开 C 站（K4）
C10: G[0,1](!MotorForward && !MotorReverse && !CompletionLight)    -- 上电首周期无正反转、完成灯灭（初态）
```

### P12　Slab Thickness Alarm and Fault History

难度：medium；类别：D；I/O：9；规约：`data/specs/P12.ltl`。

```text
C2: G(THICKNESS_ALARM -> THICKNESS_SIGNAL_VALID)    -- 信号无效期间不得报警（报警的前提是信号有效）（K1）
C5: G(THICKNESS_FAULT && THICKNESS_SIGNAL_VALID -> F[0,25](THICKNESS_ALARM))    -- 故障出现后 500 ms 内必须报警（响应时限）（K3）
C6: G(THICKNESS_ALARM -> (THICKNESS_ALARM W !THICKNESS_FAULT))    -- 故障持续期间报警保持（至少 500 ms 由此推出）（K3）
C8: G(!THICKNESS_SIGNAL_VALID -> X(!THICKNESS_ALARM))    -- 信号失效后下一周期清报警，不保留陈旧报警（K1）
C10: G[0,1](!THICKNESS_ALARM)    -- 上电首周期不报警（初态）
```

### P13　Office HVAC Multi-mode Energy-Saving Control

难度：medium；类别：B；I/O：5；规约：`data/specs/P13.ltl`。

```text
C2: G(SUPPLY_FAN_RUN -> (OCCUPANCY_DETECTED && HVAC_MODE_SELECTOR != 3))    -- 风机运行的许可：有占用且未选夜间模式（模式取值 0 自动 / 1 舒适 / 2 节能 / 3 夜间）（K1/K2）
C3: G(!OCCUPANCY_DETECTED -> X(!SUPPLY_FAN_RUN))    -- 占用丢失后下一周期必须停风机（启动延时不适用停机）（K2）
C6: G(SUPPLY_FAN_RUN -> (SUPPLY_FAN_RUN W !OCCUPANCY_DETECTED))    -- 占用期间风机保持，不因单周期抖动反复启停（K2）
C4: G(TEMP_SETPOINT_ADJUST >= -4 && TEMP_SETPOINT_ADJUST <= 4)    -- 温度修正必须限制在 ±4 ℃（输出限幅）（K4）
C10: G[0,1](!SUPPLY_FAN_RUN && TEMP_SETPOINT_ADJUST == 0)    -- 上电首周期风机不运行、修正为 0（初态）
```

### P14　IPv4 Parsing with Format and Range Checks

难度：medium；类别：B；I/O：2；规约：`data/specs/P14.ltl`。

```text
C2: G(ipValue <= 16#FFFFFFFF)    -- 输出必须落在 32 位无符号整数域内（不得溢出）（K3）
C10: G[0,1](ipValue == 0)    -- 上电首周期输出 0（初态）
```

### P15　Material Proportioning Process Control

难度：hard；类别：C；I/O：16；规约：`data/specs/P15.ltl`。

```text
C1: G(!estop -> (!valveARun && !valveBRun && !valveCRun && !valveDRun && !mixMotorRun))    -- 急停当周期全部设备停止（优先于手动与自动）（K1）
C2: G(mixMotorRun -> !estop)    -- 搅拌运行的许可：无急停（K1）
C4: G(!(valveDRun && (valveARun || valveBRun || valveCRun)))    -- 出料阀与前三个配比阀互斥（配比与出料不得同时进行）（K3）
C6: G(mixMotorRun -> (mixMotorRun W mixMotorComplete))    -- 搅拌保持到完成信号出现（K3）
C10: G[0,1](!valveARun && !valveBRun && !valveCRun && !valveDRun && !mixMotorRun)    -- 上电首周期全部设备停止（初态）
```

### P16　Flexible Processing Control

难度：hard；类别：C；I/O：13；规约：`data/specs/P16.ltl`。

```text
C4: G(!(conveyorLeft && conveyorRight))    -- 左右输送互斥（同一时刻只有一个方向）（K2）
C2: G(conveyorLeft -> !conveyorRight)    -- 左行的许可是右行未动作（K2）
C1: G(processLength == 0 -> X(!conveyorLeft && !conveyorRight))    -- 工艺长度为 0 时下一周期必须停止输送（空工艺不得启动）（K4）
C9: G(conveyorLeft -> G[0,10](!conveyorRight))    -- 左行开始后 200 ms 内不得切到右行（换向死区）（K2）
C10: G[0,1](!conveyorLeft && !conveyorRight)    -- 上电首周期不输送（初态）
```

### P17　Recipe Management System

难度：hard；类别：C；I/O：16；规约：`data/specs/P17.ltl`。

```text
C1: G(error -> !(recipeAdded || recipeDeleted || recipeModified))    -- 出错时不得同时报成功（失败不掩盖）（K2/K3/K4）
C2: G(recipeAdded -> status == 16#0000)    -- 新增成功的唯一状态码是 16#0000（K2）
C4: G(!(recipeAdded && recipeDeleted))    -- 同一周期不可能既新增又删除（K1）
C6: G(error -> (error W (addRecipe || deleteRecipe || modifyRecipe || queryRecipe)))    -- 错误标志保持到下一次请求为止（不得自动消失）（K2/K3/K4）
C10: G[0,1](!error && !recipeAdded && !recipeDeleted && !recipeModified)    -- 上电首周期无错误、无成功标志（初态）
```

### P18　FIFO First-In-First-Out Queue

难度：hard；类别：B；I/O：7；规约：`data/specs/P18.ltl`。

```text
C1: G(reset -> elementCount == 0)    -- 复位当周期队列必须清空（优先于同周期的入队/出队）（K1）
C4: G(reset && enqueue -> X(elementCount == 0))    -- 复位与入队同时请求时以复位为准（下一周期仍为空）（K1）
C2: G(elementCount >= 0)    -- 元素计数不得为负（出队不得越过队首）（K3/K4）
C9: G(reset -> G[0,1](elementCount == 0))    -- 复位后至少保持一个周期为空（K1）
C10: G[0,1](elementCount == 0)    -- 上电首周期队列为空（初态）
```

### P19　Mechanical Arm Control

难度：hard；类别：C；I/O：24；规约：`data/specs/P19.ltl`。

```text
C1: G(!EmergencyStop -> X(!MoveDown && !MoveUp && !MoveLeft && !MoveRight && !ActivateGrip && !ActivateRelease))    -- 急停（EmergencyStop = FALSE）后下一周期六路动作全部停止（K4）
C2: G(ManualMode && DownButton && !DownLimitSwitch && EmergencyStop -> MoveDown)    -- 手动模式下的启动条件：按钮按下、未到限位且无急停（EmergencyStop = TRUE）（K1）
C4: G(!(MoveDown && MoveUp) && !(MoveLeft && MoveRight) && !(ActivateGrip && ActivateRelease))    -- 三对反向动作两两互斥（K1/K5）
C7: G(DownLimitSwitch -> X(!MoveDown))    -- 到达下限位后下一周期必须停止下行动作（K1）
C6: G(ActivateGrip -> (ActivateGrip W GripLimitSwitch))    -- 抓取输出保持到抓取限位到位为止（K5）
C10: G[0,1](!MoveDown && !MoveUp && !MoveLeft && !MoveRight && !ActivateGrip && !ActivateRelease)    -- 上电首周期无动作输出（初态）
```

### P20　Production Control

难度：hard；类别：C；I/O：17；规约：`data/specs/P20.ltl`。

```text
C4: G(!(MotorForward && MotorReverse))    -- 正反转互斥（K1）
C2: G(kick -> SensorOutput)    -- 出料动作的前提是成品站到位（K4）
C1: G(CompletionLight -> X(!kick))    -- 完成灯点亮后下一周期出料动作必须停止（K4）
C6: G(CompletionLight -> (CompletionLight W !SensorOutput))    -- 完成灯保持到产品离开成品站（K4）
C10: G[0,1](!MotorForward && !MotorReverse && !kick && !CompletionLight)    -- 上电首周期无输出（初态）
```

## A.2　自编题 S01-S14

### S01　双工位气动夹具互锁

难度：easy；类别：A；I/O：8；规约：`data/specs/S01.ltl`。

```text
C1: G(!EStop_NC -> (!ClampLeft && !ClampRight))    -- 急停当周期两侧夹具必须松开（K4）
C2: G(ClampLeft -> LeftPartPresent)    -- 夹紧的前提是对应工位有零件（左侧）（K2）
C2b: G(ClampRight -> RightPartPresent)    -- 夹紧的前提是对应工位有零件（右侧）（K2）
C4: G(!(ClampLeft && ClampRight))    -- 两侧夹具互斥（共用一路气源）（K1）
C10: G[0,1](!ClampLeft && !ClampRight && !Busy)    -- 上电首周期两侧不夹紧、不忙（初态）
```

### S02　输送线正反转与检修锁

难度：easy；类别：A；I/O：8；规约：`data/specs/S02.ltl`。

```text
C1: G(!EStop_NC -> (!MotorFwd && !MotorRev))    -- 急停当周期两个方向都必须断开（K4）
C2: G(MotorFwd -> !MaintKey)    -- 检修钥匙插入时禁止正转（K3）
C2b: G(MotorRev -> !MaintKey)    -- 检修钥匙插入时禁止反转（K3）
C4: G(!(MotorFwd && MotorRev))    -- 正反转互斥（K1）
C9: G(MotorFwd && !MotorRev -> G[0,10](!MotorRev))    -- 正转期间 200 ms 内不得出现反转（换向死区）（K2）
C10: G[0,1](!MotorFwd && !MotorRev)    -- 上电首周期两个方向都不输出（初态）
```

### S03　安全门分级停机

难度：medium；类别：A；I/O：9；规约：`data/specs/S03.ltl`。

```text
C1: G(!EStop_NC -> (!DriveA_Run && !DriveB_Run))    -- 急停当周期两区都停（优先于分级延时）（K3）
C1b: G(DoorSwitch -> F[0,1](!DriveA_Run))    -- 门打开后 A 区当周期必须停（分级停机的高等级侧）（K1）
C5: G(DoorSwitch -> F[0,25](!DriveB_Run))    -- 门打开后 B 区 500 ms 内必须停（低等级侧允许走完当前动作）（K2）
C2: G(DriveA_Run -> (!DoorSwitch && EStop_NC))    -- A 区运行的许可：门关闭且无急停（K3）
C6: G(AlarmLamp -> (AlarmLamp W !DoorSwitch))    -- 门关闭后报警才允许撤销（不得随门抖动闪烁）（K4）
C10: G[0,1](!DriveA_Run && !DriveB_Run && !AlarmLamp)    -- 上电首周期两区都不运行、无报警（初态）
```

### S04　称重零点漂移补偿

难度：medium；类别：B；I/O：7；规约：`data/specs/S04.ltl`。

```text
C4: G(CompensatedWeight == (RawWeight - ZeroOffset) * 0.01)    -- 输出必须等于换算式（不得沿用上一周期的结果）（K2）
C2: G(DriftAlarm -> driftOut)    -- 报警的前提是偏差确实超限（不得空报）（K3）
C6: G(DriftAlarm -> (DriftAlarm W driftBack))    -- 偏差回落到 ±150 以内才允许撤警（滞回保持）（K3）
C7: G(DriftAlarm && driftBack -> X(!DriftAlarm))    -- 偏差回到 ±150 死区内就必须下一周期撤报（不得滞留）（K3）
C10: G[0,1](ZeroOffset == 0 && !DriftAlarm && CompensatedWeight == 0.0)    -- 上电首周期零点为 0、无报警（K4）
```

### S05　泵站流量累计与班次清零

难度：hard；类别：B；I/O：8；规约：`data/specs/S05.ltl`。

```text
C1: G(OverflowFlag -> TotalVolume <= 1000000.0)    -- 溢出标志置位后总量不得继续增长（也不得回绕）（K3）
C2: G(TotalVolume >= 0.0 && ShiftVolume >= 0.0)    -- 两个累计量都不得为负（单向累计）（K1）
C8: G(TotalVolume >= 1000000.0 -> X(OverflowFlag))    -- 达到上限后下一周期必须置溢出标志（K3）
C8b: G(OverflowFlag -> X(OverflowFlag))    -- 溢出标志一旦置位就永久保持（不自动清除）（K3）
C6: G(ShiftVolume <= TotalVolume)    -- 当班流量不得超过累计总量（班次清零不影响总量）（K2）
C10: G[0,1](TotalVolume == 0.0 && ShiftVolume == 0.0 && !OverflowFlag)    -- 上电首周期两个累计量为 0、无溢出（初态）
```

### S06　烘箱分段升温与超温降载

难度：medium；类别：B；I/O：9；规约：`data/specs/S06.ltl`。

```text
C1: G(LoadReduce -> !HeatOn)    -- 降载动作时加热必须关断（保护优先于温控）（K3）
C2: G(HeatOn -> FanOn)    -- 加热的前提是风机运行（禁止干烧）（K4）
C4: G(!(HeatOn && LoadReduce))    -- 加热与降载互斥（K3）
C7: G(OverTempAlarm -> (OverTempAlarm W TempPV <= SetTemp - 3.0))    -- 超温报警保持到温度回落到设定值以下 3 ℃（迟滞）（K3）
C8: G(Segment < 0 || Segment > 2 -> X(Status == 16#8601))    -- 段号非法时下一周期必须报错误码（K1）
C10: G[0,1](!HeatOn && !FanOn && !OverTempAlarm && !LoadReduce)    -- 上电首周期全部输出关断（初态）
```

### S07　灌装四工位节拍控制

难度：hard；类别：C；I/O：12；规约：`data/specs/S07.ltl`。

```text
C1: G(!EStop_NC -> (!Conveyor && !FillValve && !CapMotor && !PackCyl))    -- 急停当周期四路执行器全停（K5）
C2: G(FillValve -> BottleIn)    -- 开灌装阀的前提是瓶子到位（K2）
C4: G(!(Conveyor && FillValve) && !(Conveyor && CapMotor) && !(Conveyor && PackCyl) && !(FillValve && CapMotor) && !(FillValve && PackCyl) && !(CapMotor && PackCyl))    -- 四路执行器两两互斥（单工步动作）（K4）
C6: G(FillValve -> (FillValve W FillDone))    -- 灌装阀保持到灌装完成信号出现（K2）
C9: G(FillValve -> G[0,5](FillValve))    -- 灌装动作至少保持 100 ms（防抖，避免单周期抖动误判完成）（K3）
C10: G[0,1](!Conveyor && !FillValve && !CapMotor && !PackCyl)    -- 上电首周期无动作（初态）
```

### S08　分拣线配方切换

难度：hard；类别：C；I/O：9；规约：`data/specs/S08.ltl`。

```text
C1: G(Busy -> (!SortLeft && !SortRight))    -- 切换配方期间禁止分拣（切换优先于分拣）（K1）
C2: G(SortLeft -> PartHeight > 0.0)    -- 分拣的前提是线上有料（K4）
C4: G(!(SortLeft && SortRight))    -- 左右分拣互斥（K4）
C9: G(Busy -> G[0,100](Busy))    -- 切换状态至少保持 2 s（防止请求抖动造成反复切换）（K2）
C10: G[0,1](!SortLeft && !SortRight && !Busy && ActiveRecipe == 1)    -- 上电首周期默认配方 1、不分拣（初态）
```

### S09　CIP 三步清洗时序

难度：medium；类别：C；I/O：9；规约：`data/specs/S09.ltl`。

```text
C1: G(!EStop_NC -> (!WaterValve && !LyeValve && !RinseValve && !PumpRun))    -- 急停当周期所有阀门与泵关断（K5）
C2: G(PumpRun -> (WaterValve || LyeValve || RinseValve))    -- 泵运行的前提是至少一个阀门打开（禁止空转）（K3）
C4: G(!(WaterValve && LyeValve) && !(WaterValve && RinseValve) && !(LyeValve && RinseValve))    -- 三路阀门两两互斥（同一步只开一个阀）（K2）
C5: G(StartCIP && StepNo == 0 -> F[0,5](StepNo == 1))    -- 启动清洗后 100 ms 内必须进入水洗步（响应时限）（K1）
C10: G[0,1](StepNo == 0 && !PumpRun)    -- 上电首周期步号为 0、泵不运行（初态）
```

### S10　变频器故障码分级报警

难度：easy；类别：D；I/O：6；规约：`data/specs/S10.ltl`。

```text
C1: G(VFDRun && VFDFaultCode != 16#0000 && VFDFaultCode != 16#0001 -> TripOutput)    -- 运行中出现重故障码（除 16#0001 轻故障外）必须当周期跳闸（K4）
C2: G(TripOutput -> !VFDRun)    -- 跳闸的许可形式：跳闸时不得处于运行状态（K2）
C6: G(TripOutput -> (TripOutput W ResetBtn))    -- 跳闸保持到复位按钮（不能随故障码消失自动复位）（K3）
C7: G(VFDFaultCode == 16#0001 && VFDRun -> X(VFDRun))    -- 轻故障只报警不跳闸，运行状态不得因轻故障改变（K1）
C10: G[0,1](!TripOutput && !AlarmLamp && Status == 16#0000)    -- 上电首周期不跳闸、不报警（初态）
```

### S11　传感器断线检测与降级运行

难度：hard；类别：D；I/O：7；规约：`data/specs/S11.ltl`。

```text
C1: G(DegradedMode -> ControlValue == FallbackValue)    -- 降级期间输出必须是备用值（不得继续输出失效测量值）（K4）
C2: G(DegradedMode && SensorValid -> G[0,150](DegradedMode))    -- 信号恢复后仍须保持降级至少 3 s（150 个周期）才允许退出，防止接线抖动反复切换（K3）
C6: G(DegradedMode -> AlarmLamp)    -- 降级期间报警灯常亮（K5）
C10: G[0,1](!DegradedMode && !SensorValid && ControlValue == 0.0 && !AlarmLamp)    -- 上电首周期未降级、信号无效、输出 0（安全默认），报警灯灭（初态）
```

### S12　急停后安全重启与班次统计

难度：medium；类别：D；I/O：8；规约：`data/specs/S12.ltl`。

```text
C1: G(!EStop_NC -> !MachineRun)    -- 急停当周期设备必须停（K1）
C2: G(MachineRun -> DoorClosed)    -- 运行的许可：安全门关闭（K2）
C3: G(StartBtn && !DoorClosed -> X(!MachineRun))    -- 门未关时按启动不得启动（三步确认缺一不可）（K2/K3）
C4: G(!(MachineRun && AlarmLamp))    -- 报警期间不得运行（互斥）（K1）
C10: G[0,1](!MachineRun && ShiftCount == 0 && !AlarmLamp)    -- 上电首周期不运行、计数为 0（初态）
```

### S13　双段输送合流同步与堵料防撞

难度：hard；类别：C；I/O：11；规约：`data/specs/S13.ltl`。

```text
C1: G(!LineRun -> !MainMotor && !MergeMotor)    -- 总停时两段电机都必须停（K1）
C4: G(PartAtMerge -> !MergeMotor)    -- 合流段有料时汇流段不得送料（防撞互锁）（K2）
C5: G(JamSensor && LineRun -> F[0,100] JamAlarm)    -- 堵料 2 s 内必须报警（100 周期）（K3）
C6: G(JamAlarm && !(ResetBtn && !JamSensor) -> X(JamAlarm))    -- 报警锁存到复位条件满足（K3/K4）
C7: G(PartOnMain && MainMotor && !SpeedHigh -> F[0,150] SpeedHigh)    -- 有料 3 s 内切高速（150 周期）（K5）
C10: G[0,1](!MainMotor && !MergeMotor && !SpeedHigh && !JamAlarm && Status == 16#0000)    -- 上电首周期全部停机、无报警（初态）
```

### S14　液压站压力分级加载与卸荷

难度：medium；类别：B；I/O：8；规约：`data/specs/S14.ltl`。

```text
C1: G(Pressure > 160.0 -> X(!LowPump && !HighPump && ReliefValve))    -- 过压当周期卸荷并停泵（K1）
C2: G(Pressure < 120.0 && PumpEnable && !AlarmLamp -> X(LowPump))    -- 低压加载条件成立时一周期内投泵（K2）
C4: G(!(ReliefValve && LowPump) && !(ReliefValve && HighPump))    -- 卸荷阀与泵不得同时为 TRUE（K5）
C6: G((Pressure < 0.5 || Pressure > 250.0) -> F[0,10] AlarmLamp)    -- 传感器越界 200 ms 内报警（10 周期）（K4）
C7: G(HighPump && Pressure >= 100.0 && Pressure < 140.0 -> X(HighPump))    -- 滞回带内保持高压泵状态，不抖动（K3）
C10: G[0,1](!LowPump && !HighPump && !ReliefValve && !AlarmLamp && Status == 16#0000)    -- 上电首周期不加载、无报警（初态）
```

# 参考文献

[1] GenAI 赋能工业编程课程组. 期末大作业五人分工与交付清单: v3.0[Z]. 2026.

[2] International Electrotechnical Commission. IEC 61131-3: Programmable controllers - Part 3: Programming languages[S]. Geneva: IEC, 2013.

[3] NAMUR. NE 43: Signal level for fault information from measuring transducers[S]. Leverkusen: NAMUR, 2003.

[4] International Organization for Standardization. ISO 4413: Hydraulic fluid power - General rules and safety requirements for systems and their components[S]. Geneva: ISO, 2010.

[5] CODESYS GmbH. CODESYS Development System command line and scripting documentation[EB/OL]. https://content.helpme-codesys.com/.

[6] Beremiz Project. MATIEC compiler source and command-line documentation[EB/OL]. https://github.com/beremiz/matiec.

[7] Aider AI. Aider documentation: OpenAI-compatible APIs, scripting and lint/test integration[EB/OL]. https://aider.chat/docs/.

[8] Zertz777. Gen-AI: PLC ST generation and cycle-level verification repository[EB/OL]. https://github.com/zertz777/Gen-AI.

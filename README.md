# GenAI 赋能工业编程：PLC ST 生成与逐周期验证

本仓库是《GenAI 赋能工业编程》期末大作业提交件，包含 34 道 PLC Structured Text 题目、177 条 LTL 条款、自研 Agent 与 Aider 基线、214 条逐周期测试用例、四组正式实验、测试与形式化验证材料，以及 Word/PDF 报告和 A1-A7 提交包。

正式实验口径为 P01-P20 与 S01-S14 共 34 题，两个框架乘两个模型，最终矩阵为 34 x 4 = 136 个 run。任务书早先的 32 题、128 主轮和 48 复跑数字已被当前冻结题集取代。

## 三条命令

以下命令在仓库根目录执行，使用 Python 3.10+。第 2、3 条使用 deterministic fixture，不调用付费模型或 PLC 编译器，只验证 Agent 的解析、候选、修复、终止和日志链路。

```bash
pip install -r requirements.txt
python agent/run.py --framework self --model fixture --tasks data/tasks/S01.yaml --out runs/demo --mode fixture
python agent/run.py --framework self --model fixture --tasks data/tasks --task-set all34 --out runs/all34 --mode fixture
```

第一条安装测试、绘图和报告构建依赖。第二条运行单题。第三条运行一组 34 题的 fixture。重复运行会依据已完成记录执行 `SKIP`，不会向已有终态重复追加。

## 目录与状态

| 目录 | 内容 | 状态 |
| --- | --- | --- |
| `data/` | 34 份题面、34 份 LTL、来源表、多样性矩阵、评审记录和冻结哈希 | 已完成 |
| `agent/` | 七模块自研 Agent、入口、提示词、配置、CODESYS 桥和 fixture 样例 | 已完成 |
| `baseline/` | Aider 适配器与统一判定桥 | 已完成 |
| `tests/` | 214 条用例、逐周期比对器、ST 解释器、缺陷单和测试报告 | 已完成 |
| `verify/` | 变异测试与 PLCVerif 材料 | 已完成到当前可用范围 |
| `experiments/` | 136 个最终 run、32 个修订替换 run、汇总表、统计脚本和独立重放记录 | 已完成 |
| `figures/` | 4 张 300 dpi 实验图及其数据来源 | 已完成 |
| `docs/` | 环境、框架、判据、问答、报告章节和 Word/PDF 成稿 | 已完成 |
| `release/` | v1.0 源码快照与 SHA-256 清单 | 已完成 |
| `final/` | A1-A7 提交包、README 和 12 项检查表 | 已完成 |

## 正式实验结果摘要

| 组别 | 框架 | 模型 | 整题通过 |
| --- | --- | --- | ---: |
| E1 | Aider 0.86.2 | `deepseek-v4.1-flash` | 18/34（52.94%） |
| E2 | Aider 0.86.2 | `gpt-6.1-sol` | 16/34（47.06%） |
| E3 | 自研 Agent | `deepseek-v4.1-flash` | 8/34（23.53%） |
| E4 | 自研 Agent | `gpt-6.1-sol` | 7/34（20.59%） |

这些数字描述冻结题集、同一实验机和当前配置下的一次运行。E3 有 24 题受预算终止影响，其中包含框架把 UTF-8 字节长度当作 token 的已知实现问题；P19、S11、S05-06 仍有判据争议。因此不能据此宣称某个框架或模型普遍更优。详细分析见 `docs/report/ch4.md` 和 `docs/统稿前审查说明.md`。

## 数据、测试与验证

数据自检：

```bash
python tools/ltl_check.py --quiet
python tools/schema_check.py
python tools/import_bank.py --check
```

测试链路：

```bash
python -m pytest tests -q
python tests/run_tests.py --cases tests/cases/P03.csv --io tests/cases/_fixtures/P03.io.json --out tests/results/P03.jsonl --backend echo
```

统计复算：

```bash
python tools/stats.py
python experiments/verify_package.py
```

`tools/reproduce_runs.py` 会用仓库 ST 解释器对全部有源码 run 做独立重放。当前 132 个有源码 run 中完成 72 个，60 个受解释器未支持的方言限制，4 个 abandoned run 没有源码；结果标记为 `independent_replay`，不冒充 CODESYS 原始 actual。

提交检查：

```bash
python tools/check_submission.py
```

## 运行真实 Agent

真实运行需要 CODESYS profile、成员4测试器和模型凭据。复制 `agent/configs/default.yaml` 后，按 `docs/codesys_setup.md` 生成本机配置，并设置环境变量 `DMXAPI_API_KEY`。不要把 Key 写进配置、日志或提交包。

```bash
python agent/run.py --framework self --model <准确模型ID> --tasks data/tasks --task-set all34 --out runs/E3 --setting-id E3 --config local/codesys.local.yaml
```

Aider 基线在独立 Python 环境安装 `requirements-baseline.txt` 后运行。实际实验使用的 Aider 版本为 0.86.2。

## 关键口径

- 「整题通过」要求权威编译通过，且该题所有有效功能用例逐拍通过。
- `pass / fail / timeout / error / missing` 分态统计；`timeout/error/missing` 不并入模型失败率。
- seed 42 是本地运行标识，默认未发送给模型 API，不保证服务端逐字复现。
- token 只累加服务商返回的已知 usage；未知用量单列，不能按零处理。
- 34 题主轮固定使用 34 分母；补充的 32 个修订 run 替换对应旧记录，不与首轮相加。

## 常见问题

1. **`pytest` 报 `ModuleNotFoundError: runner`？**
   在仓库根目录执行 `python -m pytest tests -q`，不要先进入 `tests/`。

2. **fixture 结果能算实验通过率吗？**
   不能。fixture 只验证程序控制流，`metadata.execution_mode=fixture`，`eligible_for_experiments=false`。

3. **为什么 P18 的声明骨架未通过 CODESYS？**
   当前 profile 不支持题目使用的 `VARIANT`。这是环境方言限制，单列为工具/环境问题，不记为模型功能失败。

4. **正式实验为何是 136 run？**
   冻结题集为 34 题，2 框架 x 2 模型 x 34 = 136。32 题口径已被 `docs/tasks_note.md` 与 `data/CHANGELOG.md` 的 v1.7 记录取代。

5. **能不能在其他电脑直接复现 136 run？**
   可以复算现有 136 条记录，但不能原样重放模型和 CODESYS 中间过程。换机真实运行须重新登记模型 ID、Aider、CODESYS、设备库和测试执行器，并生成新的实验批次，不能覆盖本批次。

## 许可与引用

课程作业用途。公共题来源与改编过程见 `data/provenance.csv`；外部工具与规范引用见 `docs/report/report.md` 的参考文献。

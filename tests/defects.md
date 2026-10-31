# 缺陷单（defects）

成员4 的 D4.4 交付物。**一条失败 = 一条缺陷**，不多不少；回归结果单独一节，不混进第一轮。

## 当前状态

| 项 | 值 |
| --- | --- |
| 真实缺陷条数 | **0**（D2-6 全量第一轮尚未开始：等成员2 的 `test/actual/*.csv`） |
| 干跑数据 | 见 `results/_dryrun/`，**是假数据，不记缺陷** |
| 已复现的抽样失败 | 无 |

> 判定口径：`fail`（逐拍失配）才记缺陷；`timeout` / `error` / `missing` 是工具或环境问题，
> 记在各自的列里，**不进失败率、也不算缺陷**。这一条与 `results/_dryrun/README.md` 一致。

## 字段（缺一列成员2 就没法修）

| 字段 | 说明 | 示例 |
| --- | --- | --- |
| `defect_id` | `DEF-` + 三位序号 | DEF-001 |
| `task_id` | P01—P20 / S01—S14 | P03 |
| `run_id` | 组别_题号_r次_s种子 | E3_P03_r1_s42 |
| `case_id` | 用例号 | P03-02 |
| `cycle` | 首个失配拍 | 2 |
| `variable` | 首个失配变量 | hiAlarm |
| `expected` / `actual` | 期望值 / 实际值（按声明类型写） | TRUE / FALSE |
| `kind` | 逻辑 / 时序 / 边界 / 编译 / 工具超时 | 时序 |
| `repro` | 一行可直接粘贴的复现命令 | 见下 |
| `status` | 待修 / 已修待回归 / 已关闭 / 不修（附理由） | 待修 |

## 表格

| defect_id | task_id | run_id | case_id | cycle | variable | expected | actual | kind | repro | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| — | — | — | — | — | — | — | — | — | 等待真实 actual | — |

## 复现命令模板

```bash
python tests/run_tests.py --cases tests/cases/P03.csv \
  --io tests/cases/_fixtures/P03.io.json \
  --out tests/results/<run_id>/P03.jsonl \
  --backend replay --actual experiments/runs/E3/P03_r1_s42/test/actual \
  --run-dir experiments/runs/E3/P03_r1_s42
```

整组复现：

```bash
python tests/run_batch.py --runs experiments/runs/E3 \
  --out tests/results/batch/E3 --framework self --model <model>
```

## 回归（D2-7 填）

| defect_id | 修复后状态 | 是否引入新失败 | 引入的破坏数 | 证据 |
| --- | --- | --- | --- | --- |
| — | — | — | — | 等待第一轮缺陷单 |

“修复引入的破坏数”是本表最有价值的一列：它直接回答“修 A 是不是把 B 改坏了”。

# 成员4 交接说明（D2 24:00 / D3 10:00 / D3 14:00）

交接只认文件：每条都给**路径 + 文件数 + 自检结论**，接收方当场打开/跑一遍再回“收到”。

## 1 现在就能交的（不依赖 actual）

| 交付物 | 路径 | 数量 | 自检结论 | 接收方 |
| --- | --- | --- | --- | --- |
| 用例库 | `组员4/tests/cases/*.csv` | 34 份 / 214 条 / 22 634 拍 | `pytest` 47 passed；`coverage.csv` 143/143；逐题四类齐 | 成员2 |
| 执行器 | `组员4/tests/run_tests.py`、`runner/` | 7 个模块 | echo 34/34 全 pass；broken 能定位到拍+变量 | 成员2 |
| 批量入口 | `组员4/tests/run_batch.py` | 1 个 | 136 个假 run 干跑，0 失配（`results/_dryrun/`） | 成员3 |
| 缺陷单 | `组员4/tests/defects.md` | 1 份 | 字段 11 列齐全；真实缺陷 0 条（等 actual） | 成员2 |
| 测试报告 | `组员4/tests/report.md` | 1 份 | 口径/规模/链路已写实，结果节标“待填” | 成员3 |
| D3 计划 | `组员4/tests/plan_d3.md` | 1 份 | 30 个变异体 + 14 条 PLCVerif 属性，题号已定 | 成员3 |
| 答辩问答 | `组员4/docs/qa/member4.md` | 3 条 | 每条 10 秒内能翻到证据 | 成员3 |
| 统计口径 | `组员4/docs/stats_alignment.md` | 1 份 | 字段与分母规则，供 `stats.py` 对齐 | 成员3 |

## 2 需要成员5 合并的两个路径

`组员4/` 目前是成员4 的独立目录，进主仓库时要落到任务书定的位置：

| 现在 | 合并到 | 谁做 | 注意 |
| --- | --- | --- | --- |
| `组员4/tests/` | `<repo>/tests/` | 成员5 | `run_tests.py` 名字不许改（D4.2 的验收路径）；`results/_selftest/`、`results/_dryrun/` 一并保留，它们是自检证据 |
| `组员4/docs/qa/member4.md` | `<repo>/docs/qa/member4.md` | 成员5 | 成员3 合并 12 条主问答时要用 |

合并后请回一句“路径已通”，否则 D4.1/D4.3 的验收路径不存在。

## 3 等 actual 到了才能交的

| 交付物 | 路径 | 判据 | 时点 |
| --- | --- | --- | --- |
| 第一轮结果 | `<run>/test/cases_result.jsonl` | 136 跑齐全，缺失率 ≤2% | D2 24:00 |
| 汇总 | `tests/results/batch/E*/summary.csv` | 与成员3 的 `summary.csv` 逐 run 对得上 | D2 24:00 |
| 缺陷单（真实） | `tests/defects.md` | 条数 = 失败数；前 3 条 5 分钟内可复现 | D2 24:00 |
| 回归表 | `tests/defects.md` 末节 | 能算出“修复引入的破坏数” | D2 23:00 |
| 变异得分 | `verify/mutants/` | 30 个变异体，killed/30 | D3 12:00 |
| PLCVerif | `verify/plcverif/` | 14 条属性三态 + 至少 1 条反例 | D3 18:00 |

## 4 给成员2 的一句话（复制即用）

> 每个 run 请产出：`source/final.st`、`test/actual/<case_id>.csv`（列名与 fixture 的 OUT 列逐字一致，
> `cycle` 从 1 起连续，BOOL 写 `TRUE/FALSE`，WORD 写 `16#xxxx`，TIME 写 `T#500ms`）；
> 整题超时/跑崩写 `test/status.json`：`{"status":"timeout","reason":"..."}`。
> 我这边一条命令出汇总：`python tests/run_batch.py --runs experiments/runs/E3 --out tests/results/batch/E3`。

配套材料：

- 格式模板：`examples/actual_package.zip`（一个完整 run 的目录 + 6 份 actual 示例 + `task_card.json`），
  解压后照着填即可；
- 测试器：`tests/tester_cli.py`（按成员2 的 `tools.test` 协议输出 `status/total/passed/passed_ids/failures`）；
- 群聊文案：`docs/messages.md`（给成员2/1/3/5 各一条，复制即用）。

## 5 当前阻塞（D2 24:00 前必须解决）

1. **没有 actual**：`experiments/` 与 `agent/` 都还不存在，D2-6 全量第一轮无法开跑；
2. **4 条规约/约束缺陷**待成员1 改：P13 C2 `!= 4`、S11 C2/C4 与 3 s 确认期、P01 C2、P17 K3 错误码；
3. **34 vs 32 题**：按 34 题走，主轮 136 跑，成员3 的 128/176 要改。

阻塞项不解决，上面第 3 节的所有交付物都只能写“顺延”，不能拿假数据凑。

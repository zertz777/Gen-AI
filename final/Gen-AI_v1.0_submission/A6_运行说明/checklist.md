# 提交前 12 项检查表

检查日期：2026-11-09。检查对象：`final/Gen-AI_v1.0_submission.zip`。

| 序号 | 检查项 | 责任人 | 结果 | 证据 |
| ---: | --- | --- | --- | --- |
| 1 | 34 份题面齐全，schema_check 通过 | 成员1 | 通过 | `data/tasks` 34 份；`tools/schema_check.py` |
| 2 | 34 份规约一一对应，无孤立条款 | 成员1 | 通过 | `data/specs` 34 份、177 条；`tools/ltl_check.py` |
| 3 | provenance.csv 34 行，来源完整 | 成员1 | 通过 | `data/provenance.csv` |
| 4 | 框架一条命令可跑单题并留产物 | 成员2 | 通过 | README 第 2 条；`runs/demo` |
| 5 | 正式结果保留 22 字段契约 | 成员2 | 通过 | `experiments/runs/*/*/result.json` |
| 6 | 四组配置齐全，seed 与题集记录 | 成员3 | 通过 | `experiments/configs/E1-E4.yaml` |
| 7 | 136 个最终 run 齐全 | 成员3 | 通过 | `experiments/runs/`；`experiments/verify_package.py` |
| 8 | summary 可由 stats.py 重算 | 成员3/5 | 通过 | `tools/stats.py --check` |
| 9 | 用例不少于 150 条，每题有安全用例 | 成员4 | 通过 | 214 条；`tests/cases` |
| 10 | 失败可定位到周期，并尽可能独立重放 | 成员4/5 | 部分通过，已如实记录 | 316 条缺陷均含周期；解释器完成 72/132 个有源码 run，60 个受未支持 ST 方言限制，4 个 abandoned 无源码；见 `experiments/reproduction/summary.jsonl` |
| 11 | README 三条命令在干净环境可用 | 成员5 | 通过 | 当前会话完成单题和 34 题 fixture |
| 12 | 包内无 key、绝对路径和临时文件 | 成员5 | 通过 | `tools/check_submission.py`、`checklist.json` |

结论：第 1-9、11-12 项完成；第 10 项在原实验材料保留的范围内完成，完整 CODESYS 逐拍证据缺失是当前提交件的已知风险。签名栏留待各责任人最终确认：

| 成员1 | 成员2 | 成员3 | 成员4 | 成员5 |
| --- | --- | --- | --- | --- |
| 待签 | 待签 | 待签 | 待签 | 待签 |

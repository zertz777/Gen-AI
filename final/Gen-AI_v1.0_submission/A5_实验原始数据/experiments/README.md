# 正式实验数据

`runs/E1` 至 `runs/E4` 是供报告和图表直接使用的最终矩阵，共 136 个 run。每组 34 题，目录名为 `<setting>_<task>_<repeat>_<seed>`。

`archive/source_runs` 保留成员3交付的两个批次：

- `formal34_v7`：首轮主实验，共 136 条原始记录。
- `formal34_frozen8_v1`：八道判据修订题的补跑记录，共 32 条。

最终矩阵用 32 条补跑记录替换对应旧记录，其余 104 条沿用首轮；旧记录不删除、不相加。逐题映射见 `per_task.csv` 的 `source_batch` 与 `result_path` 列。

可复算文件：

- `per_task.csv`：136 行逐题逐组结果。
- `34_task_matrix.csv`：34 行四组状态矩阵。
- `summary.csv`：四组汇总。
- `statistics_notes.txt`：统计口径。
- `figures/`：四张图的 PNG 与 SVG。

统计脚本是仓库根目录的 `tools/stats.py`。成员3交付的 `finalize_results.py`、`render_charts.py` 与 `verify_package.py` 保留在 `experiments/`，用于复核来源批次的完整性。

`reproduction/` 是成员5用仓库自带 ST 解释器做的独立离线重放，`evidence_kind=independent_replay`，不冒充 CODESYS 原始 actual。132 个有 `final.st` 的 run 中完成 72 个；60 个触发解释器未支持的 ST 方言；另 4 个 abandoned run 没有源码。结果见 `reproduction/summary.jsonl`。

精简实验包不含完整的 CODESYS 逐拍 actual 中间文件。失败记录可追到 `result.json`、`metadata.json`、候选评估和最终 ST；完整 CODESYS 逐拍重放仍需实验机保留的完整批次。

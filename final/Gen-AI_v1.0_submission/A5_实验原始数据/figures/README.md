# 报告图表

| 编号 | 文件 | 内容 | 数据来源 |
| --- | --- | --- | --- |
| 图4-1 | `fig4-1_strict_pass.png` | 四组整题通过数 | `experiments/per_task.csv` |
| 图4-2 | `fig4-2_difficulty.png` | 按易/中/难分层的整题通过率 | `experiments/per_task.csv`、`data/tasks/*.yaml` |
| 图4-3 | `fig4-3_status.png` | 四组终态分布 | `experiments/per_task.csv` |
| 图4-4 | `fig4-4_latency.png` | 单题端到端耗时的中位数和 p95 | `experiments/per_task.csv` |

四张位图均为 300 dpi PNG。`图1_整题通过.png` 至 `图4_运行耗时.png` 是成员3交付的原文件；`fig4-*` 是报告使用的稳定命名副本，内容一致。

重算方式：

```bash
python experiments/render_charts.py
```

绘图需要 `matplotlib`，并依赖已通过 `experiments/verify_package.py` 检查的最终逐题表。

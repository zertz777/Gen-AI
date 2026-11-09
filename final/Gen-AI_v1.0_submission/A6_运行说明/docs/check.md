# 交叉检查记录

检查日期：2026-11-09。

| 检查项 | 结果 | 证据或处置 |
| --- | --- | --- |
| 题号 P/S 是否统一两位 | 通过 | `data/tasks`、`tests/cases` 均为 34 个同名题号 |
| 题面与规约是否一一对应 | 通过 | 34 份 YAML、34 份 LTL |
| 实验题数是否统一 | 通过 | 四组各 34 题，最终 136 run |
| 修订记录是否被错误相加 | 通过 | 32 个补跑为替换，104 个沿用首轮 |
| 汇总能否从逐题表重算 | 通过 | `python tools/stats.py --check` |
| 图表是否有数据来源 | 通过 | `figures/README.md` |
| API Key、私钥和 Bearer 凭据 | 合并前未发现 | `tools/check_submission.py` |
| 本机绝对路径 | 打包时清理并在最终树复扫 | `tools/package_final.py` |
| 完整逐拍 actual | 部分完成 | 独立解释器重放 72 个有源码 run；60 个使用解释器未支持的 ST 方言；4 个 abandoned 无 final.st，详见 `experiments/reproduction/summary.jsonl` |
| 换机真实复现 | 未完成 | 环境与复现边界已写入 `docs/env.md`；不属于可在当前材料中伪造的绿色项 |

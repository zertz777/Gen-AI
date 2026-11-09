# 成员5答辩问答（3条）

## Q1 没装过项目的电脑怎样验证，三条命令能证明什么？

按 `README.md` 执行安装依赖、单题 fixture 和 34 题 fixture 三条命令，可以验证题面解析、候选、修复、终止、日志和批量入口。它不调用付费模型或 CODESYS，因此不能证明模型质量或正式实验已跨机复现。真实运行还需按 `docs/env.md` 和 `docs/codesys_setup.md` 配置 Key、CODESYS、Aider 与测试器；卡在哪一步可以从工具错误和原始输出定位。

证据：`README.md`、`docs/env.md`、`agent/run.py`、`agent/logs/`。

## Q2 报告里的数字和实验目录怎样对应？

报告第4章的每个组级数字由 `experiments/per_task.csv` 汇总，`experiments/runs/<E*>/<run_id>/result.json` 对应单题原始结果，`tools/stats.py` 可重建 `experiments/summary.csv`。图1至图4保留 PNG 和数据来源，详见 `figures/README.md`。P01、P08、P13、P14、P17、P18、P19、S11 的修订记录通过 `source_batch` 区分，替换旧记录而不是相加。

证据：`docs/report/ch4.md`、`experiments/per_task.csv`、`experiments/summary.csv`、`tools/stats.py`。

## Q3 提交包里会不会带 Key、本机绝对路径或临时文件？

合并前已扫描成员2/3的 3438 个文件，未发现私钥、API Key 或 Bearer 凭据，也没有超过 20 MB 的单文件。打包脚本会对文本再次清理本机绝对路径，`tools/check_submission.py` 复扫提交树中的凭据、绝对路径和临时后缀。CODESYS 本机配置、安装包和许可证不进入仓库与提交包。

证据：`tools/package_final.py`、`tools/check_submission.py`、`checklist.json`。

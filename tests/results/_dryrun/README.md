# results/_dryrun/ —— 假数据的批量干跑（**不是实验结果**）

## 这是什么

成员2 的逐周期 actual 还没交付，但 `run_batch.py` 的发现、汇总、缺失率、三态口径
可以先验证。本目录是 `tests/gen/make_fake_runs.py` 生成的**假实验目录**跑出来的汇总：

| 文件 | 说明 |
| --- | --- |
| `summary.csv` | 136 个假 run 的汇总（E1—E4 × 34 题） |
| `manifest.json` | 每个 run 的预期结局，用来逐行对账 |

**任何数字都不能进报告第 4 章。** 真实数据只能来自 `experiments/runs/` 下成员2 产出的 actual。

## 怎么复现

```bash
python tests/gen/make_fake_runs.py --out %TEMP%/fake_runs
python tests/run_batch.py --runs %TEMP%/fake_runs --out %TEMP%/fake_batch
```

生成 + 批跑各约 1.4 s（136 run / 856 条用例判定）。

## 这一轮压到了什么

| 结局 | run 数 | 验证的口径 |
| --- | --- | --- |
| `passed` | 109 | 全部用例通过 |
| `best-effort` | 17 | 11 个单拍错值（fail=1）+ 6 个缺一个 case 文件（error=1） |
| `abandoned` | 5 | 2 个 `status.json: timeout` + 3 个 actual 缺输出列 |
| `missing` | 5 | 整个 run 没有 actual，**不计入失败率、也不进分母** |

对账结果：136 行与 `manifest.json` **逐 run 一致，0 失配**；每个 run 都写出了
`test/cases_result.jsonl`。对应的自动测试是 `tests/test_dryrun.py`（4 项）。

## 顺带定下来的两条口径

1. `missing` 与 `error` 都不进失败率；`timeout` 单列。三者在 `summary.csv` 里各有独立列
   （`test_missing` / `test_error` / `test_timeout`），不合并进 `test_failed`。
2. 单个 run 的 `final_status` 判定：全过 = `passed`；有通过但有失败/工具故障 =
   `best-effort`；一条都没过 = `abandoned`；没有 actual = `missing`。

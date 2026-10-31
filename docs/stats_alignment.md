# 测试结果 ↔ 成员3 统计的字段对齐说明

给成员3 的 `tools/stats.py` 与 `experiments/summary.csv` 对齐用。目标：**同一份数据，
两个人各算一遍得同一组数**（任务书 T4.4 的互算校验）。

## 1 数据流

```
experiments/runs/<E1—E4>/<题号>_r<次>_s<种子>/
├── source/final.st                 # 成员2
└── test/
    ├── actual/<case_id>.csv        # 成员2（逐拍实际输出）
    ├── status.json                 # 成员2（整题超时/跑崩时才有）
    └── cases_result.jsonl          # 成员4（逐条用例判定）
                │
                ▼
tests/run_batch.py --runs experiments/runs/E3 --out tests/results/batch/E3
                │
                ▼
tests/results/batch/E3/summary.csv  # 逐 run 一行
tests/results/batch/E3/runs.jsonl    # 逐条用例
```

## 2 `summary.csv` 字段（17 列）

| 列 | 取值 | 说明 |
| --- | --- | --- |
| `run_id` | `E3_P07_r1_s42` | 与成员3 的 `run_id` 必须逐字一致 |
| `setting_id` | E1—E4 | 组别 |
| `framework` | self / baseline | 由命令行传入，不从目录猜 |
| `model` | 模型名 | 同上 |
| `task_id` | P01—P20 / S01—S14 | 34 题口径 |
| `repeat_idx` | 1、2… | 主轮为 1 |
| `seed` | 42 | 与目录名一致 |
| `test_total` | 整数 | 该题用例总数，**等于用例 CSV 的 case 数** |
| `test_passed` | 整数 | `status=pass` 的条数 |
| `test_failed` | 整数 | `status=fail`（逐拍失配）的条数 |
| `test_timeout` | 整数 | `status=timeout` 的条数 |
| `test_error` | 整数 | 工具故障（actual 缺列、runner 非 0 退出）的条数 |
| `test_missing` | 整数 | 整个 run 没有 actual 的条数 |
| `latency_s` | 秒 | 该 run 各用例耗时的均值；缺失为空 |
| `verify_status` | pass / violated / timeout / skipped | 第一轮固定 `skipped`，等 PLCVerif |
| `final_status` | passed / best-effort / abandoned / missing | 逐 run 结论，见 §3 |
| `note` | 文本 | 超时原因、缺失原因 |

不变式：`test_total = test_passed + test_failed + test_timeout + test_error + test_missing`。

## 3 分母与四态（**最容易被算错的地方**）

| 状态 | 进不进失败率 | 进不进分母 | 成员3 怎么用 |
| --- | --- | --- | --- |
| `pass` | 进分子 | 进 | 通过数 |
| `fail` | 进分子（算失败） | 进 | 失败数 |
| `timeout` | **不进** | **不进** | 单列一栏（任务书表 5-3 要求） |
| `error` | **不进** | **不进** | 工具故障，单列 |
| `missing` | **不进** | **不进** | 缺失率单列，不凑分母 |

- 题目级通过率 `EPR_task` = 该组 `final_status=passed` 的题数 ÷ 34；
- 用例级通过率 `EPR_case` = `Σtest_passed ÷ Σ(test_total − test_timeout − test_error − test_missing)`；
- 不要把 `timeout/error/missing` 并进 `fail`，否则四组之间不可比（任务书 5.3 的硬口径）。

## 4 八项指标里，哪些该找谁要

| 指标 | 来源 | 备注 |
| --- | --- | --- |
| CPR₁ / CPRₙ（首轮/修复后编译通过率） | **成员2 的日志**（`compile_status`、`compile_stage`） | 测试侧不算编译，`cases_result.jsonl` 里没有编译状态 |
| EPR_task / EPR_case | 本文件的 `summary.csv` | 成员4 出 |
| ARR（平均修复轮数） | 成员2 的 `repair_rounds` | 成员4 不记修复轮次 |
| 平均耗时 / p95 | 本文件的 `latency_s` + `runs.jsonl` 的逐条 `latency_s` | 超时题按 900 s 单列，不混进均值 |
| token 成本 | 成员2 的日志（`tokens_in/out`） | 测试侧不记 |
| VPR（验证通过率） | `verify/plcverif/`（D3） | 三态：通过/违反/超时，超时不算违反 |

**一句话**：编译类指标找成员2，执行类指标找成员4，别拿测试结果反推编译通过率。

## 5 对账三步（互算校验一次）

```bash
# 1) 成员4 出汇总
python tests/run_batch.py --runs experiments/runs/E3 --out tests/results/batch/E3

# 2) 对账（run_id 集合 + 逐 run 的 test_total/test_passed + 合计）
python tests/gen/check_alignment.py \
  --ours tests/results/batch/E3/summary.csv \
  --theirs experiments/summary.csv --setting E3

# 3) 抽一个 run 回指证据
python tests/run_tests.py --cases tests/cases/P07.csv \
  --io tests/cases/_fixtures/P07.io.json --out /tmp/P07.jsonl \
  --backend replay --actual experiments/runs/E3/P07_r1_s42/test/actual \
  --run-dir experiments/runs/E3/P07_r1_s42
```

三步都一致，才算“同一份数据得同一组数”。

## 6 五个常见坑

1. **把 `results/*.jsonl` 当实验结果**：那是 echo 自检（期望值=实际值），只证明链路通，
   不是被测程序的结果；真实结果在 `experiments/runs/<run>/test/cases_result.jsonl`。
2. **分母用 32**：成员1 已交 34 题（v1.6），主轮 4×34=136 跑，复跑 48，合计 184。
3. **把 `missing` 当失败**：会凭空拉低通过率，且四组缺失数不同，直接失真。
4. **超时题按 900 s 混进均值**：任务书要求单列一栏。
5. **只报通过率不报分母**：每个数字旁边写清 `分母 = test_total − timeout − error − missing`。

## 7 复现与变更

- `summary.csv` 由 `run_batch.py` 一条命令重算，不允许手改；
- 用例改了（`cases/*.csv`）必须重跑 `run_batch`，否则 `test_total` 与用例行数对不上；
- 题面/规约冻结（D3 10:00）后，`tests/` 与 `experiments/` 都不再改口径，只修缺陷。

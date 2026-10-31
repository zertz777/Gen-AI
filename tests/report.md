# 测试报告（tests/report.md）

成员4 的 D4.3 交付物。D2-6 的全量第一轮尚未开始（等成员2 的 actual），
下面先把**已经能确定的部分**写实，结果类小节留空并标明数据来源。

## 1 范围与判定口径

| 项 | 口径 |
| --- | --- |
| 被测对象 | 4 组实验（E1—E4）× 34 题，每组每个 run 的 `source/final.st` |
| 判定粒度 | **逐扫描周期**比对，不是只看末态 |
| 状态 | `pass` / `fail` / `timeout` / `error`，批量汇总另有 `missing` |
| 失败率分母 | 只含 `pass + fail`；`timeout`、`error`、`missing` 单列，**不进分母** |
| 单题超时 | 900 s（`exec` 后端为 subprocess 硬超时） |
| 编译超时 | 90 s，写 `status.json` 后整题判 `timeout` |

数据来源：`runner/verdict.py`、`runner/actual_io.py`、`results/_dryrun/README.md`。

## 2 用例库规模

| 指标 | 数值 | 来源 |
| --- | --- | --- |
| 题数 | 34（P01—P20、S01—S14） | `cases/*.csv` |
| 用例条数 | 214 | `cases/*.csv` |
| 逐拍行数 | 22 634 | `cases/*.csv` |
| K 覆盖 | 143 / 143 | `coverage.csv` |
| 类别分布 | 正常 68 / 边界 38 / 异常 48 / 安全 60 | `cases/*.csv` 的 `category` 列 |
| 四类齐 | 34 / 34 题 | `pytest::test_every_task_has_four_categories` |
| 每题最少条数 | 4（S03） | 同上 |

## 3 执行链路

```
cases/<题号>.csv ─┐
_fixtures/*.io.json ─┼→ case_loader（校验列名/类型/拍号）
                     ├→ backend（replay 读 actual / exec 调外部命令）
                     ├→ compare（首个失配拍 + 变量 + 期望/实际）
                     ├→ verdict（pass/fail/timeout/error）
                     └→ cases_result.jsonl → run_batch → summary.csv
```

关键约束（D2-4 定）：

- actual 列名必须与 fixture 的 OUT 列逐字一致，缺列判 `error` 而不是 `fail`；
- actual 值按 fixture 声明类型解析（BOOL 只认 `TRUE/FALSE`，WORD 认 `16#xxxx`）；
- 同一程序、同一 seed 跑两次，结论必须一致。

## 4 第一轮结果（**待 D2-6 填**）

| 组别 | run 数 | pass | fail | timeout | error | missing | 题目级通过率 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| E1 | — | — | — | — | — | — | — |
| E2 | — | — | — | — | — | — | — |
| E3 | — | — | — | — | — | — | — |
| E4 | — | — | — | — | — | — | — |

数据来源：`experiments/runs/E*/`、`results/batch/E*/summary.csv`。
每个数字必须能回指 `run_id` 与 `cases_result.jsonl` 的具体行。

### 4.1 干跑（不是结果）

用 `gen/make_fake_runs.py` 造的 136 个假 run 验证了汇总口径：136 行与 manifest 逐 run 一致，
`passed 109 / best-effort 17 / abandoned 5 / missing 5`。**这一节只证明脚本没算错，不能当实验结果。**
证据：`results/_dryrun/summary.csv`。

## 5 失败分布与复现（**待 D2-6 填**）

- 按原因分类统计：逻辑 / 时序 / 边界 / 编译 / 工具超时；
- 每条失败对应 `defects.md` 的一条缺陷，必须带首失配拍与复现命令；
- 典型失败至少写 3 个（安全类、时序类、边界类各一个）。

## 6 回归（**待 D2-7 填**）

| 项 | 数值 |
| --- | --- |
| 复测题数 | — |
| 修好 | — |
| 仍失败 | — |
| **修复引入的破坏数** | — |

“修坏已通过用例”是框架质量的核心证据，必须单列，不能并进“仍失败”。

## 7 已知局限

1. **`X` 拍不判定**：语义未定的拍写 `X`（见 `ambiguities.md` A-01…A-46），
   这些拍上的错误测不出来，报告里要给出 `X` 占输出总格数的比例。
2. **期望值来源**：用例期望值按 K 约束手推，不是从被测程序反推；但也没有独立的
   参考实现做交叉验证，所以“用例本身写错”只能靠人工复核兜底。
3. **题量口径**：按 34 题（成员1 v1.6）执行；任务书排期写的 32 题/128 跑已作废，
   报告里的分母一律用 34 题/136 跑。
4. **S05 溢出边界不可达**：K3 的 1 000 000 L 需要 2×10⁶ 个脉冲，接口无法注入初值，
   `S05-06` 只覆盖“清零与脉冲同拍”的边界，溢出本身未测。
5. **工具故障与模型失败分离**：`error`/`timeout`/`missing` 均不计入模型失败；
   若成员3 的 `stats.py` 口径与此不一致，以 `summary.csv` 的列为准重新对齐。

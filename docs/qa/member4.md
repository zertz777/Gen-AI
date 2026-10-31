# 成员4 答辩问答（3 条）

给成员3 合并成 12 条主问答用。每条都能在 **10 秒内翻到证据文件**；括号里是证据路径。
口径：只讲测试与验证，不替成员2 讲框架、不替成员3 讲统计。

---

## Q1　“编译通过不等于功能正确——你们凭什么说程序跑不对？”

**30 秒版**：我们不按“最终状态”判，也不抽查，而是**逐扫描周期**比对：每个周期注入输入、
读全部输出，和期望值逐拍比；一旦不一致，直接报出**第几拍、哪个变量、期望值、实际值**。
抽查会漏——任务书引用的实测是每 5 拍抽一次会漏掉约 21.66% 的失败样本，且漏检率随相位在
12.10%—28.03% 之间波动，所以抽查出来的通过率既偏高又不稳。

**证据**

- `tests/runner/compare.py`：逐拍比对，返回首个失配的 `{cycle, variable, expected, actual}`；
- `tests/results/_selftest/P03_broken.jsonl`：故意翻转第一拍 `hiAlarm`，结果精确报出
  `cycle=1, variable=hiAlarm, expected=true, actual=false`；
- `tests/runner/actual_io.py`：actual 缺列/拍号不对判 `error`，不会“缺列就当通过”；
- `tests/cases/_schema.md`：期望输出逐拍写，`cycle=0` 只是初态行，不参与比对。

**追问兜底**：“长定时题 1500 拍怎么逐拍写？”——`gen/gen_P05.py`、`gen_P13.py`、`gen_S09.py`
按采样点铺满全拍，人工只写边界拍；改生成器重跑，不手改 CSV。

---

## Q2　“超时、编译失败、工具崩了，会不会都算成模型写错？”

**30 秒版**：不会，我们分四态：`pass / fail / timeout / error`，批量汇总里再加 `missing`。
**失败率的分母只含 pass + fail**；超时、工具故障、缺 actual 各自单列，既不进分子也不进分母。
这一条是写死在脚本里的，不是口头约定——成员3 的 `summary.csv` 直接用这几列。

**证据**

- `tests/runner/verdict.py`：四态定义，`BackendTimeout`/`BackendError` 分别映射到 timeout/error；
- `tests/run_batch.py` 的 `summary.csv` 字段：`test_passed / test_failed / test_timeout /
  test_error / test_missing` 五列分开；
- `tests/results/_dryrun/README.md`：136 个假 run 的压测里，5 个 missing、26 条 error、
  11 条 timeout **都没有**被算进 `test_failed`；
- `tests/runner/backends.py`：`exec` 后端用 `subprocess.run(timeout=)` 真杀进程，
  不是线程软超时。

**追问兜底**：“编译超时怎么记？”——成员2 写 `<run>/test/status.json`：
`{"status":"timeout","reason":"compile timeout 90s"}`，整题判 timeout，不读 actual、不判 fail。

---

## Q3　“用例的期望值是谁算的？会不会和被测程序同源，或者用 X 放水？”

**30 秒版**：期望值按**题面的 K 约束**手推，不读任何生成的 ST 代码，所以不存在“程序怎么写、
用例就怎么判”。语义没定的拍才写 `X`，而且每一条 `X` 都在歧义单里登记、有编号、有处置；
`X` 只出现在输出列，输入列写 `X` 会被 loader 直接拒掉。我们也在报告里如实写了两个局限：
没有独立参考实现做交叉验证；`X` 拍上的错误测不出来。

**证据**

- `tests/cases/*.csv` 与 `tests/gen/*.py`：期望值来自 K 条款，逐拍写；
- `tests/coverage.csv`：143 条 K 全部有用例对应；其中 35 条 LTL 表达不了的（R6 口径）
  也逐条落到用例；
- `tests/ambiguities.md`：A-01…A-46，每条写明“影响的拍 + 当前处置（按 X / 已澄清 / 自行决定）”；
- `tests/report.md` §7：已披露“期望值无独立参考实现”“X 拍不判定”“S05 溢出边界不可达”；
- `pytest::test_no_all_dont_care_case`：一条用例如果所有输出都写 X，测试直接失败。

**追问兜底**：“X 占比多少？”——D2-6 第一轮跑完后由 `cases_result.jsonl` 统计，
写进 `report.md` §7 第 1 条；现在不报口算数，避免和真实数据对不上。

---

## 附：三条最容易被追问的边界

| 追问 | 一句话回答 | 证据 |
| --- | --- | --- |
| 34 题还是 32 题？分母是多少？ | 按成员1 v1.6 的 34 题走，主轮 136 跑，分母恒为 34 | `tests/report.md` §7 第 3 条 |
| 同一程序跑两次结论会变吗？ | 不会：用例固定、seed 固定，`run_batch` 同输入同输出 | `tests/README.md` §3.5 |
| 缺 actual 的 run 怎么算？ | 记 `missing`，不进失败率、也不进分母，单独报缺失率 | `run_batch.py`、`results/_dryrun/README.md` |

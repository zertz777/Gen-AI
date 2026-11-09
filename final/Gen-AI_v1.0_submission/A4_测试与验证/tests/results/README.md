# results/ —— 执行器输出

## 先看这一句

**本目录里的 `<题号>.jsonl` 不是「被测 ST 程序的测试结果」，而是执行器的链路自检结果。**

它们由 `--backend echo` 生成：把用例里写的**期望值原样当成实际值**返回。
所以「34 题全绿」只能证明 **loader → compare → verdict 这条链路是通的**，
**不能**证明任何一份 ST 代码是对的。真实结论要等接上真实执行后端后重跑。

## 文件说明

| 文件 | 后端 | 说明 |
| --- | --- | --- |
| `P01.jsonl` … `S14.jsonl`（34 份） | `echo` | 期望值 = 实际值。用于回归执行器本身：改了 `compare.py` / `verdict.py` 之后重跑，若这里出现 fail，说明执行器坏了，不是被测程序坏了 |
| `_selftest/P01_broken.jsonl` 等（5 份） | `broken` | 故意把第一拍第一个 BOOL 输出（或 BOOL 数组首元素）翻转。用于证明 `compare` 能报出「第几拍、哪个变量、期望 vs 实际」 |
| `_dryrun/summary.csv` | `replay`（假 actual） | 136 个假 run 的批量汇总，用来验证 `run_batch.py` 的缺失率与四态口径。**不是实验结果**，见 `_dryrun/README.md` |

`_selftest/` 里的失败是**故意制造的**，不要当成缺陷。

## 怎么复现

```bash
# 链路自检（34 题）
python tests/run_tests.py --cases tests/cases/P03.csv \
  --io tests/cases/_fixtures/P03.io.json \
  --out tests/results/P03.jsonl --backend echo

# 失配定位自检
python tests/run_tests.py --cases tests/cases/P03.csv \
  --io tests/cases/_fixtures/P03.io.json \
  --out tests/results/_selftest/P03_broken.jsonl --backend broken

# 真实产物（成员2 导出的逐拍实际值，目录或单文件都行）
python tests/run_tests.py --cases tests/cases/P03.csv \
  --io tests/cases/_fixtures/P03.io.json \
  --out tests/results/P03_real.jsonl --backend replay \
  --actual experiments/runs/E3/P03_r1_s42/test/actual \
  --run-dir experiments/runs/E3/P03_r1_s42

# 一整组实验 → summary.csv（字段对齐成员3）
python tests/run_batch.py --runs experiments/runs/E3 \
  --out tests/results/batch/E3 --framework self --model <model>
```

`run_batch.py` 的产物在 `--out` 目录下：`summary.csv`（逐 run 一行）与 `runs.jsonl`（逐条），
每个 run 自己还会留一份 `<run>/test/cases_result.jsonl`。

## 四态口径

`status` 有四种：`pass` / `fail` / `timeout` / `error`，批量汇总里另有 `missing`。

| 状态 | 含义 | 进失败率 |
| --- | --- | --- |
| `pass` / `fail` | 逐拍全对 / 有失配 | 进 |
| `timeout` | 超时（单题 900 s、编译 90 s） | 不进，单列 |
| `error` | 工具故障：actual 缺列、runner 退出码非 0、status.json 不合法 | 不进，单列 |
| `missing` | 整个 run 没有 actual | 不进，也不进分母 |

超时与工具故障都不并入 fail——否则成员3 的四组数据不可比。

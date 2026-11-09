# tests/ —— 测试与逐周期对拍

成员4 的交付目录（任务书 T4.1—T4.9）。本文件说明目录结构与约定：**成员2、成员3 看第 3 节；成员1 看第 6 节（已自行决定的事项通报）。**

## 1 目录结构

```
tests/
├── run_tests.py                 # 单题入口（D4.2 的验收路径，不许改名）
├── run_batch.py                 # 批量入口：一个实验目录 → summary.csv
├── test_runner.py               # 执行器自身的单测
├── test_contract.py             # actual CSV / exec 后端的接口契约测试
├── test_batch.py                # 批量汇总的端到端测试
├── test_dryrun.py               # 假实验目录的干跑测试（不依赖真 actual）
├── test_alignment.py            # 与成员3 summary.csv 的对账脚本单测
├── test_interp.py               # 兜底解释器的单测（含 P03 参考实现逐拍全 pass）
├── coverage.csv                 # K 号 → LTL 条款 → 用例 的双向索引（脚本生成）
├── ambiguities.md               # 歧义单
├── defects.md                   # 缺陷单与回归记录（D4.4）
├── report.md                    # 测试报告（D4.3）
├── plan_d3.md                   # D3 变异测试 30 个 + PLCVerif 14 条属性的选样与计分
├── refimpl/<题号>.st            # 成员4 自写的参考实现（变异测试底本，不是模型产物）
├── runner/
│   ├── __init__.py
│   ├── case_loader.py           # 读 CSV、校验字段与字面量
│   ├── compare.py               # 逐周期比对，定位首个失配
│   ├── verdict.py               # 四态：pass / fail / timeout / error
│   ├── actual_io.py             # actual CSV 的读取与校验（成员2 的契约）
│   ├── backends.py              # echo / broken / replay / exec 四个后端
│   ├── io_normalize.py          # 把上游 io_table 转成 fixture
│   └── interp/                  # ST 子集解释器（exec 后端的兜底实现，见 3.7）
│       ├── lexer.py             # 词法（含 (* *) 嵌套注释、16#、T#500ms）
│       ├── parser.py            # 语法 → AST（VAR 块 / IF / CASE / FOR / ARRAY / STRUCT）
│       ├── st_types.py          # IEC 类型、字面量、CSV 回写
│       ├── state.py             # 变量表 + TON/TOF/R_TRIG/F_TRIG/CTU/CTD
│       ├── eval.py              # 按拍执行
│       └── run.py               # CLI：--inputs/--outputs 或 --cases/--out-dir
├── gen/
│   ├── _emit.py                 # CSV 生成小工具（fmt / Case / write_cases）
│   ├── gen_fixtures.py          # 34 份 fixture + coverage.csv 生成器
│   ├── gen_Pxx.py               # P05/P06/P07/P10/P13/P15—P20 的长定时/复杂题
│   ├── gen_Sxx.py               # S01—S14 全部由生成器出（含 30 s/60 s 计时）
│   ├── gen_gap.py               # D2-5 补四类缺口（36 条），必须在各题生成器之后跑
│   ├── make_fake_runs.py        # 造假实验目录，压测 run_batch（不是实验结果）
│   └── check_alignment.py       # 与成员3 的 summary.csv 对账（run_id/总数/逐 run）
├── cases/
│   ├── _schema.md               # 用例文件规范（写用例前必读）
│   ├── _fixtures/<题号>.io.json # 每题的 I/O 方向与类型（34 份，脚本生成）
│   └── <题号>.csv               # 用例，一题一份
└── results/                     # 执行器输出；见 results/README.md
                                 #   <题号>.jsonl = echo 链路自检（不是真实测试结果）
                                 #   _selftest/ = 故意改坏的失配定位演示
                                 #   _dryrun/ = 假实验目录的批量干跑（不是实验结果）
```

## 2 自检命令（tests 内部）

```bash
# 1) 跑单测（改完执行器必跑）
cd tests && python -m pytest -q

# 2) 跑一题（用期望值当实际值，验证链路）
python tests/run_tests.py --cases tests/cases/P03.csv \
  --io tests/cases/_fixtures/P03.io.json \
  --out tests/results/P03.jsonl --backend echo

# 3) 故意改坏一个输出，验证失配能被精确定位
python tests/run_tests.py --cases tests/cases/P03.csv \
  --io tests/cases/_fixtures/P03.io.json \
  --out tests/results/_selftest/P03_broken.jsonl --backend broken

# 4) 变异测试（真实底本 S10）：冻结用例 3/5，补 2 条后 5/5
python verify/run_mutants.py --task S10 --out verify/mutants
python verify/run_mutants.py --task S10 \
  --extra verify/mutants/S10_extra_cases.csv --out verify/mutants_augmented
```

### 2.1 当前进度（D3 收尾）

| 项 | 数量 |
| --- | --- |
| 已写用例的题目 | **34 / 34**（P01—P20 + S01—S14） |
| 用例条数 | **214**（下限 150；每题 ≥4 条，平均 6.3 条） |
| 逐拍行数 | **22 636 行**（含 214 条 `cycle=0` 初态行），实际扫描拍 **22 422** |
| K 覆盖 | **143 / 143**（`coverage.csv` 零空格） |
| 用例类别 | 正常 68 / 边界 38 / 异常 48 / 安全 60，**逐题四类齐**（`pytest` 断言） |
| 单测 | **71 passed**（执行器 50 + 接口契约/批量/干跑/对账 + 解释器 15） |
| 真实缺陷 | **316 条**（来自 132 份 `evaluation.json`，见 `defects.md`） |
| 与成员3 对账 | **132 / 132 一致，0 不一致**（见 `report.md` §4.1） |

生成器一览：`gen_P05/P06/P07/P10/P13/P15—P20.py`、`gen_S01—S14.py`、`gen_gap.py`。
`gen_gap.py` 是 D2-5 的补缺脚本：只追加「边界/异常/正常」缺口用例（36 条），
**必须在各题生成器之后运行**，否则会被覆盖（`pytest` 的逐题四类齐会立刻发现）。
含长定时的题（P05/P06/P10/P13/S07/S08/S09/S11/S12/S13）必须改生成器后重跑，
不要直接手改 CSV——手写续行极易多写一个逗号，导致整行右移。

`category` 列（正常/边界/异常/安全）由 `gen/_emit.py` 的 `classify()` 按 `purpose`
自动推断，也可在 `Case(...)` 里显式覆盖。当前 `pytest` 断言的是：取值合法、**全局**四类齐、
每题至少 1 条安全类；**逐题四类齐**（T4.2 的字面要求）尚未断言，缺口与补法见 D2-5。

## 3 给成员2 的接口约定（D2-4 起生效）

### 3.1 一个 run 的目录

```
<run_dir>/                          # experiments/runs/<E1—E4>/<题号>_r<次>_s<种子>/
├── source/final.st                 # 被测程序（成员2 产出）
└── test/
    ├── actual/<case_id>.csv        # 逐拍实际输出（成员2 必须产出）
    ├── status.json                 # 整题超时/跑崩时写（成员2 可选）
    └── cases_result.jsonl          # 判定结果（成员4 的脚本写）
```

成员2 只需要保证 `source/final.st` + `test/actual/*.csv`（+ 必要时 `status.json`）存在，
判定、比对、汇总全部在 `tests/` 这一侧完成——避免出现"两套标准"。

### 3.2 actual CSV 格式

```csv
case_id,cycle,hiAlarm,loAlarm,error,status
P03-01,1,TRUE,FALSE,FALSE,16#0000
P03-01,2,TRUE,FALSE,FALSE,16#0000
```

| 规则 | 违反时的判定 |
| --- | --- |
| 列名与 `cases/_fixtures/<题号>.io.json` 的 OUT 列逐字一致 | 缺列 → `error`（工具故障，不算模型失败） |
| `cycle` 从 1 起、连续；允许带 `cycle=0` 初态行（读取时忽略） | 跳号/重号/拍数不符 → `error` |
| 值按 fixture 声明的类型写（BOOL 只认 `TRUE/FALSE`，WORD 认 `16#xxxx`，TIME 认 `T#500ms`） | 类型错 → `error` |

**为什么单独强调类型**：旧版 replay 把 `"TRUE"` 当字符串和 `True` 比，BOOL 列必然判 fail。
这条路径以前没有真 actual 文件，所以一直没暴露；D2-4 起由 `runner/actual_io.py` 统一解析。

### 3.3 status.json（整题级别）

```json
{"status": "timeout", "reason": "compile timeout 90s"}
```

`status` ∈ `pass / fail / timeout / error`。写 `timeout` 时整题所有用例判 `timeout`，
脚本不会去读不存在的 actual 文件——这样"编译超时"不会被算成"模型写错"。

### 3.4 三条命令

```bash
# 1) 单题链路自检（不接真程序，应全 pass）
python tests/run_tests.py --cases tests/cases/P03.csv \
  --io tests/cases/_fixtures/P03.io.json --out tests/results/P03.jsonl --backend echo

# 2) 单题接成员2 的实际输出
python tests/run_tests.py --cases tests/cases/P03.csv \
  --io tests/cases/_fixtures/P03.io.json --out tests/results/P03.jsonl \
  --backend replay --actual experiments/runs/E3/P03_r1_s42/test/actual \
  --run-dir experiments/runs/E3/P03_r1_s42

# 3) 一整组实验：E3 下所有 run → summary.csv
python tests/run_batch.py --runs experiments/runs/E3 \
  --out tests/results/batch/E3 --framework self --model deepseek-v4.1-flash
```

没有 actual 时可以用 `exec` 后端直接调外部命令（`{program} {inputs} {outputs}` 占位符，
`subprocess.run(timeout=)` 硬超时）：

```bash
python tests/run_tests.py --cases tests/cases/P03.csv \
  --io tests/cases/_fixtures/P03.io.json --out tests/results/P03.jsonl \
  --backend exec --program path/to/final.st --timeout 900 \
  --runner-cmd '["python","baseline/run_one.py"]'
```

### 3.5 四态与超时口径

| 状态 | 含义 | 进不进失败率 |
| --- | --- | --- |
| `pass` / `fail` | 逐拍全对 / 有失配 | 进 |
| `timeout` | 超时（单题 900 s，编译 90 s） | **不进**，单列 |
| `error` | 工具故障：actual 缺列、runner 退出码非 0、status.json 不合法 | **不进**，单列 |
| `missing` | 整个 run 没有 actual（批量汇总里才有） | **不进**，也不进分母 |

真正的硬超时由 `ExecBackend` 的 `subprocess.run(timeout=)` 提供（会 kill 子进程）；
`replay`/`echo` 走的是线程软超时，只作兜底，不能拿来当 900 s 口径的证据。

### 3.6 作为成员2 的 `test.command` 接入

成员2 的 `agent/src/tools.py` 用四个占位符调外部测试器。把 `tests/` 拷进他的包根目录后，
`agent/configs/*.yaml` 的 `tools.test` 填：

```json
"test": {
  "command": [
    "python", "tests/tester_cli.py",
    "--source", "{source}",
    "--task-card", "{task_card}",
    "--cases-dir", "{cases_dir}",
    "--result", "{result}"
  ],
  "timeout_s": 90,
  "cases_dir": "tests/cases"
}
```

`tester_cli.py` 按 `docs/toolchain.md` §4 写结果 JSON：

```json
{"status": "pass", "total": 6, "passed": 6,
 "passed_ids": ["P03-01", "P03-02"], "failures": []}
```

- 退出码：`pass=0`、`fail=1`、`tool_error=2`、`skipped/timeout=0`；
- 后端默认 `auto`：有 actual 用 `replay`；没有 actual 但设了 `--runner-cmd`（或环境变量
  `PLC_RUNNER_CMD`）用 `exec`；两者都没有 → `skipped`，**绝不伪造 pass**；
- `exec` 的命令模板支持 `{source} {program} {inputs} {outputs} {task_card}`，
  runner 按 `inputs.csv` 逐拍跑、把逐拍输出写进 `outputs.csv`（格式同 actual）。

自检（示例包应输出 `pass/total=6`）：

```bash
python tests/tester_cli.py \
  --source examples/actual_package/E3_P03_r1_s42/source/final.st \
  --task-card examples/actual_package/E3_P03_r1_s42/task_card.json \
  --cases-dir tests/cases \
  --result examples/actual_package/E3_P03_r1_s42/test/result.demo.json
```


### 3.7 兜底解释器（成员4 自写，绝不冒充成员2 产物）

用途只有一条：**变异测试需要"能跑起来"的 ST**。成员2 的真实执行链没到位时，
用 `tests/refimpl/*.st`（按 K 条款自己写的参考实现）+ `runner/interp/` 跑出逐拍 actual。

| 项 | 说明 |
|---|---|
| 支持范围 | FUNCTION_BLOCK/PROGRAM、VAR 块、赋值、IF/CASE/FOR/WHILE/REPEAT/RETURN、AND/OR/XOR/NOT、算术与比较、ARRAY（含 `ARRAY[*]` 变长）、STRUCT、`STRING(n)`、TON/TOF/TP/R_TRIG/F_TRIG/CTU/CTD |
| 不支持 | `VAR_EXTERNAL`、METHOD/PROPERTY、`AT %I*` 直接地址、指针/REF、VARIANT、FB 实例数组 → **明确报错**，不静默算错 |
| 扫描周期 | 20 ms（`--cycle-ms` 可改）；时间语义"同一拍先累加后判定"（D-11） |
| 边界 | `cycle=0` 只设初值、不执行；输出在 FB 体执行后采样；死循环兜底报错，不拖成 900 s 超时 |

两条命令（契约与成员2 的 `runner-cmd` 一致，可互换）：

```bash
# 1) 单用例（ExecBackend 就是这么调的）
python tests/runner/interp/run.py --source tests/refimpl/P03.st \
  --inputs in.csv --outputs out.csv --case-id P03-01

# 2) 整题（变异测试用）：一次写出该题全部 actual
python tests/runner/interp/run.py --source tests/refimpl/P03.st \
  --cases tests/cases/P03.csv --io tests/cases/_fixtures/P03.io.json \
  --out-dir verify/mutants/M-P03-1/test/actual
```

接执行器的写法（已实测：参考实现 6/6 pass；把 `Value > hiLevel` 反相后 4/6 fail）：

```bash
python tests/run_tests.py --cases tests/cases/P03.csv \
  --io tests/cases/_fixtures/P03.io.json --out tests/results/P03.exec.jsonl \
  --backend exec --program tests/refimpl/P03.st \
  --runner-cmd '["python","tests/runner/interp/run.py","--source","{source}","--inputs","{inputs}","--outputs","{outputs}","--case-id","{case_id}"]'
```

**红线**：解释器产出的 actual 只能用于变异测试底本。拿它当"模型产物跑出来的 L2 结果"，
等于自己出题自己判——`report.md` §7 已按此写死。

## 4 I/O 规范化规则

fixture 由 `tests/gen/gen_fixtures.py` 从上游 `data/tasks/*.yaml` 自动生成，规则集中在 `runner/io_normalize.py`，只做三件事：

| 规则 | 说明 | 例子 |
| --- | --- | --- |
| 补父结构前缀 | 裸字段名补成 `xxx[].field` | P07 `priority` → `pumpGroup[].priority` |
| 丢弃容器列 | INOUT 结构体数组若已有子列，容器本身不单列 | P07 `pumpGroup`、P08 `channels`、P17 `recipe` 均丢弃 |
| INOUT 转输入 | 没有子列的 INOUT 当输入用，输出侧不判定 | P08 `analogValues`、P18 `item`/`buffer` |

子列的类型自动升一维：`priority: INT` → `pumpGroup[].priority: ARRAY[1..5] OF INT`，因为这一列装的是 5 台泵的同一个字段。

**依据**：上游 P08 已经把逐元素字段写成 `channels[].enable`，P07 的 `pumpGroup` 和 P17 的 `recipe` 是同一个模式，所以补前缀不是猜，是照抄同项目的既有写法。

上游改好后只需删掉 `FIELD_FIX` 里对应几行，**用例文件不用动**。

重新生成：

```bash
python tests/gen/gen_fixtures.py
```

同一条命令还会刷新 `tests/coverage.csv`（`K 号 → LTL 条款 → 覆盖它的 case_id`）。


## 5 用例约定速查

- 一行一个扫描周期；`cycle=0` 是初态行，同时承载 `purpose` 与 `spec_refs`
- `spec_refs` **K 号为主、C 号为辅**（`K3;K4;C7`）
- 题目没说清的拍一律写 `X`，并记进 `tests/ambiguities.md`
- 数组/结构体用 JSON 字面量，BOOL 沿用 `TRUE/FALSE`

## 6 已自行决定的事项（通报，不必等回复）

以下是成员4 在 `tests/` 内部做出的选择。它们**不修改上游 `data/` 的任何文件**，因此不需要等待确认即可推进；若成员1 或评审有不同意见，按「回滚位置」改一处即可全量生效，用例与结果重跑一次就行。

状态只有三种：`生效` / `生效（假设，待确认）` / `已回滚`。

| 编号 | 决定 | 依据 | 回滚位置 | 状态 |
| --- | --- | --- | --- | --- |
| D-01 | 长定时用例由脚本生成（`tests/gen/gen_Pxx.py`），**逐拍写全**，只把未定义的边界拍写 `X` | P13 为 1500 拍，手写不现实；生成器写全拍反而比人工采样更严格 | 对应 `tests/gen/gen_<题号>.py` 的采样逻辑 | 生效 |
| D-02 | 全组扫描周期 **20 ms**，时间字面量一律折算成拍数 | `docs/tasks_note.md` 第 6 节换算表 | `tests/gen/` 的 `CYCLE_MS` 常量 | 生效 |
| D-03 | P19 的 `Start` 按 **上升沿** 处理 | 单步模式「每按一次执行一步」的通常语义 | `tests/gen/P19_*.py` 的 `EDGE` 参数 | 生效（假设，待确认） |
| D-04 | `spec_refs` 以 **K 号为主、C 号为辅** | C2 在 34 题恒中、无区分度；C 号是语义族槽位而非条款编号 | 各用例 `cycle=0` 行；`tests/coverage.csv` | 生效 |
| D-05 | P07 裸字段名映射为 `pumpGroup[].*`；P17 同理映射为 `recipe[].*` | 同项目 P08 已用 `channels[].enable` 写法（详见第 4 节） | `runner/io_normalize.py` 的 `FIELD_FIX` | 生效（P17 部分为假设，待确认） |
| D-06 | 用例总量目标 **170 条**（150 为下限） | 143 条 K 只剩 7 条余量，撑不住「每 K 至少 1 条 + 每题至少 1 条安全类」 | `tests/coverage.csv` | 生效 |
| D-07 | 数组/结构体用 JSON 字面量，BOOL 沿用 ST 写法 `TRUE/FALSE`（loader 内部转小写再解析） | 使用者只记一套语法 | `runner/case_loader.py` 的 `parse_value` | 生效 |
| D-08 | 超时独立成 `timeout` 态，绝不并入 `fail` | 否则成员3 的四组数据不可比 | `runner/verdict.py` | 生效 |
| D-09 | INOUT 结构体容器不单列，子列升一维（`pumpGroup[].priority` 类型为 `ARRAY[1..5] OF INT`） | 容器与逐元素字段是同一个东西，列两遍会重复；类型升维才能写整列 | `runner/io_normalize.py` 的 `_drop_containers` | 生效 |
| D-10 | fixture 由脚本从 `data/tasks/*.yaml` 生成，不手写 | 34 题手工维护必出错；上游一改重跑即可 | `tests/gen/gen_fixtures.py` | 生效 |
| D-11 | 计时类输出按「**同一拍先累加后判定**」写期望值（去抖满额那一拍就动作，运行时间在启动当拍即累加 CycleTime） | 需求原文「accumulate ... while VFD_RUN is TRUE」的直读；滞后一拍的实现会在边界拍差 1 个周期 | 各 `tests/gen/gen_Pxx.py` 的边界拍；`P04.csv` 的 `PUMP_RUNTIME_ACC` | 生效（假设，待确认） |
| D-12 | 用例增加 `category` 列（正常/边界/异常/安全），由 `purpose` 自动推断、可显式覆盖 | 任务书 T4.2 要求四类必须齐、每题至少 1 条安全类；不落成列就只能靠人眼看 | `tests/gen/_emit.py` 的 `classify()`；`cases/_schema.md` 第 2 节 | 生效（8 字段之外的新增列，loader 向后兼容） |
| D-13 | 四类缺口的 36 条用例由 `gen/gen_gap.py` 统一追加（边界 23 / 异常 12 / 正常 1），另将 P02-05、S05-05 改判为异常类；新增「逐题四类齐」断言 | 23 题有生成器、9 题是手写 CSV，逐题改生成器风险高；集中追加只碰新用例，已有用例零改动 | `tests/gen/gen_gap.py`；`test_runner.py::test_every_task_has_four_categories` | 生效（重跑任一题生成器后需再跑一次 `gen_gap.py`） |
| D-14 | P19 的 `EmergencyStop` 按原始 I/O 表写：`FALSE`=急停触发、`TRUE`=正常；用例统一为此语义 | I/O 表是接口定义，优先于题内约束；P19-05 本来就是 FALSE=急停，只有 P19-08/09 原按 K4 的 TRUE 写反 | `tests/gen/gen_gap.py` 的 P19 段；`ambiguities.md` A-47 | 生效（假设，待成员1 修正 K4/C1/C2） |

### 6.1 仍需上游一句话确认的阻塞项

下面这几条**不在 D 表里**——它们要么改上游文件，要么影响别人的产出，成员4 无权自行决定。明细见 `tests/ambiguities.md`。

| 编号 | 问题 | 卡住什么 |
| --- | --- | --- |
| A-11 | P09 `windowSizeReached` 的语义 | 该输出目前只能全标 `X`，等于白测 |
| A-15 | P19 `Start` 是上升沿还是电平 | 全部单步模式用例（当前按 D-03 的假设顶着） |
| A-22 | `INOUT` 但无子列的变量（P18 `item`/`buffer`）是否也要判定输出 | 现在只当输入用，输出侧不判定 |
| A-23 | P01 的 C2 与需求正文「泵 continues to work」冲突 | P01 用例绕开冲突，但**规约 C2 本身要改** |
| A-27 | P13 的 C2 写 `HVAC_MODE_SELECTOR != 4`，需求夜间模式是 3 | 用例按 3 写，**规约 C2 需改成 `!= 3`** |
| — | 34 题是最终题量还是留了缓冲 | 成员3 的实验矩阵 128 跑 vs 136 跑 |

> P17 的字段归属已按 D-05 处理（`recipe[].*`），依据是 P08 的 `channels[].enable` 同构写法；若成员1 认为应挂在 `recipeIn` 上，改 `FIELD_FIX` 一行即可。

> 约定：以上任一条被否决或澄清后，只改「回滚位置」一处，用例重跑一次即可，不影响其他题目。
>
> `tests/gen/` 与 `tests/coverage.csv` 已随 D-01 / D-06 落地：`gen_fixtures.py` 生成 fixture 与覆盖索引，`gen_P05.py`、`gen_P06.py`、`gen_P10.py`、`gen_P13.py` 生成长定时用例。


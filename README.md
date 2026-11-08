# Gen-AI · PLC ST 代码生成与逐周期验证

《GenAI 赋能工业编程》期末大作业交付仓库：34 道 PLC 题（P01—P20 公共题 + S01—S14 自编题），
两组 Agent 框架 × 两个基座模型，四组实验，全部按 **20 ms 扫描周期逐拍**判定。

> **仓库状态（2026-11-08）**：成员1 的题集与规约、成员2 的 Agent 框架与 Aider 适配层、成员4 的测试与验证已入库。
> 实验产物和最终打包待合并。README 由成员5 最终定稿。

## 目录与状态

| 目录 | 内容 | 状态 | 负责人 |
| --- | --- | --- | --- |
| `tests/` | 214 条用例、逐周期执行器、缺陷单、测试报告、ST 解释器 | ✅ 已入库 | 成员4 |
| `docs/` | 成员1的题集说明与报告第2章、成员2的框架与报告第3章、成员4的判据与解释器说明、答辩问答 | ✅ 已入库 | 成员1、成员2、成员4 |
| `examples/` | 一个完整 run 的格式样例（`actual` CSV、`task_card`） | ✅ 已入库 | 成员4 |
| `data/` | 34 份题面 YAML（P01—P20 + S01—S14）+ 34 份 LTL 规约（177 条款）+ 来源表/多样性矩阵/评审记录/SHA256 | ✅ 已入库 | 成员1 |
| `tools/` | 题库导入、LTL/schema 校验、元数据生成、编译环境配置与检查 | ✅ 已入库 | 成员1、成员2 |
| `refs/` | 课程原始题库 JSON，供 `import_bank.py --check` 重放 | ✅ 已入库 | 成员1 |
| `agent/` | 自研 Agent 七模块、统一入口、提示词、配置与 CODESYS 桥接 | ✅ 已入库 | 成员2 |
| `baseline/` | 现成框架（Aider）适配层 | ✅ 已入库 | 成员2 |
| `experiments/` | 136 条正式 run 记录 + summary | ⏳ 待成员3 合并 | 成员3 |
| `figures/` | 4 图 2 表（PNG + 源文件） | ⏳ 待成员3 合并 | 成员3 |
| `final/` | A1—A7 提交包 + 检查表 | ⏳ 待成员5 打包 | 成员5 |

## 三条命令

### 1）装依赖

```bash
python -m pip install -r requirements.txt
```

当前测试部分只依赖 Python 3.10+ 标准库（`pytest` 除外）：

```bash
pip install pytest
```

### 2）跑单题（今天就能跑）

用期望值当实际值，验证"用例 → 逐拍比对 → 四态判定"整条链路：

```bash
python tests/run_tests.py \
  --cases tests/cases/P03.csv \
  --io tests/cases/_fixtures/P03.io.json \
  --out tests/results/P03.jsonl --backend echo
# 期望：P03: pass=6 fail=0 timeout=0 error=0
```

没有真实产物时，也可以直接用仓库自带的 ST 解释器跑参考实现：

```bash
python tests/runner/interp/run.py \
  --source tests/refimpl/P03.st \
  --cases tests/cases/P03.csv --io tests/cases/_fixtures/P03.io.json \
  --out-dir /tmp/P03_actual
```

### 3）离线演示 Agent 流程

```bash
python agent/run.py --framework self --model fixture --tasks data/tasks/S01.yaml --out experiments/runs/demo --mode fixture
```

将 `--tasks data/tasks/S01.yaml` 改为 `--tasks data/tasks --task-set all34` 即可演示全部 34 题。
演示走模拟编译和测试。正式实验需配置模型凭据、权威编译器及功能测试接口，具体参数见[工具接入说明](docs/toolchain.md)。

## 测试链路（成员4 部分，全部可跑）

```bash
# 全量单测（当前 71 passed）
python -m pytest tests -q

# 逐周期比对自检：故意翻转第一拍，应精确定位到 cycle=1, hiAlarm
python tests/run_tests.py --cases tests/cases/P03.csv \
  --io tests/cases/_fixtures/P03.io.json \
  --out tests/results/_selftest/P03_broken.jsonl --backend broken

# 接真实产物（需要 <run>/test/actual/*.csv）
python tests/run_tests.py --cases tests/cases/P03.csv \
  --io tests/cases/_fixtures/P03.io.json --out /tmp/P03.jsonl \
  --backend replay --actual experiments/runs/E3/P03_r1_s42/test/actual

# 从实验产物重算缺陷单（316 条，可复现）
python tests/gen/gen_defects.py --runs <实验包>/正式实验_runs --cases tests/cases
```

关键文档：`tests/report.md`（结果与对账）、`tests/defects.md`（316 条缺陷）、
`docs/判据与用例版本核对.md`（争议裁决）、`docs/interp.md`（解释器边界）。

## GenAI大作业成员1内容

- 题集：34 题（P01—P20 公共题 + S01—S14 自编题）
- 规约：34 份 LTL，177 条条款
- I/O：316 个变量；约束：144 条
- 数据文件：`data/tasks/`、`data/specs/`、`data/provenance.csv`、
  `data/diversity.md`、`data/review.md`、`data/CHANGELOG.md`、`data/sha256sums.txt`
- 工具：`tools/` 下 9 个零依赖脚本
- 原始题库：`refs/tiku_json/大作业题库json/大作业题库.json`

数据与规约自检：

```bash
python tools/ltl_check.py --quiet
python tools/schema_check.py
python tools/import_bank.py --check
```

v1.7 已按成员4 的 `tests/ambiguities.md` 修订 6 处判据，并补齐 S13、S14；
修订明细见 `docs/判据修订说明.md`，变更记录见 `data/review.md` 的 R7—R14。

## GenAI大作业成员2内容

- 自研框架入口 [`agent/run.py`](agent/run.py)，Aider 适配入口 [`baseline/run_baseline.py`](baseline/run_baseline.py)。
- [框架说明](docs/framework.md)、[环境配置](docs/codesys_setup.md)、[报告第3章](docs/report/ch3.md)和[答辩问答](docs/qa/member2.md)。
- 仓库根目录的入口使用 `data/` 下的 v1.7 题集。v1.6 题集、演示日志、编译证据、框架单测和交接材料收在 [v1.1 原始交付快照](release/member2-v1.1)。

## 目录约定（最终形态，见任务书 §7.2）

```
data/        题面 YAML、LTL 规约、来源表、多样性矩阵
tools/       题库导入、LTL/schema 校验、元数据与文档生成脚本
refs/        课程原始题库 JSON（用于重放）
agent/       自研框架：src/ 七模块、run.py、prompts/、configs/、logs/
baseline/    现成框架适配层与调用脚本
tests/       用例、逐周期执行器、缺陷单、测试报告
verify/      变异测试与 PLCVerif 结果
experiments/ 四组配置、运行记录、summary.csv
figures/     4 图 2 表（PNG + 源文件）
docs/        报告、PPT、讲稿、问答、环境说明
release/     版本快照、SHA256 校验清单与交接材料
final/       A1—A7 提交包
```

## 常见问题

1. **`pytest` 报 `ModuleNotFoundError: runner`？**
   在仓库根目录执行 `python -m pytest tests -q`。测试脚本内部已把 `tests/` 加入 `sys.path`，
   不要单独 `cd tests` 再跑。

2. **没有 `test/actual/*.csv` 怎么验证执行器？**
   用 `--backend echo`（期望值当实际值，应全 pass）或 `--backend broken`（翻第一拍，应定位到具体拍）。
   两者都只验证链路，**不是实验结果**。

3. **Windows 下 `--runner-cmd` 怎么写？**
   用 JSON 数组形式，避免路径里的反斜杠被当转义：
   `--runner-cmd '["python","tests/runner/interp/run.py","--source","{source}", ...]'`。

4. **34 题还是 32 题？**
   按成员1 v1.7 的 34 题（P01—P20 + S01—S14），主轮 34×4 = 136 跑，分母恒为 34。
   任务书排期里的 32 题/128 跑已作废。

5. **改了用例或规约之后要做什么？**
   先改 `tests/gen/gen_*.py` 里的生成器，再依次跑：本题生成器 → `gen_gap.py`（补四类缺口）→
   `python -m pytest tests -q`（K 覆盖、四类齐、字段校验会立刻报错）。不要手改 CSV。

## 许可与致谢

课程作业用途。题面来自课程公共题库与中国智能制造挑战赛赛题，改编记录见 `data/provenance.csv`；
规约与用例为小组自建，引用文献见报告。

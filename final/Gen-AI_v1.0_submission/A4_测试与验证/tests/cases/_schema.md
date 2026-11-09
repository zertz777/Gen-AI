# 用例文件规范 v1.0

## 1 文件与命名
- 一题一文件：`tests/cases/<题号>.csv`
- 一行一个扫描周期
- 一条用例 = 连续若干行，`case_id` 相同，`cycle` 从 0 递增
- 方向信息不在 CSV 里，来自 `tests/cases/_fixtures/<题号>.io.json`

## 2 列结构：5 个元数据列 + N 个输入列 + M 个输出列

| 列 | 必填 | 说明 |
| --- | --- | --- |
| `case_id` | 是 | `<题号>-<两位序号>`，如 `P03-01` |
| `cycle` | 是 | `0` = 初态行（不执行扫描）；`1..n` = 第 n 拍 |
| `spec_refs` | `cycle=0` 必填 | 分号分隔，**K 号为主、C 号为辅**：`K3;K4;C7`。其余拍可选填，表示该拍主要验证哪条；`coverage.csv` 会合并整条用例的所有行 |
| `purpose` | 仅 cycle=0 行 | 一句话说明这条用例验证什么 |
| `category` | 仅 cycle=0 行 | 四选一：`正常` / `边界` / `异常` / `安全`（任务书 T4.2 的「四类必须齐」）。缺列时 loader 不报错，但全量测试会断言必须存在 |
| `<输入列>` | 是 | 与 fixture 中 `direction=IN` 的名字**逐字一致** |
| `<输出列>` | 是 | 与 fixture 中 `direction=OUT` 的名字**逐字一致** |

### 2.1 与任务书表 6-2 的 8 字段对应关系

任务书规定用例有 8 个字段。本目录用「一题一 CSV、一行一拍」表达，**8 个字段一个不少**，只是换了存放位置：

| 任务书字段 | 本目录落在哪 |
| --- | --- |
| `case_id` | `case_id` 列 |
| `task_id` | 文件名 `P03.csv`；执行器结果 JSONL 里也带 `task_id` |
| `initial_state` | `cycle=0` 那一行（输入列 = 初态，输出列 = 初态期望） |
| `input_sequence` | `cycle>=1` 各行的输入列，一行一拍 |
| `cycles` | 该 `case_id` 的行数减 1（`cycle=0` 不计入扫描拍数） |
| `expected_output` | `cycle>=1` 各行的输出列，**逐周期**，不是只写末态 |
| `spec_refs` | `spec_refs` 列（仅 `cycle=0` 行） |
| `purpose` | `purpose` 列（仅 `cycle=0` 行） |

双向可查：`tests/coverage.csv` 给出 `K 号 → LTL 条款 → 覆盖它的 case_id`，反向从用例的 `spec_refs` 回到 K。

> `category` 是**在任务书 8 字段之外加的一列**，只为让 T4.2 的「正常/边界/异常/安全四类必须齐」能用脚本验证。它不改变 8 字段的任何语义，loader 对缺列也保持兼容。

### 2.2 结构体字段列（`xxx[].field`）

上游 `io_table` 里，结构体数组的逐元素字段单独成行，列名带 `[]`：

- P08 `channels[].enable`、`channels[].retVal`
- P07 `pumpGroup[].priority`、`pumpGroup[].RunComd`
- P17 `recipe[].recipeID`

这一列装的是**所有元素的同一个字段**，所以类型要升一维：`pumpGroup[].priority` 的类型是 `ARRAY[1..5] OF INT`，单元格写 `[1,2,3,4,5]`。容器本身（`pumpGroup`）不单列。

`INOUT` 且没有 `xxx[].field` 子列的变量（P08 `analogValues`、P18 `item`/`buffer`）按输入列处理，其输出侧不参与判定，见 `ambiguities.md` A-22。


## 3 字面量语法

| 类型 | 写法 | 例 |
| --- | --- | --- |
| BOOL | `TRUE` / `FALSE` | `TRUE` |
| INT/DINT/SINT/USINT/UINT/UDINT | 十进制 | `42` |
| WORD/DWORD | `16#` + 十六进制 | `16#8002` |
| REAL/LREAL | 十进制小数 | `12.5` |
| TIME/LTIME | `T#<n><unit>`，单位 h/m/s/ms | `T#500ms`、`T#2s` |
| STRING | 双引号 | `"10.0.0.1"` |
| ARRAY / STRUCT / VARIANT | JSON 字面量 | `[1,2,3,4,5]` |
| **不判定** | `X` | `X` |

## 4 判定规则
- `X` = 不判定，任何实际值都算通过
- REAL 相对容差 `1e-6`，LREAL `1e-12`，绝对容差兜底 `1e-6`
- TIME / LTIME 一律折算成**毫秒**再比
- 数组逐元素比，长度不等直接判错
- `X` **不允许出现在输入列**（输入必须确定）

## 5 loader 必须报错的 6 种情况
1. 列名在 fixture 里找不到（拼错、大小写不对）
2. fixture 里某个 OUT 变量没有对应列
3. 同一条 `case_id` 内 `cycle` 不连续（跳号、重号）
4. `cycle=0` 行缺 `purpose` 或 `spec_refs`
5. 字面量与声明类型不匹配（`16#8002` 出现在 BOOL 列）
6. `X` 出现在输入列

## 6 覆盖要求
- **每条 K 至少 1 条用例**，映射见 `tests/coverage.csv`（当前 143/143）
- 每题至少 1 条**安全类**用例，且**逐题四类齐**（正常/边界/异常/安全）
- 一条用例尽量覆盖多个 K（P03-01 一条打中 K3+K4 是标准做法）
- 当前 **214 条**（平均 6.3 条/题）；150 是下限。D2-5 由 `gen/gen_gap.py` 补齐 36 条缺口，改完任一题生成器后要再跑一次它
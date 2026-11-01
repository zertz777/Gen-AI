# 兜底解释器（tests/runner/interp/）

成员4 的 D3 兜底通道。目的只有一个：**变异测试需要一个"能真正跑起来、能逐拍读输出"的 ST 执行器**。
成员2 的真实执行链（CODESYS 仿真 → `test/actual/*.csv`）没到位时，用它跑自写的参考实现。

---

## 1 边界：能干什么、绝不能干什么

| 用途 | 底本 | actual 来源 | 是否合法 |
|---|---|---|---|
| 变异测试：30 个变异体的 killed / survived | `tests/refimpl/<题号>.st`（成员4 按 K 条款手写） | 本解释器 | ✅ 合法：变异测试量的是**用例强度**，与模型无关 |
| L2 全量（模型产物跑用例） | 模型生成的 `source/final.st` | **必须**成员2 的真实执行链 | ❌ 用解释器代替 = 自己出题自己判 |

`report.md` §7 已写死这条：变异的底本是参考实现、由独立解释器执行，不是模型产物。

---

## 2 支持的语法子集

| 层 | 内容 | 状态 |
|---|---|---|
| L0 | `FUNCTION_BLOCK` / `PROGRAM` / `FUNCTION`；`VAR` `VAR_INPUT` `VAR_OUTPUT` `VAR_IN_OUT` `VAR_TEMP`；`:=`；`IF/ELSIF/ELSE`、`CASE`、`FOR`、`WHILE`、`REPEAT`、`RETURN`、`EXIT`；`AND OR XOR NOT`；`= <> < > <= >=`；`+ - * / MOD`；`(*)` 与 `//` 注释；字面量 `TRUE/FALSE`、十进制、`16#`、`2#`、`8#`、实数、`T#500ms`、字符串 | ✅ 已实现并测过 |
| L1 | `TON` `TOF` `TP` `R_TRIG` `F_TRIG` `CTU` `CTD` 实例（`t(IN := x, PT := T#500ms);` + `t.Q` / `t.ET` / `t.CV`） | ✅ |
| L2 | `ARRAY[lo..hi] OF T`、`ARRAY[*] OF T`（变长，长度由输入值决定，如 P08）、`STRING(n)` / `STRING[n]`、`STRUCT`（`TYPE ... END_TYPE`）、下标、`.field`、结构体数组的 `xxx[].field` 输入输出列 | ✅ |
| — | 函数：`ABS MIN MAX LIMIT SEL MUX SQRT TRUNC SHL SHR` | ✅ |
| L3 | `VAR_EXTERNAL`、`METHOD`/`PROPERTY`/`INTERFACE`、`AT %I*` 直接地址、指针/`REF`、`VARIANT`、FB **实例数组**、`JMP/GOTO`、动态内存 | ❌ 明确报错（带行号），不静默算错 |

报错示例：`第 3 行：VAR_EXTERNAL 不在解释器支持范围内（见 docs/interp.md）`。

---

## 3 语义决策（都是会被追问的点）

| 项 | 取值 | 依据 / 影响 |
|---|---|---|
| 扫描周期 | **20 ms**，`--cycle-ms` 可改 | 全组口径 D-02；5 s 抑制 = 250 拍、30 s 延时 = 1500 拍 |
| 计时累加 | **同一拍先累加后判定**：`ET += 20` 之后才比 `ET >= PT` | D-11；滞后一拍的实现会在边界拍差 1 个周期 |
| 边沿 | `R_TRIG`/`F_TRIG` 用"上一拍 CLK"作记忆，初值 FALSE | `cycle=0` 的输入就是第 1 拍的"上一拍"基线 |
| 初态 | `cycle=0` 只写变量、不执行 FB 体；未赋值的内部变量取 IEC 零值 | `tests/cases/_schema.md` §2 |
| 输出采样 | 每拍执行完 FB 体后读 `VAR_OUTPUT`（`VAR_IN_OUT` 也读） | 与 actual 一行一拍对应 |
| 整数除法 | 向 **0** 截断（`-7/2 = -3`），不是 Python 的 `-4` | IEC 61131-3 |
| `MOD` | 符号跟被除数（`-7 MOD 2 = -1`） | 同上 |
| 结构体数组列 | 一列装所有元素的同一字段，类型**升一维**（`pumpGroup[].priority` = `ARRAY[..] OF INT`） | `_schema.md` §2.2 |
| 死循环 | 单拍 > 200 000 条语句或单循环 > 100 000 次 → 抛错 | 不能让它拖成 900 s 的 timeout，否则污染统计口径 |

---

## 4 结构

```
tests/runner/interp/
├── lexer.py      # 词法：(* *) 嵌套注释、16#、T#500ms、'...' 字符串
├── parser.py     # 语法 → AST；不支持的写法在此报错并给行号
├── st_types.py   # IEC 类型、字面量解析、actual CSV 回写（WORD 写 16#xxxx）
├── state.py      # 变量表 + 内置 FB（计时/边沿/计数）
├── eval.py       # 按拍执行：左值解析、表达式求值、控制流
└── run.py        # CLI：单用例（ExecBackend 契约）/ 整题（--cases --io --out-dir）
```

---

## 5 用法

```bash
# 单用例：契约与成员2 的 runner-cmd 完全一致，两边可互换
python tests/runner/interp/run.py --source tests/refimpl/P03.st \
  --inputs in.csv --outputs out.csv --case-id P03-01

# 整题：一次写出该题全部 actual（变异测试用）
python tests/runner/interp/run.py --source tests/refimpl/P03.st \
  --cases tests/cases/P03.csv --io tests/cases/_fixtures/P03.io.json \
  --out-dir verify/mutants/M-P03-1/test/actual
```

接进执行器（`run_tests.py --backend exec`）：

```bash
python tests/run_tests.py --cases tests/cases/P03.csv \
  --io tests/cases/_fixtures/P03.io.json --out tests/results/P03.exec.jsonl \
  --backend exec --program tests/refimpl/P03.st \
  --runner-cmd '["python","tests/runner/interp/run.py","--source","{source}","--inputs","{inputs}","--outputs","{outputs}","--case-id","{case_id}"]'
```

退出码：`0` 正常；`2` 解释/类型/输入错误（调用方判 `error`，不算模型失败）。

---

## 6 验证证据（D3 已跑）

| 项 | 结果 | 命令 |
|---|---|---|
| 解释器单测 | **15 passed**（含 P03 参考实现 6 条用例逐拍全 pass、TON 第 25 拍动作、R_TRIG 边沿、结构体数组列、变长数组、整数截断、死循环兜底、CLI 契约） | `python -m pytest tests/test_interp.py -q` |
| 全量单测 | **71 passed**（原有 56 条 + 新增 15 条，未破坏任何旧测试） | `python -m pytest tests -q` |
| 真实语料兼容性 | 成员2 那 34 份模型产出的骨架里，**33 份能解析并跑一拍**；只有 P18（`VARIANT`）按 L3 明确报不支持 | 遍历 `full34_fixture/*/final.st` |
| 接真实执行器 | P03 参考实现 **pass=6 fail=0 timeout=0 error=0** | `run_tests.py --backend exec`（见上） |
| 变异体能杀死 | `M-P03-1`（`Value > hiLevel` 反相）→ **pass=2 fail=4**，首失配 `cycle=1, hiAlarm` | 同上，把参考实现打补丁后重跑 |

---

## 7 已知局限（写进报告 §7）

1. **不是独立参考实现**：解释器的语义是照 IEC 与 D-02/D-11 实现的，与 CODESYS 可能存在实现差异；
   等成员2 的仿真通了之后，抽 3 题做**逐拍交叉校验**（diff 为空才算过），不一致的进 `ambiguities.md`。
2. **只覆盖题目用到的子集**：L3 列出的语法一律不支持，遇到就报错——这是刻意的，静默算错比报错危险得多。
3. **REAL 用 Python 双精度**：与 PLC 的单精度 REAL 在边界值上可能差 1 ulp；
   用例的 REAL 容差是 `1e-6`，正常情况下不影响判定，但极端边界要人工复核。
4. **性能**：纯 Python 解释，一条 1500 拍的用例约几十毫秒；30 个变异体 × 6 条用例完全可接受。
5. **参考实现只写了 P03**：P05 / S01 / S10 / S12 / P07 需要在 D3 上午按 K 条款补齐（每题约 30 分钟）。

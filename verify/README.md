# verify/ —— 变异测试（D4.5 的真实样例）

任务书要求 30 个变异体（6 题 × 5 算子）。受执行环境限制（CODESYS + matiec 都在实验机），
这里交付的是**可完整复算的真实样例**：1 题 × 5 算子，底本是真实模型产物，执行通道是本仓库的 ST 解释器。

比起"30 个数字但无法复现"，这一份的价值在于：**每一步都能在本机重跑，且过程发现了用例本身的真实缺口。**

---

## 1 底本与执行通道

| 项 | 内容 |
| --- | --- |
| 底本 | `03_程序案例/E1_S10_1_42/final.st`（Aider + deepseek-v4.1-flash，官方判定 **6/6 通过**） |
| 题目 | S10 变频器故障码分级报警（K1 重故障当拍跳闸、K2 锁存、K3 复位上升沿、K4 运行中非零即跳） |
| 执行 | `tests/runner/interp` 的 ST 解释器，20 ms 扫描周期，逐拍比对 |
| 为什么可以用解释器 | 已对 4 份真实产物做过交叉验证，**4/4 一致，且通过用例集合与官方 evaluation 完全相同**（见 `tests/report.md` §3.2） |

## 2 五个变异体与结果

| ID | 算子 | 改动 | 冻结 6 条用例 | 补 2 条后 | 杀手用例 |
| --- | --- | --- | --- | --- | --- |
| M-S10-1 | 条件取反 | `IsHeavyFault` 整体取 `NOT` | killed | killed | S10-01 @1 |
| M-S10-2 | 边界偏移 | 重故障阈值 `16#0003` → `16#0004` | **survived** | killed | S10-07 @1 |
| M-S10-3 | 运算符替换 | 复位上升沿 → 电平触发 | **survived** | killed | S10-08 @4 |
| M-S10-4 | 常量替换 | 锁存码 `LatchedCode := VFDFaultCode` → `16#0001` | killed | killed | S10-02 @1 |
| M-S10-5 | 语句删除 | 删除复位分支的 `LatchedTrip := FALSE` | killed | killed | S10-03 @4 |

- **冻结用例得分 3/5**（`mutants/summary.csv`）；
- **补充 2 条用例后 5/5**（`mutants_augmented/summary.csv`）。

底本在两种用例集下都先做了自检（6/6、8/8 全通过），底本不通过时脚本直接退出、不出分。

## 3 两个存活变异体暴露的用例缺口

### 缺口 1：重故障只测了"运行中"

`M-S10-2` 把 `16#0003` 的重故障分支废掉后仍然全过，原因不是用例写错，而是**覆盖不全**：
6 条用例里 `VFDRun` 恒为 TRUE，`TripCondition` 的第二条分支（K4：运行中非零即跳）会把结果救回来，
K1（重故障当拍跳闸，与是否运行无关）这条独立路径从没被单独验证。

补 `S10-07`：`VFDRun=FALSE` + `code=16#0003`，期望当拍 `TripOutput=TRUE`。

### 缺口 2：复位"电平 vs 上升沿"没被测到

`M-S10-3` 把上升沿改成电平后全过：原用例在"复位按住时出现新故障"（S10-06）之后就停了，
两种实现到那一步的表现相同。差异只在**再下一拍**：故障码回到 0、复位仍按着时，
边沿实现应保持跳闸、电平实现会误清。

补 `S10-08`（5 拍）：新增第 4 拍 `code=0 + ResetBtn 仍为 TRUE`，期望 `TripOutput` 保持 TRUE。

两条补充用例在 `mutants/S10_extra_cases.csv`，**没有并入冻结用例集**——官方 136 跑用的是 6 条版，
现在改会让 `test_total` 对不上。是否并入由成员3/5 决定，建议随下一版一起改并记 CHANGELOG。

## 4 目录

```
verify/
├── run_mutants.py                  # 执行器：打补丁 → 跑全用例 → 出 killed/survived
├── README.md                       # 本文件
├── mutants/                        # 冻结 6 条用例下的结果（3/5）
│   ├── summary.csv
│   ├── S10_extra_cases.csv         # 补充用例（验证覆盖缺口）
│   └── M-S10-1…5/                  # 每个变异体：final.st、mutation.json、cases_result.jsonl、result.json
└── mutants_augmented/              # 冻结 + 补充用例下的结果（5/5）
    ├── summary.csv
    ├── merged_S10.csv
    └── M-S10-1…5/
```

## 5 复现

```bash
cd 组员4

# 冻结用例（3/5）
python verify/run_mutants.py --task S10 --out verify/mutants

# 冻结 + 补充用例（5/5）
python verify/run_mutants.py --task S10 \
  --extra verify/mutants/S10_extra_cases.csv --out verify/mutants_augmented
```

输出里 `killed_by=<case_id>@<拍号>` 就是首个失配位置，可直接对照 `cases_result.jsonl`。

## 6 局限（如实写）

1. **只做了 1 题 5 个变异体**，不是任务书的 6 题 30 个；其余 25 个的选样与预期杀手仍见 `tests/plan_d3.md`，可直接照做。
2. **执行通道是解释器**，不是 CODESYS。解释器的语义已按 IEC 与 D-02/D-11 实现并通过交叉验证，
   但与真实 PLC 运行时仍有实现差异；如需"双通道一致"的更强证据，应在实验机上复算这 5 个变异体。
3. **底本是单份真实产物**，不代表该题所有实现的变异得分；换底本要重跑并记录。

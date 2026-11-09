# 缺陷单（defects）

成员4 的 D4.4 交付物。**一条失败 = 一条缺陷**，不多不少；回归结果单独一节，不混进第一轮。

本文件由 `tests/gen/gen_defects.py` 从实验批次的 `evaluation.json` 自动生成，
可随时重算：`python tests/gen/gen_defects.py --runs <实验目录> --cases tests/cases --out tests/defects.md`。

## 0 当前状态

| 项 | 值 |
| --- | --- |
| 数据来源 | `组员3_正式实验提交包_精简版_v1.1/正式实验_runs`（相对实验包根目录） |
| 有 evaluation.json 的 run | **132**（逐题逐组表 136 条，缺的 4 条是 `abandoned:timeout`，未进测试阶段） |
| 真实缺陷条数 | **316**（= 全部 run 的失配条目之和） |
| 涉及 run 数 | 75 |
| 与成员3 `逐题逐组结果.csv` 逐 run 对账 | 一致 **132** 条，不一致 **0** 条 |
| 争议用例条目 | 33 条（见 §5，来自 `docs/判据与用例版本核对.md`） |

## 1 字段（缺一列成员2 就没法修）

| 字段 | 说明 |
| --- | --- |
| `defect_id` | `DEF-` + 三位序号 |
| `task_id` | P01—P20 / S01—S14 |
| `run_id` | 组别_题号_r次_s种子，如 `E3_P03_1_42` |
| `case_id` / `cycle` | 失配的用例与拍号（逐周期比对得出，不是只看末态） |
| `variable` | 首个失配变量 |
| `expected` / `actual` | 期望值 / 实际值（按声明类型写） |
| `kind` | 逻辑 / 时序 / 边界 / 编译 / 工具超时（判定规则见脚本注释） |
| `repro` | 复跑命令（见 §4；actual 未随包交付，需在实验机复跑） |
| `status` | 待修 / 已修待回归 / 已关闭 / 不修（附理由） |

## 2 分布

### 2.1 按组

| 组别 | 缺陷条数 | 涉及 run |
| --- | ---: | ---: |
| E1 | 42 | 13 |
| E2 | 56 | 16 |
| E3 | 103 | 20 |
| E4 | 115 | 26 |

### 2.2 按原因

| kind | 条数 | 占比 |
| --- | ---: | ---: |
| 逻辑 | 182 | 57.6% |
| 时序 | 64 | 20.3% |
| 边界 | 61 | 19.3% |
| 工具超时 | 9 | 2.8% |

### 2.3 按题（失败最多的 12 题）

| 题号 | 条数 |
| --- | ---: |
| P20 | 25 |
| S02 | 19 |
| P15 | 18 |
| S07 | 17 |
| S11 | 17 |
| P19 | 16 |
| S04 | 16 |
| P17 | 16 |
| P10 | 15 |
| S12 | 15 |
| P16 | 13 |
| P04 | 12 |

## 3 缺陷明细（316 条）

| defect_id | task_id | run_id | case_id | cycle | variable | expected | actual | kind | repro | status |
| --- | --- | --- | --- | ---: | --- | --- | --- | --- | --- | --- |
| DEF-001 | P11 | E1_P11_1_42 | P11-04 | 2 | MotorForward | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E1_P11_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-002 | P11 | E1_P11_1_42 | P11-07 | 1 | MotorForward | FALSE | TRUE | 边界 | `python agent/scripts/member4_test.py --source E1_P11_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-003 | P15 | E1_P15_1_42 | P15-05 | 4 | valveARun | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E1_P15_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-004 | P15 | E1_P15_1_42 | P15-07 | 1 | valveARun | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E1_P15_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-005 | P16 | E1_P16_1_42 | P16-06 | 1 | conveyorRight | FALSE | TRUE | 逻辑 | `python agent/scripts/member4_test.py --source E1_P16_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-006 | P16 | E1_P16_1_42 | P16-07 | 2 | conveyorRight | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E1_P16_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-007 | P16 | E1_P16_1_42 | P16-08 | 1 | conveyorRight | TRUE | FALSE | 边界 | `python agent/scripts/member4_test.py --source E1_P16_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-008 | P19 | E1_P19_1_42 | P19-02 | 8 | MoveUp | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E1_P19_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-009 | P19 | E1_P19_1_42 | P19-03 | 6 | MoveUp | TRUE | FALSE | 时序 | `python agent/scripts/member4_test.py --source E1_P19_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-010 | P19 | E1_P19_1_42 | P19-04 | 6 | MoveUp | TRUE | FALSE | 时序 | `python agent/scripts/member4_test.py --source E1_P19_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-011 | P19 | E1_P19_1_42 | P19-08 | 1 | MoveDown | FALSE | TRUE | 时序 | `python agent/scripts/member4_test.py --source E1_P19_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-012 | P19 | E1_P19_1_42 | P19-09 | 1 | MoveDown | TRUE | FALSE | 边界 | `python agent/scripts/member4_test.py --source E1_P19_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-013 | P20 | E1_P20_1_42 | P20-08 | 1 | kick | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E1_P20_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-014 | S01 | E1_S01_1_42 | S01-05 | 2 | Status | 33025 | 0 | 逻辑 | `python agent/scripts/member4_test.py --source E1_S01_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-015 | S02 | E1_S02_1_42 | S02-01 | 3 | RunLamp | FALSE | TRUE | 逻辑 | `python agent/scripts/member4_test.py --source E1_S02_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-016 | S02 | E1_S02_1_42 | S02-02 | 2 | MotorRev | FALSE | TRUE | 时序 | `python agent/scripts/member4_test.py --source E1_S02_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-017 | S02 | E1_S02_1_42 | S02-04 | 3 | MotorFwd | FALSE | TRUE | 时序 | `python agent/scripts/member4_test.py --source E1_S02_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-018 | S02 | E1_S02_1_42 | S02-05 | 1 | RunLamp | FALSE | TRUE | 逻辑 | `python agent/scripts/member4_test.py --source E1_S02_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-019 | S02 | E1_S02_1_42 | S02-06 | 1 | RunLamp | TRUE | FALSE | 边界 | `python agent/scripts/member4_test.py --source E1_S02_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-020 | S03 | E1_S03_1_42 | S03-01 | 2 | DriveB_Run | TRUE | FALSE | 时序 | `python agent/scripts/member4_test.py --source E1_S03_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-021 | S03 | E1_S03_1_42 | S03-02 | 2 | DriveB_Run | TRUE | FALSE | 边界 | `python agent/scripts/member4_test.py --source E1_S03_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-022 | S03 | E1_S03_1_42 | S03-03 | 2 | DriveB_Run | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E1_S03_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-023 | S03 | E1_S03_1_42 | S03-04 | 2 | DriveB_Run | TRUE | FALSE | 时序 | `python agent/scripts/member4_test.py --source E1_S03_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-024 | S04 | E1_S04_1_42 | S04-01 | 3 | DriftAlarm | FALSE | TRUE | 时序 | `python agent/scripts/member4_test.py --source E1_S04_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-025 | S04 | E1_S04_1_42 | S04-02 | 3 | DriftAlarm | FALSE | TRUE | 时序 | `python agent/scripts/member4_test.py --source E1_S04_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-026 | S04 | E1_S04_1_42 | S04-03 | 3 | DriftAlarm | FALSE | TRUE | 逻辑 | `python agent/scripts/member4_test.py --source E1_S04_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-027 | S04 | E1_S04_1_42 | S04-04 | 1 | DriftAlarm | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E1_S04_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-028 | S04 | E1_S04_1_42 | S04-05 | 2 | DriftAlarm | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E1_S04_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-029 | S04 | E1_S04_1_42 | S04-06 | 2 | DriftAlarm | TRUE | FALSE | 边界 | `python agent/scripts/member4_test.py --source E1_S04_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-030 | S05 | E1_S05_1_42 | S05-06 | 2 | TotalVolume | 1.0 | 0.5 | 边界 | `python agent/scripts/member4_test.py --source E1_S05_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-031 | S07 | E1_S07_1_42 | S07-01 | 2 | Conveyor | FALSE | TRUE | 逻辑 | `python agent/scripts/member4_test.py --source E1_S07_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-032 | S07 | E1_S07_1_42 | S07-02 | 2 | Conveyor | FALSE | TRUE | 逻辑 | `python agent/scripts/member4_test.py --source E1_S07_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-033 | S07 | E1_S07_1_42 | S07-03 | 2 | Conveyor | FALSE | TRUE | 逻辑 | `python agent/scripts/member4_test.py --source E1_S07_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-034 | S07 | E1_S07_1_42 | S07-04 | 2 | Conveyor | FALSE | TRUE | 逻辑 | `python agent/scripts/member4_test.py --source E1_S07_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-035 | S07 | E1_S07_1_42 | S07-05 | 1 | Conveyor | FALSE | TRUE | 逻辑 | `python agent/scripts/member4_test.py --source E1_S07_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-036 | S07 | E1_S07_1_42 | S07-06 | 2 | Conveyor | FALSE | TRUE | 边界 | `python agent/scripts/member4_test.py --source E1_S07_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-037 | S11 | E1_S11_1_42 | S11-02 | 2 | ControlValue | 0.0 | 50.0 | 时序 | `python agent/scripts/member4_test.py --source E1_S11_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-038 | S11 | E1_S11_1_42 | S11-03 | 2 | ControlValue | 0.0 | 50.0 | 时序 | `python agent/scripts/member4_test.py --source E1_S11_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-039 | S11 | E1_S11_1_42 | S11-04 | 25 | AlarmLamp | TRUE | FALSE | 时序 | `python agent/scripts/member4_test.py --source E1_S11_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-040 | S11 | E1_S11_1_42 | S11-05 | 2 | Status | 0 | 35329 | 边界 | `python agent/scripts/member4_test.py --source E1_S11_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-041 | S14 | E1_S14_1_42 | S14-01 | 3 | LowPump | FALSE | TRUE | 时序 | `python agent/scripts/member4_test.py --source E1_S14_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-042 | S14 | E1_S14_1_42 | S14-06 | 1 | LowPump | TRUE | FALSE | 边界 | `python agent/scripts/member4_test.py --source E1_S14_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-043 | P04 | E2_P04_1_42 | P04-02 | 5 | VFD_RUN | FALSE | TRUE | 时序 | `python agent/scripts/member4_test.py --source E2_P04_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-044 | P04 | E2_P04_1_42 | P04-04 | 1 | VFD_RUN | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E2_P04_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-045 | P04 | E2_P04_1_42 | P04-05 | 1 | VFD_RUN | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E2_P04_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-046 | P04 | E2_P04_1_42 | P04-07 | 1 | VFD_RUN | TRUE | FALSE | 边界 | `python agent/scripts/member4_test.py --source E2_P04_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-047 | P10 | E2_P10_1_42 | P10-01 | 1 | HeaterStatus | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E2_P10_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-048 | P10 | E2_P10_1_42 | P10-02 | 1 | HeaterStatus | TRUE | FALSE | 时序 | `python agent/scripts/member4_test.py --source E2_P10_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-049 | P10 | E2_P10_1_42 | P10-03 | 1 | HeaterStatus | TRUE | FALSE | 时序 | `python agent/scripts/member4_test.py --source E2_P10_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-050 | P10 | E2_P10_1_42 | P10-04 | 1 | HeaterStatus | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E2_P10_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-051 | P10 | E2_P10_1_42 | P10-05 | 1 | HeaterStatus | TRUE | FALSE | 边界 | `python agent/scripts/member4_test.py --source E2_P10_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-052 | P11 | E2_P11_1_42 | P11-04 | 2 | MotorForward | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E2_P11_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-053 | P15 | E2_P15_1_42 | P15-05 | 4 | valveARun | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E2_P15_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-054 | P15 | E2_P15_1_42 | P15-07 | 1 | valveARun | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E2_P15_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-055 | P16 | E2_P16_1_42 | P16-01 | 1 | conveyorRight | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E2_P16_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-056 | P16 | E2_P16_1_42 | P16-02 | 1 | conveyorRight | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E2_P16_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-057 | P16 | E2_P16_1_42 | P16-04 | 1 | conveyorRight | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E2_P16_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-058 | P16 | E2_P16_1_42 | P16-07 | 2 | conveyorRight | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E2_P16_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-059 | P16 | E2_P16_1_42 | P16-08 | 1 | conveyorRight | TRUE | FALSE | 边界 | `python agent/scripts/member4_test.py --source E2_P16_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-060 | P19 | E2_P19_1_42 | P19-02 | 8 | MoveUp | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E2_P19_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-061 | P19 | E2_P19_1_42 | P19-03 | 6 | MoveUp | TRUE | FALSE | 时序 | `python agent/scripts/member4_test.py --source E2_P19_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-062 | P19 | E2_P19_1_42 | P19-04 | 6 | MoveUp | TRUE | FALSE | 时序 | `python agent/scripts/member4_test.py --source E2_P19_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-063 | P19 | E2_P19_1_42 | P19-08 | 1 | MoveDown | FALSE | TRUE | 时序 | `python agent/scripts/member4_test.py --source E2_P19_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-064 | P19 | E2_P19_1_42 | P19-09 | 1 | MoveDown | TRUE | FALSE | 边界 | `python agent/scripts/member4_test.py --source E2_P19_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-065 | P20 | E2_P20_1_42 | P20-01 | 1 | MotorForward | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E2_P20_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-066 | P20 | E2_P20_1_42 | P20-02 | 1 | MotorForward | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E2_P20_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-067 | P20 | E2_P20_1_42 | P20-03 | 1 | MotorForward | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E2_P20_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-068 | P20 | E2_P20_1_42 | P20-04 | 1 | MotorForward | TRUE | FALSE | 边界 | `python agent/scripts/member4_test.py --source E2_P20_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-069 | P20 | E2_P20_1_42 | P20-05 | 1 | MotorForward | TRUE | FALSE | 边界 | `python agent/scripts/member4_test.py --source E2_P20_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-070 | P20 | E2_P20_1_42 | P20-06 | 1 | MotorForward | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E2_P20_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-071 | P20 | E2_P20_1_42 | P20-07 | 1 | MotorForward | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E2_P20_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-072 | P20 | E2_P20_1_42 | P20-08 | 1 | kick | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E2_P20_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-073 | S02 | E2_S02_1_42 | S02-01 | 1 | MotorFwd | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E2_S02_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-074 | S02 | E2_S02_1_42 | S02-02 | 1 | MotorFwd | TRUE | FALSE | 时序 | `python agent/scripts/member4_test.py --source E2_S02_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-075 | S02 | E2_S02_1_42 | S02-04 | 1 | MotorFwd | TRUE | FALSE | 时序 | `python agent/scripts/member4_test.py --source E2_S02_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-076 | S02 | E2_S02_1_42 | S02-06 | 1 | MotorFwd | TRUE | FALSE | 边界 | `python agent/scripts/member4_test.py --source E2_S02_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-077 | S03 | E2_S03_1_42 | S03-03 | 3 | DriveB_Run | FALSE | TRUE | 逻辑 | `python agent/scripts/member4_test.py --source E2_S03_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-078 | S04 | E2_S04_1_42 | S04-01 | 1 | DriftAlarm | FALSE | TRUE | 时序 | `python agent/scripts/member4_test.py --source E2_S04_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-079 | S04 | E2_S04_1_42 | S04-03 | 2 | DriftAlarm | FALSE | TRUE | 逻辑 | `python agent/scripts/member4_test.py --source E2_S04_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-080 | S04 | E2_S04_1_42 | S04-06 | 3 | DriftAlarm | TRUE | FALSE | 边界 | `python agent/scripts/member4_test.py --source E2_S04_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-081 | S05 | E2_S05_1_42 | S05-06 | 2 | TotalVolume | 1.0 | 0.5 | 边界 | `python agent/scripts/member4_test.py --source E2_S05_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-082 | S07 | E2_S07_1_42 | S07-02 | 251 | FillValve | FALSE | TRUE | 逻辑 | `python agent/scripts/member4_test.py --source E2_S07_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-083 | S07 | E2_S07_1_42 | S07-04 | 3 | FillValve | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E2_S07_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-084 | S07 | E2_S07_1_42 | S07-05 | 1 | Conveyor | FALSE | TRUE | 逻辑 | `python agent/scripts/member4_test.py --source E2_S07_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-085 | S11 | E2_S11_1_42 | S11-02 | 2 | ControlValue | 0.0 | 50.0 | 时序 | `python agent/scripts/member4_test.py --source E2_S11_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-086 | S11 | E2_S11_1_42 | S11-03 | 2 | ControlValue | 0.0 | 50.0 | 时序 | `python agent/scripts/member4_test.py --source E2_S11_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-087 | S11 | E2_S11_1_42 | S11-05 | 1 | SensorValid | TRUE | FALSE | 边界 | `python agent/scripts/member4_test.py --source E2_S11_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-088 | S12 | E2_S12_1_42 | S12-01 | 1 | MachineRun | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E2_S12_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-089 | S12 | E2_S12_1_42 | S12-02 | 1 | MachineRun | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E2_S12_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-090 | S12 | E2_S12_1_42 | S12-03 | 1 | MachineRun | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E2_S12_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-091 | S12 | E2_S12_1_42 | S12-04 | 1 | MachineRun | TRUE | FALSE | 时序 | `python agent/scripts/member4_test.py --source E2_S12_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-092 | S12 | E2_S12_1_42 | S12-05 | 1 | MachineRun | TRUE | FALSE | 边界 | `python agent/scripts/member4_test.py --source E2_S12_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-093 | S13 | E2_S13_1_42 | S13-03 | 101 | MainMotor | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E2_S13_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-094 | S13 | E2_S13_1_42 | S13-04 | 101 | MainMotor | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E2_S13_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-095 | S13 | E2_S13_1_42 | S13-05 | 151 | SpeedHigh | FALSE | TRUE | 时序 | `python agent/scripts/member4_test.py --source E2_S13_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-096 | S14 | E2_S14_1_42 | S14-03 | 2 | LowPump | FALSE | TRUE | 逻辑 | `python agent/scripts/member4_test.py --source E2_S14_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-097 | S14 | E2_S14_1_42 | S14-05 | 1 | ReliefValve | FALSE | TRUE | 逻辑 | `python agent/scripts/member4_test.py --source E2_S14_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-098 | S14 | E2_S14_1_42 | S14-06 | 1 | LowPump | TRUE | FALSE | 边界 | `python agent/scripts/member4_test.py --source E2_S14_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-099 | P04 | E3_P04_1_42 | P04-01 | 3 | VFD_RUN | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E3_P04_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-100 | P04 | E3_P04_1_42 | P04-02 | 3 | VFD_RUN | TRUE | FALSE | 时序 | `python agent/scripts/member4_test.py --source E3_P04_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-101 | P04 | E3_P04_1_42 | P04-04 | 1 | VFD_RUN | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E3_P04_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-102 | P04 | E3_P04_1_42 | P04-05 | 1 | VFD_RUN | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E3_P04_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-103 | P04 | E3_P04_1_42 | P04-07 | 1 | VFD_RUN | TRUE | FALSE | 边界 | `python agent/scripts/member4_test.py --source E3_P04_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-104 | P07 | E3_P07_1_42 | P07-01 | 2 | pumpGroup[].RunComd | [True, False, True, False, False] | [True, False, False, False, False] | 逻辑 | `python agent/scripts/member4_test.py --source E3_P07_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-105 | P07 | E3_P07_1_42 | P07-03 | 1 | pumpGroup[].RunComd | [True, True, True, False, False] | [False, False, False, False, False] | 边界 | `python agent/scripts/member4_test.py --source E3_P07_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-106 | P07 | E3_P07_1_42 | P07-04 | 1 | pumpGroup[].RunComd | [True, False, False, False, False] | [False, False, False, False, False] | 逻辑 | `python agent/scripts/member4_test.py --source E3_P07_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-107 | P07 | E3_P07_1_42 | P07-05 | 1 | pumpGroup[].RunComd | [True, False, False, False, False] | [False, False, False, False, False] | 逻辑 | `python agent/scripts/member4_test.py --source E3_P07_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-108 | P07 | E3_P07_1_42 | P07-06 | 1 | pumpGroup[].RunComd | [False, True, False, True, True] | [False, False, False, False, False] | 边界 | `python agent/scripts/member4_test.py --source E3_P07_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-109 | P07 | E3_P07_1_42 | P07-07 | 1 | pumpGroup[].RunComd | [False, False, True, True, True] | [False, False, False, False, False] | 逻辑 | `python agent/scripts/member4_test.py --source E3_P07_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-110 | P10 | E3_P10_1_42 | P10-01 | 1 | HeaterStatus | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E3_P10_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-111 | P10 | E3_P10_1_42 | P10-02 | 1 | HeaterStatus | TRUE | FALSE | 时序 | `python agent/scripts/member4_test.py --source E3_P10_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-112 | P10 | E3_P10_1_42 | P10-03 | 1 | HeaterStatus | TRUE | FALSE | 时序 | `python agent/scripts/member4_test.py --source E3_P10_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-113 | P10 | E3_P10_1_42 | P10-04 | 1 | HeaterStatus | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E3_P10_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-114 | P10 | E3_P10_1_42 | P10-05 | 1 | HeaterStatus | TRUE | FALSE | 边界 | `python agent/scripts/member4_test.py --source E3_P10_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-115 | P12 | E3_P12_1_42 | P12-01 | 1 | THICKNESS_ALARM | TRUE | FALSE | 时序 | `python agent/scripts/member4_test.py --source E3_P12_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-116 | P12 | E3_P12_1_42 | P12-02 | 1 | Slab_Fault_Counter | 1 | 0 | 逻辑 | `python agent/scripts/member4_test.py --source E3_P12_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-117 | P12 | E3_P12_1_42 | P12-04 | 1 | Slab_Runtime_Accumulator | 1000.0 | 0.0 | 逻辑 | `python agent/scripts/member4_test.py --source E3_P12_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-118 | P12 | E3_P12_1_42 | P12-05 | 1 | THICKNESS_ALARM | TRUE | FALSE | 时序 | `python agent/scripts/member4_test.py --source E3_P12_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-119 | P12 | E3_P12_1_42 | P12-06 | 1 | THICKNESS_ALARM | TRUE | FALSE | 边界 | `python agent/scripts/member4_test.py --source E3_P12_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-120 | P13 | E3_P13_1_42 | P13-03 | 1 | TEMP_SETPOINT_ADJUST | 4 | 0 | 时序 | `python agent/scripts/member4_test.py --source E3_P13_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-121 | P13 | E3_P13_1_42 | P13-05 | 1 | TEMP_SETPOINT_ADJUST | 3 | 0 | 时序 | `python agent/scripts/member4_test.py --source E3_P13_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-122 | P15 | E3_P15_1_42 | P15-01 | 1 | valveARun | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E3_P15_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-123 | P15 | E3_P15_1_42 | P15-02 | 1 | valveARun | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E3_P15_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-124 | P15 | E3_P15_1_42 | P15-03 | 1 | valveARun | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E3_P15_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-125 | P15 | E3_P15_1_42 | P15-04 | 1 | valveARun | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E3_P15_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-126 | P15 | E3_P15_1_42 | P15-05 | 1 | valveARun | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E3_P15_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-127 | P15 | E3_P15_1_42 | P15-06 | 1 | valveARun | TRUE | FALSE | 边界 | `python agent/scripts/member4_test.py --source E3_P15_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-128 | P15 | E3_P15_1_42 | P15-07 | 1 | valveARun | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E3_P15_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-129 | P17 | E3_P17_1_42 | P17-01 | 1 | recipeQueryResult | {'recipeID': 1, 'ingredientType': 10, 'ingredientRatio': 0.5, 'productionTemperature': 100.0} | {'ingredientRatio': 0.0, 'ingredientType': 0, 'productionTemperature': 0.0, 'recipeID': 0} | 逻辑 | `python agent/scripts/member4_test.py --source E3_P17_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-130 | P17 | E3_P17_1_42 | P17-02 | 1 | error | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E3_P17_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-131 | P17 | E3_P17_1_42 | P17-03 | 1 | recipeAdded | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E3_P17_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-132 | P17 | E3_P17_1_42 | P17-04 | 1 | error | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E3_P17_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-133 | P17 | E3_P17_1_42 | P17-05 | 1 | error | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E3_P17_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-134 | P17 | E3_P17_1_42 | P17-06 | 1 | error | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E3_P17_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-135 | P17 | E3_P17_1_42 | P17-07 | 1 | recipeAdded | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E3_P17_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-136 | P17 | E3_P17_1_42 | P17-08 | 1 | recipeAdded | TRUE | FALSE | 边界 | `python agent/scripts/member4_test.py --source E3_P17_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-137 | P20 | E3_P20_1_42 | P20-01 | 1 | MotorForward | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E3_P20_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-138 | P20 | E3_P20_1_42 | P20-02 | 1 | MotorForward | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E3_P20_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-139 | P20 | E3_P20_1_42 | P20-03 | 1 | MotorForward | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E3_P20_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-140 | P20 | E3_P20_1_42 | P20-04 | 1 | MotorForward | TRUE | FALSE | 边界 | `python agent/scripts/member4_test.py --source E3_P20_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-141 | P20 | E3_P20_1_42 | P20-05 | 1 | MotorForward | TRUE | FALSE | 边界 | `python agent/scripts/member4_test.py --source E3_P20_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-142 | P20 | E3_P20_1_42 | P20-06 | 1 | MotorForward | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E3_P20_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-143 | P20 | E3_P20_1_42 | P20-07 | 1 | MotorForward | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E3_P20_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-144 | P20 | E3_P20_1_42 | P20-08 | 1 | kick | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E3_P20_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-145 | S01 | E3_S01_1_42 | S01-01 | 1 | ClampLeft | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E3_S01_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-146 | S01 | E3_S01_1_42 | S01-02 | 1 | ClampRight | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E3_S01_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-147 | S01 | E3_S01_1_42 | S01-04 | 1 | ClampLeft | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E3_S01_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-148 | S01 | E3_S01_1_42 | S01-05 | 1 | Status | 33025 | 0 | 逻辑 | `python agent/scripts/member4_test.py --source E3_S01_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-149 | S02 | E3_S02_1_42 | S02-01 | 1 | MotorFwd | TRUE | FALSE | 工具超时 | `python agent/scripts/member4_test.py --source E3_S02_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-150 | S02 | E3_S02_1_42 | S02-02 | 1 | MotorFwd | TRUE | FALSE | 工具超时 | `python agent/scripts/member4_test.py --source E3_S02_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-151 | S02 | E3_S02_1_42 | S02-03 | 1 | RunLamp | TRUE | FALSE | 工具超时 | `python agent/scripts/member4_test.py --source E3_S02_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-152 | S02 | E3_S02_1_42 | S02-04 | 1 | MotorFwd | TRUE | FALSE | 工具超时 | `python agent/scripts/member4_test.py --source E3_S02_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-153 | S02 | E3_S02_1_42 | S02-05 | 2 | MotorFwd | FALSE | TRUE | 工具超时 | `python agent/scripts/member4_test.py --source E3_S02_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-154 | S02 | E3_S02_1_42 | S02-06 | 1 | MotorFwd | TRUE | FALSE | 工具超时 | `python agent/scripts/member4_test.py --source E3_S02_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-155 | S04 | E3_S04_1_42 | S04-01 | 1 | DriftAlarm | FALSE | TRUE | 时序 | `python agent/scripts/member4_test.py --source E3_S04_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-156 | S04 | E3_S04_1_42 | S04-02 | 2 | DriftAlarm | FALSE | TRUE | 时序 | `python agent/scripts/member4_test.py --source E3_S04_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-157 | S04 | E3_S04_1_42 | S04-03 | 2 | DriftAlarm | FALSE | TRUE | 逻辑 | `python agent/scripts/member4_test.py --source E3_S04_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-158 | S04 | E3_S04_1_42 | S04-06 | 1 | DriftAlarm | FALSE | TRUE | 边界 | `python agent/scripts/member4_test.py --source E3_S04_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-159 | S05 | E3_S05_1_42 | S05-01 | 1 | TotalVolume | 0.5 | 0.0 | 逻辑 | `python agent/scripts/member4_test.py --source E3_S05_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-160 | S05 | E3_S05_1_42 | S05-02 | 1 | TotalVolume | 0.5 | 0.0 | 逻辑 | `python agent/scripts/member4_test.py --source E3_S05_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-161 | S05 | E3_S05_1_42 | S05-04 | 1 | TotalVolume | 0.5 | 0.0 | 逻辑 | `python agent/scripts/member4_test.py --source E3_S05_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-162 | S05 | E3_S05_1_42 | S05-05 | 1 | TotalVolume | 0.5 | 0.0 | 逻辑 | `python agent/scripts/member4_test.py --source E3_S05_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-163 | S05 | E3_S05_1_42 | S05-06 | 1 | TotalVolume | 0.5 | 0.0 | 边界 | `python agent/scripts/member4_test.py --source E3_S05_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-164 | S06 | E3_S06_1_42 | S06-01 | 1 | HeatOn | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E3_S06_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-165 | S06 | E3_S06_1_42 | S06-02 | 1 | HeatOn | TRUE | FALSE | 边界 | `python agent/scripts/member4_test.py --source E3_S06_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-166 | S06 | E3_S06_1_42 | S06-03 | 1 | HeatOn | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E3_S06_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-167 | S06 | E3_S06_1_42 | S06-04 | 1 | OverTempAlarm | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E3_S06_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-168 | S06 | E3_S06_1_42 | S06-05 | 1 | LoadReduce | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E3_S06_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-169 | S07 | E3_S07_1_42 | S07-01 | 1 | Conveyor | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E3_S07_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-170 | S07 | E3_S07_1_42 | S07-02 | 1 | Conveyor | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E3_S07_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-171 | S07 | E3_S07_1_42 | S07-03 | 1 | Conveyor | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E3_S07_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-172 | S07 | E3_S07_1_42 | S07-04 | 1 | Conveyor | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E3_S07_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-173 | S07 | E3_S07_1_42 | S07-06 | 1 | Conveyor | TRUE | FALSE | 边界 | `python agent/scripts/member4_test.py --source E3_S07_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-174 | S08 | E3_S08_1_42 | S08-01 | 1 | SortLeft | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E3_S08_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-175 | S08 | E3_S08_1_42 | S08-02 | 1 | Busy | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E3_S08_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-176 | S08 | E3_S08_1_42 | S08-03 | 1 | Status | 34817 | 0 | 逻辑 | `python agent/scripts/member4_test.py --source E3_S08_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-177 | S08 | E3_S08_1_42 | S08-04 | 1 | SortLeft | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E3_S08_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-178 | S08 | E3_S08_1_42 | S08-05 | 1 | Status | 34817 | 0 | 边界 | `python agent/scripts/member4_test.py --source E3_S08_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-179 | S09 | E3_S09_1_42 | S09-01 | 1 | WaterValve | TRUE | FALSE | 时序 | `python agent/scripts/member4_test.py --source E3_S09_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-180 | S09 | E3_S09_1_42 | S09-02 | 1 | WaterValve | TRUE | FALSE | 时序 | `python agent/scripts/member4_test.py --source E3_S09_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-181 | S09 | E3_S09_1_42 | S09-03 | 1 | WaterValve | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E3_S09_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-182 | S09 | E3_S09_1_42 | S09-04 | 1 | WaterValve | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E3_S09_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-183 | S09 | E3_S09_1_42 | S09-06 | 1 | WaterValve | TRUE | FALSE | 边界 | `python agent/scripts/member4_test.py --source E3_S09_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-184 | S11 | E3_S11_1_42 | S11-01 | 1 | SensorValid | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E3_S11_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-185 | S11 | E3_S11_1_42 | S11-02 | 1 | SensorValid | TRUE | FALSE | 时序 | `python agent/scripts/member4_test.py --source E3_S11_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-186 | S11 | E3_S11_1_42 | S11-03 | 1 | SensorValid | TRUE | FALSE | 时序 | `python agent/scripts/member4_test.py --source E3_S11_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-187 | S11 | E3_S11_1_42 | S11-04 | 1 | AlarmLamp | TRUE | FALSE | 时序 | `python agent/scripts/member4_test.py --source E3_S11_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-188 | S11 | E3_S11_1_42 | S11-05 | 1 | SensorValid | TRUE | FALSE | 边界 | `python agent/scripts/member4_test.py --source E3_S11_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-189 | S12 | E3_S12_1_42 | S12-01 | 1 | MachineRun | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E3_S12_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-190 | S12 | E3_S12_1_42 | S12-02 | 1 | MachineRun | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E3_S12_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-191 | S12 | E3_S12_1_42 | S12-03 | 1 | MachineRun | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E3_S12_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-192 | S12 | E3_S12_1_42 | S12-04 | 1 | MachineRun | TRUE | FALSE | 时序 | `python agent/scripts/member4_test.py --source E3_S12_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-193 | S12 | E3_S12_1_42 | S12-05 | 1 | MachineRun | TRUE | FALSE | 边界 | `python agent/scripts/member4_test.py --source E3_S12_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-194 | S13 | E3_S13_1_42 | S13-01 | 1 | MainMotor | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E3_S13_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-195 | S13 | E3_S13_1_42 | S13-02 | 1 | MainMotor | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E3_S13_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-196 | S13 | E3_S13_1_42 | S13-03 | 1 | MainMotor | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E3_S13_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-197 | S13 | E3_S13_1_42 | S13-04 | 1 | MainMotor | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E3_S13_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-198 | S13 | E3_S13_1_42 | S13-05 | 1 | MainMotor | TRUE | FALSE | 时序 | `python agent/scripts/member4_test.py --source E3_S13_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-199 | S14 | E3_S14_1_42 | S14-03 | 2 | LowPump | FALSE | TRUE | 逻辑 | `python agent/scripts/member4_test.py --source E3_S14_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-200 | S14 | E3_S14_1_42 | S14-05 | 1 | ReliefValve | FALSE | TRUE | 逻辑 | `python agent/scripts/member4_test.py --source E3_S14_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-201 | S14 | E3_S14_1_42 | S14-06 | 1 | LowPump | TRUE | FALSE | 边界 | `python agent/scripts/member4_test.py --source E3_S14_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-202 | P01 | E4_P01_1_42 | P01-01 | 1 | Pump_Motor | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E4_P01_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-203 | P01 | E4_P01_1_42 | P01-02 | 1 | Pump_Motor | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E4_P01_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-204 | P01 | E4_P01_1_42 | P01-03 | 1 | Pump_Motor | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E4_P01_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-205 | P01 | E4_P01_1_42 | P01-04 | 1 | Pump_Motor | TRUE | FALSE | 时序 | `python agent/scripts/member4_test.py --source E4_P01_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-206 | P01 | E4_P01_1_42 | P01-05 | 1 | Pump_Motor | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E4_P01_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-207 | P01 | E4_P01_1_42 | P01-06 | 1 | Pump_Motor | TRUE | FALSE | 时序 | `python agent/scripts/member4_test.py --source E4_P01_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-208 | P01 | E4_P01_1_42 | P01-08 | 1 | Pump_Motor | TRUE | FALSE | 边界 | `python agent/scripts/member4_test.py --source E4_P01_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-209 | P04 | E4_P04_1_42 | P04-04 | 1 | VFD_RUN | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E4_P04_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-210 | P04 | E4_P04_1_42 | P04-05 | 1 | VFD_RUN | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E4_P04_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-211 | P04 | E4_P04_1_42 | P04-07 | 1 | VFD_RUN | TRUE | FALSE | 边界 | `python agent/scripts/member4_test.py --source E4_P04_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-212 | P07 | E4_P07_1_42 | P07-01 | 2 | pumpGroup[].RunComd | [True, False, True, False, False] | [False, False, False, False, False] | 逻辑 | `python agent/scripts/member4_test.py --source E4_P07_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-213 | P07 | E4_P07_1_42 | P07-03 | 1 | pumpGroup[].RunComd | [True, True, True, False, False] | [False, False, False, False, False] | 边界 | `python agent/scripts/member4_test.py --source E4_P07_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-214 | P07 | E4_P07_1_42 | P07-04 | 1 | pumpGroup[].RunComd | [True, False, False, False, False] | [False, False, False, False, False] | 逻辑 | `python agent/scripts/member4_test.py --source E4_P07_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-215 | P07 | E4_P07_1_42 | P07-05 | 1 | pumpGroup[].RunComd | [True, False, False, False, False] | [False, False, False, False, False] | 逻辑 | `python agent/scripts/member4_test.py --source E4_P07_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-216 | P07 | E4_P07_1_42 | P07-06 | 1 | pumpGroup[].RunComd | [False, True, False, True, True] | [False, False, False, False, False] | 边界 | `python agent/scripts/member4_test.py --source E4_P07_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-217 | P07 | E4_P07_1_42 | P07-07 | 1 | pumpGroup[].RunComd | [False, False, True, True, True] | [False, False, False, False, False] | 逻辑 | `python agent/scripts/member4_test.py --source E4_P07_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-218 | P10 | E4_P10_1_42 | P10-01 | 1 | HeaterStatus | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E4_P10_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-219 | P10 | E4_P10_1_42 | P10-02 | 1 | HeaterStatus | TRUE | FALSE | 时序 | `python agent/scripts/member4_test.py --source E4_P10_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-220 | P10 | E4_P10_1_42 | P10-03 | 1 | HeaterStatus | TRUE | FALSE | 时序 | `python agent/scripts/member4_test.py --source E4_P10_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-221 | P10 | E4_P10_1_42 | P10-04 | 1 | HeaterStatus | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E4_P10_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-222 | P10 | E4_P10_1_42 | P10-05 | 1 | HeaterStatus | TRUE | FALSE | 边界 | `python agent/scripts/member4_test.py --source E4_P10_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-223 | P11 | E4_P11_1_42 | P11-01 | 1 | MotorForward | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E4_P11_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-224 | P11 | E4_P11_1_42 | P11-02 | 2 | MotorForward | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E4_P11_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-225 | P11 | E4_P11_1_42 | P11-03 | 2 | MotorForward | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E4_P11_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-226 | P11 | E4_P11_1_42 | P11-04 | 1 | MotorForward | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E4_P11_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-227 | P11 | E4_P11_1_42 | P11-06 | 2 | MotorForward | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E4_P11_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-228 | P11 | E4_P11_1_42 | P11-07 | 2 | MotorForward | TRUE | FALSE | 边界 | `python agent/scripts/member4_test.py --source E4_P11_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-229 | P12 | E4_P12_1_42 | P12-01 | 1 | THICKNESS_ALARM | TRUE | FALSE | 时序 | `python agent/scripts/member4_test.py --source E4_P12_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-230 | P12 | E4_P12_1_42 | P12-02 | 1 | Slab_Fault_Counter | 1 | 0 | 逻辑 | `python agent/scripts/member4_test.py --source E4_P12_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-231 | P12 | E4_P12_1_42 | P12-04 | 1 | Slab_Runtime_Accumulator | 1000.0 | 0.0 | 逻辑 | `python agent/scripts/member4_test.py --source E4_P12_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-232 | P12 | E4_P12_1_42 | P12-05 | 1 | THICKNESS_ALARM | TRUE | FALSE | 时序 | `python agent/scripts/member4_test.py --source E4_P12_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-233 | P12 | E4_P12_1_42 | P12-06 | 1 | THICKNESS_ALARM | TRUE | FALSE | 边界 | `python agent/scripts/member4_test.py --source E4_P12_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-234 | P13 | E4_P13_1_42 | P13-03 | 1 | TEMP_SETPOINT_ADJUST | 4 | 0 | 时序 | `python agent/scripts/member4_test.py --source E4_P13_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-235 | P13 | E4_P13_1_42 | P13-05 | 1 | TEMP_SETPOINT_ADJUST | 3 | 0 | 时序 | `python agent/scripts/member4_test.py --source E4_P13_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-236 | P15 | E4_P15_1_42 | P15-01 | 1 | valveARun | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E4_P15_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-237 | P15 | E4_P15_1_42 | P15-02 | 1 | valveARun | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E4_P15_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-238 | P15 | E4_P15_1_42 | P15-03 | 1 | valveARun | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E4_P15_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-239 | P15 | E4_P15_1_42 | P15-04 | 1 | valveARun | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E4_P15_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-240 | P15 | E4_P15_1_42 | P15-05 | 1 | valveARun | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E4_P15_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-241 | P15 | E4_P15_1_42 | P15-06 | 1 | valveARun | TRUE | FALSE | 边界 | `python agent/scripts/member4_test.py --source E4_P15_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-242 | P15 | E4_P15_1_42 | P15-07 | 1 | valveARun | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E4_P15_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-243 | P16 | E4_P16_1_42 | P16-01 | 1 | conveyorRight | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E4_P16_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-244 | P16 | E4_P16_1_42 | P16-02 | 1 | conveyorRight | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E4_P16_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-245 | P16 | E4_P16_1_42 | P16-04 | 1 | conveyorRight | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E4_P16_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-246 | P16 | E4_P16_1_42 | P16-07 | 2 | conveyorRight | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E4_P16_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-247 | P16 | E4_P16_1_42 | P16-08 | 1 | conveyorRight | TRUE | FALSE | 边界 | `python agent/scripts/member4_test.py --source E4_P16_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-248 | P17 | E4_P17_1_42 | P17-01 | 1 | recipeQueryResult | {'recipeID': 1, 'ingredientType': 10, 'ingredientRatio': 0.5, 'productionTemperature': 100.0} | {'ingredientRatio': 0.0, 'ingredientType': 0, 'productionTemperature': 0.0, 'recipeID': 0} | 逻辑 | `python agent/scripts/member4_test.py --source E4_P17_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-249 | P17 | E4_P17_1_42 | P17-02 | 1 | error | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E4_P17_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-250 | P17 | E4_P17_1_42 | P17-03 | 1 | recipeAdded | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E4_P17_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-251 | P17 | E4_P17_1_42 | P17-04 | 1 | error | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E4_P17_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-252 | P17 | E4_P17_1_42 | P17-05 | 1 | error | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E4_P17_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-253 | P17 | E4_P17_1_42 | P17-06 | 1 | error | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E4_P17_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-254 | P17 | E4_P17_1_42 | P17-07 | 1 | recipeAdded | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E4_P17_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-255 | P17 | E4_P17_1_42 | P17-08 | 1 | recipeAdded | TRUE | FALSE | 边界 | `python agent/scripts/member4_test.py --source E4_P17_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-256 | P19 | E4_P19_1_42 | P19-01 | 1 | MoveDown | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E4_P19_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-257 | P19 | E4_P19_1_42 | P19-02 | 1 | MoveDown | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E4_P19_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-258 | P19 | E4_P19_1_42 | P19-03 | 1 | MoveDown | TRUE | FALSE | 时序 | `python agent/scripts/member4_test.py --source E4_P19_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-259 | P19 | E4_P19_1_42 | P19-04 | 1 | MoveDown | TRUE | FALSE | 时序 | `python agent/scripts/member4_test.py --source E4_P19_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-260 | P19 | E4_P19_1_42 | P19-05 | 1 | MoveDown | TRUE | FALSE | 时序 | `python agent/scripts/member4_test.py --source E4_P19_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-261 | P19 | E4_P19_1_42 | P19-09 | 1 | MoveDown | TRUE | FALSE | 边界 | `python agent/scripts/member4_test.py --source E4_P19_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-262 | P20 | E4_P20_1_42 | P20-01 | 1 | MotorForward | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E4_P20_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-263 | P20 | E4_P20_1_42 | P20-02 | 1 | MotorForward | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E4_P20_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-264 | P20 | E4_P20_1_42 | P20-03 | 1 | MotorForward | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E4_P20_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-265 | P20 | E4_P20_1_42 | P20-04 | 1 | MotorForward | TRUE | FALSE | 边界 | `python agent/scripts/member4_test.py --source E4_P20_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-266 | P20 | E4_P20_1_42 | P20-05 | 1 | MotorForward | TRUE | FALSE | 边界 | `python agent/scripts/member4_test.py --source E4_P20_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-267 | P20 | E4_P20_1_42 | P20-06 | 1 | MotorForward | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E4_P20_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-268 | P20 | E4_P20_1_42 | P20-07 | 1 | MotorForward | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E4_P20_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-269 | P20 | E4_P20_1_42 | P20-08 | 1 | kick | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E4_P20_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-270 | S01 | E4_S01_1_42 | S01-01 | 1 | ClampLeft | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E4_S01_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-271 | S01 | E4_S01_1_42 | S01-02 | 1 | ClampRight | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E4_S01_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-272 | S01 | E4_S01_1_42 | S01-04 | 1 | ClampLeft | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E4_S01_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-273 | S01 | E4_S01_1_42 | S01-05 | 1 | Status | 33025 | 0 | 逻辑 | `python agent/scripts/member4_test.py --source E4_S01_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-274 | S02 | E4_S02_1_42 | S02-01 | 1 | MotorFwd | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E4_S02_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-275 | S02 | E4_S02_1_42 | S02-02 | 1 | MotorFwd | TRUE | FALSE | 时序 | `python agent/scripts/member4_test.py --source E4_S02_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-276 | S02 | E4_S02_1_42 | S02-04 | 1 | MotorFwd | TRUE | FALSE | 时序 | `python agent/scripts/member4_test.py --source E4_S02_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-277 | S02 | E4_S02_1_42 | S02-06 | 1 | MotorFwd | TRUE | FALSE | 边界 | `python agent/scripts/member4_test.py --source E4_S02_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-278 | S03 | E4_S03_1_42 | S03-01 | 1 | DriveA_Run | TRUE | FALSE | 时序 | `python agent/scripts/member4_test.py --source E4_S03_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-279 | S03 | E4_S03_1_42 | S03-02 | 1 | DriveA_Run | TRUE | FALSE | 边界 | `python agent/scripts/member4_test.py --source E4_S03_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-280 | S03 | E4_S03_1_42 | S03-03 | 1 | DriveA_Run | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E4_S03_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-281 | S03 | E4_S03_1_42 | S03-04 | 1 | DriveA_Run | TRUE | FALSE | 时序 | `python agent/scripts/member4_test.py --source E4_S03_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-282 | S04 | E4_S04_1_42 | S04-01 | 1 | DriftAlarm | FALSE | TRUE | 时序 | `python agent/scripts/member4_test.py --source E4_S04_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-283 | S04 | E4_S04_1_42 | S04-03 | 2 | DriftAlarm | FALSE | TRUE | 逻辑 | `python agent/scripts/member4_test.py --source E4_S04_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-284 | S04 | E4_S04_1_42 | S04-06 | 3 | DriftAlarm | TRUE | FALSE | 边界 | `python agent/scripts/member4_test.py --source E4_S04_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-285 | S05 | E4_S05_1_42 | S05-06 | 2 | TotalVolume | 1.0 | 0.5 | 边界 | `python agent/scripts/member4_test.py --source E4_S05_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-286 | S06 | E4_S06_1_42 | S06-01 | 1 | HeatOn | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E4_S06_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-287 | S06 | E4_S06_1_42 | S06-02 | 1 | HeatOn | TRUE | FALSE | 边界 | `python agent/scripts/member4_test.py --source E4_S06_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-288 | S06 | E4_S06_1_42 | S06-03 | 1 | HeatOn | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E4_S06_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-289 | S06 | E4_S06_1_42 | S06-04 | 1 | OverTempAlarm | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E4_S06_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-290 | S06 | E4_S06_1_42 | S06-05 | 1 | LoadReduce | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E4_S06_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-291 | S07 | E4_S07_1_42 | S07-02 | 251 | FillValve | FALSE | TRUE | 逻辑 | `python agent/scripts/member4_test.py --source E4_S07_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-292 | S07 | E4_S07_1_42 | S07-04 | 3 | FillValve | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E4_S07_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-293 | S07 | E4_S07_1_42 | S07-05 | 1 | Conveyor | FALSE | TRUE | 逻辑 | `python agent/scripts/member4_test.py --source E4_S07_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-294 | S08 | E4_S08_1_42 | S08-01 | 1 | SortLeft | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E4_S08_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-295 | S08 | E4_S08_1_42 | S08-02 | 1 | Busy | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E4_S08_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-296 | S08 | E4_S08_1_42 | S08-04 | 1 | SortLeft | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E4_S08_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-297 | S09 | E4_S09_1_42 | S09-02 | 3 | WaterValve | FALSE | TRUE | 工具超时 | `python agent/scripts/member4_test.py --source E4_S09_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-298 | S09 | E4_S09_1_42 | S09-04 | 2 | WaterValve | FALSE | TRUE | 工具超时 | `python agent/scripts/member4_test.py --source E4_S09_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-299 | S09 | E4_S09_1_42 | S09-06 | 2 | WaterValve | FALSE | TRUE | 工具超时 | `python agent/scripts/member4_test.py --source E4_S09_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-300 | S10 | E4_S10_1_42 | S10-01 | 1 | TripOutput | FALSE | TRUE | 时序 | `python agent/scripts/member4_test.py --source E4_S10_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-301 | S11 | E4_S11_1_42 | S11-01 | 1 | SensorValid | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E4_S11_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-302 | S11 | E4_S11_1_42 | S11-02 | 1 | SensorValid | TRUE | FALSE | 时序 | `python agent/scripts/member4_test.py --source E4_S11_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-303 | S11 | E4_S11_1_42 | S11-03 | 1 | SensorValid | TRUE | FALSE | 时序 | `python agent/scripts/member4_test.py --source E4_S11_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-304 | S11 | E4_S11_1_42 | S11-04 | 1 | AlarmLamp | TRUE | FALSE | 时序 | `python agent/scripts/member4_test.py --source E4_S11_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-305 | S11 | E4_S11_1_42 | S11-05 | 1 | SensorValid | TRUE | FALSE | 边界 | `python agent/scripts/member4_test.py --source E4_S11_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-306 | S12 | E4_S12_1_42 | S12-01 | 1 | MachineRun | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E4_S12_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-307 | S12 | E4_S12_1_42 | S12-02 | 1 | MachineRun | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E4_S12_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-308 | S12 | E4_S12_1_42 | S12-03 | 1 | MachineRun | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E4_S12_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-309 | S12 | E4_S12_1_42 | S12-04 | 1 | MachineRun | TRUE | FALSE | 时序 | `python agent/scripts/member4_test.py --source E4_S12_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-310 | S12 | E4_S12_1_42 | S12-05 | 1 | MachineRun | TRUE | FALSE | 边界 | `python agent/scripts/member4_test.py --source E4_S12_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-311 | S13 | E4_S13_1_42 | S13-03 | 101 | MainMotor | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E4_S13_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-312 | S13 | E4_S13_1_42 | S13-04 | 101 | MainMotor | TRUE | FALSE | 逻辑 | `python agent/scripts/member4_test.py --source E4_S13_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-313 | S13 | E4_S13_1_42 | S13-05 | 151 | SpeedHigh | FALSE | TRUE | 时序 | `python agent/scripts/member4_test.py --source E4_S13_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-314 | S14 | E4_S14_1_42 | S14-03 | 2 | LowPump | FALSE | TRUE | 逻辑 | `python agent/scripts/member4_test.py --source E4_S14_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-315 | S14 | E4_S14_1_42 | S14-05 | 1 | ReliefValve | FALSE | TRUE | 逻辑 | `python agent/scripts/member4_test.py --source E4_S14_1_42/final.st --cases-dir tests/cases` | 待修 |
| DEF-316 | S14 | E4_S14_1_42 | S14-06 | 1 | LowPump | TRUE | FALSE | 边界 | `python agent/scripts/member4_test.py --source E4_S14_1_42/final.st --cases-dir tests/cases` | 待修 |

## 4 复现

`actual/*.csv` 没有随精简包交付，所以本机只能用**实验机**复跑。每条缺陷的复现命令模板：

```bash
# 在实验机（装了 CODESYS V3.5 SP22 Patch 4 + matiec）上，任一 run 复跑：
python agent/scripts/member4_test.py \
  --source <批次>/live/<run_id>/final.st \
  --task-card <批次>/live/<run_id>/task_card.json \
  --cases-dir tests/cases --artifact-dir /tmp/repro \
  --exe "<CODESYS.exe 路径>" --profile "CODESYS V3.5 SP22 Patch 4"
```

如果后续补交 `test/actual/*.csv`，本机可以直接用 replay 后端复现同一拍：

```bash
python tests/run_tests.py --cases tests/cases/P03.csv \
  --io tests/cases/_fixtures/P03.io.json --out /tmp/P03.jsonl \
  --backend replay --actual experiments/runs/E3/P03_r1_s42/test/actual
```

## 5 争议用例条目（33 条，单独列，不混进上面的计数）

这些条目**不一定是模型的错**，逐条依据见 `docs/判据与用例版本核对.md`：

| 用例 | 条数 | 裁决 |
| --- | ---: | --- |
| S05-06 | 4 | 用例错：非上升沿却期望累加（K1 只认上升沿） |
| S11-02 | 4 | 用例错：断线未满 2 s 时期望 ControlValue=0 无依据 |
| S11-03 | 4 | 用例错：同上 |
| S11-05 | 4 | 用例错：3.59 mA 已越断线阈值，期望 Status=0 错 |
| P19-02 | 3 | 用例错：UpLimitSwitch=TRUE 却期望 MoveUp=TRUE（违反 K1） |
| P19-03 | 3 | 用例错：同上 |
| P19-04 | 3 | 用例错：同上 |
| P19-09 | 3 | 版本错 + 模式互斥未满足 |
| S11-04 | 3 | 歧义：1 Hz 闪烁的相位边界未定义 |
| P19-08 | 2 | 版本错：实验用的是旧版急停极性用例 |

## 6 回归（D4.6）

| 项 | 数值 |
| --- | --- |
| 复测题数 | 待填 |
| 修好 | 待填 |
| 仍失败 | 待填 |
| **修复引入的破坏数** | 待填 |

**为什么是空的**：回归要求「同一题修复前后的两份产物都要有逐拍 actual」才能算出
「修 A 把 B 改坏」的数量。精简包只交付了每次 run 的最终产物，没有保留修复前中间产物的 actual；
`repair_1.evaluation.json` 只在整个包里出现 1 次。要补这一节，需要在实验机上对 `repair_rounds>0` 的题重跑一次，
把修复前/后两次的 actual 都落盘。这条如实标注，不拿替代数据凑。

## 7 结论

- 失败主要集中在 逻辑 / 时序 / 边界 三类原因；`工具超时` 与 `编译` 已按口径单列，未计入模型失败。
- 33 条争议条目应先按 `docs/判据与用例版本核对.md` 裁决，其中 S05-06 会影响 E1/E2/E4 的整题通过数。
- 逐 run 与成员3 的汇总对账：一致 132 条，不一致 0 条。

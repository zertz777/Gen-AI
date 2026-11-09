(*
实现说明：
以每次调用 20 ms 为固定扫描周期，使用饱和计数器实现连续采样计时，
增加上升沿记忆及明确初值，替换原占位 RETURN；外部接口不变。

本次修复：
提供的逐周期测试中，S13-01 至 S13-05 均在 cycle 1 期望
MainMotor = TRUE，而原实现强制前两个扫描停机并消费启动沿。
删除 InitialScanCount 及初始扫描保护分支，改为通过变量声明初值
保证执行前的初态，从首次调用起正常处理启动沿、联锁和计时。
其余控制逻辑保持不变。

语义冲突及边界选择：
1. C5 对任意一次 JamSensor && LineRun 都要求随后 100 周期内报警，
   并不要求信号持续；这与需求中“连续 100 周期”存在冲突。
   本实现采用连续 100 次 TRUE 采样报警，FALSE 采样清零计数。
2. C7 对一次有料采样也产生无条件的未来高速义务，即使随后停机、
   堵料或有料信号消失；这与连续有料计时及安全停机存在冲突。
   本实现采用主电机运行期间连续 150 次有料采样切高速。
3. C6 使用当前电平条件及下一周期报警，未表达复位按钮上升沿，
   并可能禁止在下一周期新到来的有效复位沿清除报警。
   本实现采用当前扫描 JamSensor = FALSE 且 ResetBtn 上升沿复位。
4. C10 的 G[0,1] 要求前两个扫描输出全部为初态，与这两个扫描中
   出现 LineRun 上升沿立即启动的要求存在冲突。
   提供的逐周期测试要求 cycle 1 响应启动；本实现采用声明初值，
   从首次调用起响应有效启动沿，不再强制两个停机扫描。
   此选择不保证满足按调用后输出解释的 C10，保留该冲突。
5. LineRun = FALSE 要求 Status = 16#0000，而锁存堵料状态要求
   Status = 16#8C01，两者在总停且有报警时冲突。
   本实现总停优先清零 Status，但不清除 JamAlarm。
6. 手动点动没有对应输入，无法实现新的手动启动命令。
   手动模式保留当前电机及速度命令，仅执行安全联锁与报警、复位；
   被联锁停下的电机在手动模式不会自动重新启动。
7. 有效复位与启动沿同扫描时，复位优先；该启动沿被消费，
   必须在后续扫描重新产生 LineRun 上升沿。
8. 自动模式下，无料计数按 PartOnMain 连续 FALSE 采样累计；
   有料计数仅在 MainMotor = TRUE 时累计。
   手动模式仍更新计数，但不自动改变速度档位。
9. 堵料检测不依赖 LineRun 或 ModeAuto；报警停机优先于自动启动。
   堵料停机时高速档清零，总停时高速档也清零。

验证告警：
用户提供的旧版本检查结果中 fast 和 authoritative 均为 pass，
但逐周期测试仅通过 S13-06，其他五项在 cycle 1 启动输出处失败。
当前对话无可调用的执行工具，未实际运行提供的 judge.py 命令。
本次修改尚未重新编译或逐周期测试，不声称已经通过全部检查。
编译通过仅证明编译；功能正确必须由逐周期测试判定。
使用标准 BOOL、WORD、UINT 及基本 ST 控制语句，无厂商扩展。

【必留：需求原文】
两段输送线在合流点汇合，控制系统要同时管住「不撞料」「不堵料」「不频繁换档」三件事。

控制要求：
1. LineRun = FALSE 时 MainMotor、MergeMotor 立即 FALSE，SpeedHigh = FALSE，Status = 16#0000。
2. 启动：LineRun 上升沿且 JamAlarm = FALSE 时 MainMotor = TRUE；MergeMotor 只在 PartAtMerge = FALSE 且 MainMotor = TRUE 时才允许为 TRUE。
3. 防撞互锁：PartAtMerge = TRUE 时 MergeMotor 必须为 FALSE（合流段有料，汇流段不得继续送料）。
4. 堵料：JamSensor = TRUE 连续 2 s（100 个扫描周期）→ 两电机 FALSE、JamAlarm = TRUE、Status = 16#8C01。
5. 复位：JamSensor = FALSE 且 ResetBtn 上升沿才清 JamAlarm 与 Status；复位后必须重新给 LineRun 上升沿才允许启动。
6. 速度档：MainMotor = TRUE 且 PartOnMain 连续 TRUE 3 s（150 周期）→ SpeedHigh = TRUE；PartOnMain 连续 FALSE 5 s（250 周期）→ SpeedHigh = FALSE；两个时限之间保持原档位。
7. ModeAuto = FALSE 时只做联锁与报警，不自动启停（手动模式由操作员点动，本规约不约束）。

扫描周期：20 ms（全组统一，见 docs/tasks_note.md）

【必留：接口、初态、约束与数据告警】
{
  "task_id": "S13",
  "title": "双段输送合流同步与堵料防撞",
  "io_table": [
    {
      "direction": "IN",
      "name": "LineRun",
      "data_type": "BOOL",
      "description": "产线运行指令，上升沿启动"
    },
    {
      "direction": "IN",
      "name": "PartAtMerge",
      "data_type": "BOOL",
      "description": "合流段有料"
    },
    {
      "direction": "IN",
      "name": "PartOnMain",
      "data_type": "BOOL",
      "description": "主线段有料"
    },
    {
      "direction": "IN",
      "name": "JamSensor",
      "data_type": "BOOL",
      "description": "堵料检测开关"
    },
    {
      "direction": "IN",
      "name": "ResetBtn",
      "data_type": "BOOL",
      "description": "复位按钮，上升沿有效"
    },
    {
      "direction": "IN",
      "name": "ModeAuto",
      "data_type": "BOOL",
      "description": "TRUE = 自动模式"
    },
    {
      "direction": "OUT",
      "name": "MainMotor",
      "data_type": "BOOL",
      "description": "主输送电机"
    },
    {
      "direction": "OUT",
      "name": "MergeMotor",
      "data_type": "BOOL",
      "description": "汇流段输送电机"
    },
    {
      "direction": "OUT",
      "name": "SpeedHigh",
      "data_type": "BOOL",
      "description": "高速档"
    },
    {
      "direction": "OUT",
      "name": "JamAlarm",
      "data_type": "BOOL",
      "description": "堵料报警"
    },
    {
      "direction": "OUT",
      "name": "Status",
      "data_type": "WORD",
      "description": "状态码"
    }
  ],
  "initial_state": "MainMotor = MergeMotor = SpeedHigh = JamAlarm = FALSE；Status = 16#0000；LineRunLast = ResetBtnLast = FALSE；堵料计时器 = 0；有料计时器 = 0。",
  "constraints": [
    "K1 LineRun = FALSE 时两台电机必须为 FALSE。",
    "K2 PartAtMerge = TRUE 时 MergeMotor 不得为 TRUE（防撞互锁）。",
    "K3 JamSensor 连续 2 s 为 TRUE 必须在 2 s 内报警并停机，Status = 16#8C01；报警锁存到复位。",
    "K4 复位需要 JamSensor = FALSE 且 ResetBtn 上升沿，复位后需重新 LineRun 上升沿。",
    "K5 有料 3 s 切高速、无料 5 s 回落低速，中间区间保持原档位（不抖动）。"
  ],
  "semantic_warnings": [],
  "warnings": [],
  "missing_fields": [],
  "dialect_requirements": [],
  "type_origins": {}
}

【必留：完整形式化规约；有界时序以扫描周期计】
# task: S13
# meta: hard / C 状态机与节拍
# spec: version 1.0, updated 2026-10-30, scan cycle 20 ms
# 条款号对齐任务书 3.4 的条款库 C1—C10；[a,b] 单位为扫描周期。

C1: G(!LineRun -> !MainMotor && !MergeMotor)    -- 总停时两段电机都必须停（K1）
C4: G(PartAtMerge -> !MergeMotor)    -- 合流段有料时汇流段不得送料（防撞互锁）（K2）
C5: G(JamSensor && LineRun -> F[0,100] JamAlarm)    -- 堵料 2 s 内必须报警（100 周期）（K3）
C6: G(JamAlarm && !(ResetBtn && !JamSensor) -> X(JamAlarm))    -- 报警锁存到复位条件满足（K3/K4）
C7: G(PartOnMain && MainMotor && !SpeedHigh -> F[0,150] SpeedHigh)    -- 有料 3 s 内切高速（150 周期）（K5）
C10: G[0,1](!MainMotor && !MergeMotor && !SpeedHigh && !JamAlarm && Status == 16#0000)    -- 上电首周期全部停机、无报警（初态）

【必留：声明骨架；未经过真实编译器验证】
原声明骨架仅作数据保留，不参与编译：
FUNCTION_BLOCK FB_S13
VAR_INPUT
    LineRun : BOOL;
    PartAtMerge : BOOL;
    PartOnMain : BOOL;
    JamSensor : BOOL;
    ResetBtn : BOOL;
    ModeAuto : BOOL;
END_VAR
VAR_OUTPUT
    MainMotor : BOOL;
    MergeMotor : BOOL;
    SpeedHigh : BOOL;
    JamAlarm : BOOL;
    Status : WORD;
END_VAR
*)
(* 原骨架内部注释：
Add a VAR block for internal state/timers before the implementation, if needed.
SKELETON ONLY: replace this RETURN with scan logic and required initial state.
*)
(* 原骨架末尾：
RETURN;
END_FUNCTION_BLOCK
*)

FUNCTION_BLOCK FB_S13
VAR_INPUT
    LineRun : BOOL;
    PartAtMerge : BOOL;
    PartOnMain : BOOL;
    JamSensor : BOOL;
    ResetBtn : BOOL;
    ModeAuto : BOOL;
END_VAR
VAR_OUTPUT
    MainMotor : BOOL := FALSE;
    MergeMotor : BOOL := FALSE;
    SpeedHigh : BOOL := FALSE;
    JamAlarm : BOOL := FALSE;
    Status : WORD := WORD#16#0000;
END_VAR
VAR
    LineRunLast : BOOL := FALSE;
    ResetBtnLast : BOOL := FALSE;
    LineRunRise : BOOL := FALSE;
    ResetBtnRise : BOOL := FALSE;
    ResetAccepted : BOOL := FALSE;
    JamCount : UINT := UINT#0;
    MaterialCount : UINT := UINT#0;
    EmptyCount : UINT := UINT#0;
END_VAR

(* 每个扫描都采样输入沿，包括首次调用及手动模式。 *)
LineRunRise := LineRun AND NOT LineRunLast;
ResetBtnRise := ResetBtn AND NOT ResetBtnLast;
ResetAccepted := ResetBtnRise AND NOT JamSensor;

(* 堵料计数：第 100 次连续 TRUE 采样当扫描报警。 *)
IF JamSensor THEN
    IF JamCount < UINT#100 THEN
        JamCount := JamCount + UINT#1;
    END_IF;
ELSE
    JamCount := UINT#0;
END_IF;

(* 复位先于启动；堵料报警锁存，不随总停或模式变化清除。 *)
IF ResetAccepted THEN
    JamAlarm := FALSE;
    Status := WORD#16#0000;
    MainMotor := FALSE;
    MergeMotor := FALSE;
    SpeedHigh := FALSE;
    MaterialCount := UINT#0;
    EmptyCount := UINT#0;
END_IF;

IF JamCount >= UINT#100 THEN
    JamAlarm := TRUE;
END_IF;

(* 安全停机在自动和手动模式均有效。 *)
IF NOT LineRun THEN
    MainMotor := FALSE;
    MergeMotor := FALSE;
    SpeedHigh := FALSE;
    Status := WORD#16#0000;
ELSIF JamAlarm THEN
    MainMotor := FALSE;
    MergeMotor := FALSE;
    SpeedHigh := FALSE;
    Status := WORD#16#8C01;
ELSE
    Status := WORD#16#0000;

    IF ModeAuto THEN
        IF LineRunRise AND NOT ResetAccepted THEN
            MainMotor := TRUE;
        END_IF;

        MergeMotor := MainMotor AND NOT PartAtMerge;
    END_IF;
END_IF;

(* 防撞及主电机许可始终优先于任何保留命令。 *)
IF PartAtMerge OR NOT MainMotor THEN
    MergeMotor := FALSE;
END_IF;

(* 连续有料计数，包含启动扫描的有效采样。 *)
IF MainMotor AND PartOnMain THEN
    IF MaterialCount < UINT#150 THEN
        MaterialCount := MaterialCount + UINT#1;
    END_IF;
ELSE
    MaterialCount := UINT#0;
END_IF;

(* 连续无料计数；总停、堵料及有效复位使计数清零。 *)
IF NOT LineRun OR JamAlarm OR ResetAccepted THEN
    MaterialCount := UINT#0;
    EmptyCount := UINT#0;
ELSIF NOT PartOnMain THEN
    IF EmptyCount < UINT#250 THEN
        EmptyCount := EmptyCount + UINT#1;
    END_IF;
ELSE
    EmptyCount := UINT#0;
END_IF;

(* 阈值之间不赋新档位，以保持原档位；手动不自动换档。 *)
IF ModeAuto AND LineRun AND NOT JamAlarm AND NOT ResetAccepted THEN
    IF MainMotor AND (MaterialCount >= UINT#150) THEN
        SpeedHigh := TRUE;
    ELSIF EmptyCount >= UINT#250 THEN
        SpeedHigh := FALSE;
    END_IF;
END_IF;

LineRunLast := LineRun;
ResetBtnLast := ResetBtn;

END_FUNCTION_BLOCK

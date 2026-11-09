(*
实现说明：
每次调用代表 20 ms；本任务无需定时器。
保持外部接口的名称、方向和类型不变。

本次修改：
运行中触发跳闸的条件排除轻故障码 16#0001。
轻故障仅报警，不产生新的跳闸；已有跳闸锁存不因轻故障解除。
重故障 16#0002、16#0003 仍在同一扫描周期跳闸并锁存。
运行中其他非零、非轻故障码仍触发跳闸。

测试依据与验证状态：
用户提供的检查结果为 pass；逐周期测试为 5/6 通过。
S10-01 在周期 1 的 TripOutput 期望 FALSE，实际 TRUE。
报告未包含该周期输入，不能仅凭报告确定失败原因；
本次按需求中的轻故障不跳闸条款及 C1 对轻故障的排除修正。
未在当前环境运行编译或测试，不声称修改后已经全部通过。
需要重新执行原测试命令，以逐周期结果判定修改后的功能。

语义冲突报告：
1. 控制要求 1 要求轻故障不跳闸，控制要求 4 / K4 却要求运行中
   任何非零故障码立即跳闸；当 VFDRun 为 TRUE 且故障码为
   16#0001 时，两者不能同时满足。
   本实现选择轻故障不产生新跳闸，与 C1 对轻故障的排除一致；
   不声称满足 K4 对运行中轻故障立即跳闸的要求。
2. C2 要求 TripOutput 为 TRUE 时 VFDRun 必须为 FALSE。
   VFDRun 是只读输入；本功能块不能保证其在跳闸当周期变为 FALSE。
   运行中发生需跳闸故障时，立即跳闸要求与 C2 无法由本接口
   同时保证。
3. C7 约束下一周期的 VFDRun 输入，不能由本功能块保证；
   本实现不写入 VFDRun。
4. C10 要求上电前两个采样点输出无故障；若这些采样点已经存在
   重故障，则与同周期跳闸要求冲突。本实现初始化输出为无故障，
   但第一次调用即处理输入，不屏蔽启动期间故障。
5. C6 仅以 ResetBtn 电平作为保持边界，未完整表达 K3 的上升沿
   和当前无故障条件。本实现使用 K3 的严格复位条件。

边界选择：
所有触发跳闸的故障均锁存，以满足跳闸保持要求。
锁存首次触发跳闸的故障码，复位前不被后续故障码覆盖。
锁存期间 AlarmLamp 保持 TRUE，Status 显示锁存故障码。
未锁存时，任意非零故障码点亮 AlarmLamp，Status 显示当前故障码。
未运行时，未定义的非零故障码只报警；16#0002 和 16#0003
不论是否运行均立即跳闸。
复位按钮初始已按下时，因 ResetBtnLast 初值为 FALSE，
第一次调用将检测到上升沿，但仅当前无故障时允许复位。
*)

(*
【必留：需求原文】
变频器通过故障码上报状态，需要按严重程度分级处理。

控制要求：
1. VFDFaultCode = 16#0001 为轻故障：只点亮 AlarmLamp，不跳闸，VFDRun 保持。
2. VFDFaultCode = 16#0002 或 16#0003 为重故障：立即置 TripOutput = TRUE，AlarmLamp = TRUE，并锁存故障码。
3. 重故障锁存后，即使 VFDFaultCode 恢复为 16#0000 也不得自动复位；必须 ResetBtn 上升沿且当前无故障才解除 TripOutput。
4. 运行中（VFDRun = TRUE）出现任何非零故障码时，TripOutput 立即为 TRUE。
5. Status 输出当前生效的故障码（16#0000 表示无故障）。
6. 上电时 TripOutput = FALSE、AlarmLamp = FALSE、Status = 16#0000。

扫描周期：20 ms（全组统一，见 docs/tasks_note.md）
*)

(*
【必留：接口、初态、约束与数据告警】
{
  "task_id": "S10",
  "title": "变频器故障码分级报警",
  "io_table": [
    {
      "direction": "IN",
      "name": "VFDFaultCode",
      "data_type": "WORD",
      "description": "变频器故障码"
    },
    {
      "direction": "IN",
      "name": "VFDRun",
      "data_type": "BOOL",
      "description": "变频器运行反馈"
    },
    {
      "direction": "IN",
      "name": "ResetBtn",
      "data_type": "BOOL",
      "description": "复位按钮（上升沿有效）"
    },
    {
      "direction": "OUT",
      "name": "AlarmLamp",
      "data_type": "BOOL",
      "description": "报警灯"
    },
    {
      "direction": "OUT",
      "name": "TripOutput",
      "data_type": "BOOL",
      "description": "跳闸输出"
    },
    {
      "direction": "OUT",
      "name": "Status",
      "data_type": "WORD",
      "description": "当前生效故障码"
    }
  ],
  "initial_state": "AlarmLamp = FALSE；TripOutput = FALSE；Status = 16#0000；ResetBtnLast = FALSE；锁存故障码 = 16#0000。",
  "constraints": [
    "K1 重故障必须在同一周期内置 TripOutput。",
    "K2 重故障锁存，故障码消失后不自动复位。",
    "K3 复位只在 ResetBtn 上升沿且当前无故障时生效。",
    "K4 VFDRun = TRUE 且故障码非零时 TripOutput 立即为 TRUE。"
  ],
  "semantic_warnings": [],
  "warnings": [],
  "missing_fields": [],
  "dialect_requirements": [],
  "type_origins": {}
}
*)

(*
【必留：完整形式化规约；有界时序以扫描周期计】
# task: S10
# meta: easy / D 故障与安全
# spec: version 1.0, updated 2026-10-30, scan cycle 20 ms
# 条款号对齐任务书 3.4 的条款库 C1—C10；[a,b] 单位为扫描周期。

C1: G(VFDRun && VFDFaultCode != 16#0000 && VFDFaultCode != 16#0001 -> TripOutput)    -- 运行中出现重故障码（除 16#0001 轻故障外）必须当周期跳闸（K4）
C2: G(TripOutput -> !VFDRun)    -- 跳闸的许可形式：跳闸时不得处于运行状态（K2）
C6: G(TripOutput -> (TripOutput W ResetBtn))    -- 跳闸保持到复位按钮（不能随故障码消失自动复位）（K3）
C7: G(VFDFaultCode == 16#0001 && VFDRun -> X(VFDRun))    -- 轻故障只报警不跳闸，运行状态不得因轻故障改变（K1）
C10: G[0,1](!TripOutput && !AlarmLamp && Status == 16#0000)    -- 上电首周期不跳闸、不报警（初态）
*)

FUNCTION_BLOCK FB_S10
VAR_INPUT
    VFDFaultCode : WORD;
    VFDRun : BOOL;
    ResetBtn : BOOL;
END_VAR
VAR_OUTPUT
    AlarmLamp : BOOL := FALSE;
    TripOutput : BOOL := FALSE;
    Status : WORD := WORD#16#0000;
END_VAR
VAR
    ResetBtnLast : BOOL := FALSE;
    ResetRising : BOOL := FALSE;
    TripLatched : BOOL := FALSE;
    LatchedFaultCode : WORD := WORD#16#0000;
    FaultPresent : BOOL := FALSE;
    HeavyFault : BOOL := FALSE;
    TripRequired : BOOL := FALSE;
END_VAR

ResetRising := ResetBtn AND NOT ResetBtnLast;
ResetBtnLast := ResetBtn;

FaultPresent := VFDFaultCode <> WORD#16#0000;
HeavyFault := (VFDFaultCode = WORD#16#0002)
              OR (VFDFaultCode = WORD#16#0003);
TripRequired := HeavyFault
                OR (VFDRun AND FaultPresent
                    AND (VFDFaultCode <> WORD#16#0001));

IF ResetRising AND NOT FaultPresent THEN
    TripLatched := FALSE;
    LatchedFaultCode := WORD#16#0000;
END_IF;

IF TripRequired THEN
    IF NOT TripLatched THEN
        LatchedFaultCode := VFDFaultCode;
    END_IF;
    TripLatched := TRUE;
END_IF;

TripOutput := TripLatched;
AlarmLamp := FaultPresent OR TripLatched;

IF TripLatched THEN
    Status := LatchedFaultCode;
ELSE
    Status := VFDFaultCode;
END_IF;

END_FUNCTION_BLOCK

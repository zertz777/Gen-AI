(*
【必留：需求原文】
Write a function block FB to implement a temperature control logic. The program should include the following functions:
1. Read the value of the temperature sensor through an analog input module.
2. Compare the read temperature value TemperatureSensorInput with the set temperature value SetTemperature.
3. If the actual temperature is lower than the set temperature, start the heater HeaterOutput.
4. If the actual temperature is higher than the set temperature, turn off the heater HeaterOutput.
5. If the heater works continuously for more than a certain period (for convenience, using 5s), it should trigger an overheating protection, automatically turn off the heater, and must wait for a certain period (for convenience, using 3s) before the overheating protection can be lifted.
6. Provide status indication, displaying the current temperature, set temperature, heater status, and whether overheating protection is triggered.
7. Provide temperature sensor fault judgment, if the read temperature value TemperatureSensorInput is less than 0 or greater than 100, it is considered a sensor fault, and the heater should be turned off.

中文摘要：温度逻辑控制：低于设定值加热、高于设定值停止，
连续加热超 5 秒触发过热保护并需等 3 秒才能解除，
传感器越界判故障。

扫描周期：20 ms（全组统一，见 docs/tasks_note.md）

【必留：接口、初态、约束与数据告警】
{
  "task_id": "P10",
  "title": "Temperature Logic Control",
  "io_table": [
    {
      "direction": "IN",
      "name": "TemperatureSensorInput",
      "data_type": "REAL",
      "description": "The input value of the temperature sensor, i.e., the actual temperature"
    },
    {
      "direction": "IN",
      "name": "SetTemperature",
      "data_type": "REAL",
      "description": "The set temperature value"
    },
    {
      "direction": "OUT",
      "name": "CurrentTemperature",
      "data_type": "REAL",
      "description": "Display of the current temperature"
    },
    {
      "direction": "OUT",
      "name": "SetTempDisplay",
      "data_type": "REAL",
      "description": "Display of the set temperature"
    },
    {
      "direction": "OUT",
      "name": "HeaterStatus",
      "data_type": "BOOL",
      "description": "Display of the heater status"
    },
    {
      "direction": "OUT",
      "name": "OverheatProtection",
      "data_type": "BOOL",
      "description": "Display of the overheating protection status"
    },
    {
      "direction": "OUT",
      "name": "HeaterOutput",
      "data_type": "BOOL",
      "description": "The control output of the heater"
    }
  ],
  "initial_state": "HeaterOutput = FALSE；OverheatProtection = FALSE；传感器故障标志 = FALSE；加热计时与保护计时清零。",
  "constraints": [
    "K1 TemperatureSensorInput < SetTemperature 时 HeaterOutput = TRUE，> SetTemperature 时 HeaterOutput = FALSE。",
    "K2 加热连续运行超过 5 s 触发 OverheatProtection，并强制 HeaterOutput = FALSE。",
    "K3 过热保护触发后必须保持至少 3 s 才能解除，解除前不得重新加热。",
    "K4 TemperatureSensorInput < 0 或 > 100 判为传感器故障，此时不得继续加热。"
  ],
  "semantic_warnings": [],
  "warnings": [],
  "missing_fields": [],
  "dialect_requirements": [],
  "type_origins": {}
}

【必留：完整形式化规约；有界时序以扫描周期计】
# task: P10
# meta: medium / B 模拟量与数据处理
# spec: version 1.0, updated 2026-10-30, scan cycle 20 ms
# 条款号对齐任务书 3.4 的条款库 C1—C10；[a,b] 单位为扫描周期。

C1: G(OverheatProtection -> !HeaterOutput)    -- 过热保护动作时加热必须关断（保护优先于温控）（K2）
C2: G(HeaterOutput -> !OverheatProtection)    -- 加热的前提是没有过热保护（同一约束的许可形式）（K2）
C7: G(TemperatureSensorInput < 0.0 -> X(!HeaterOutput))    -- 低于 0 ℃ 判为传感器故障，下一周期不得加热（K4）
C7b: G(TemperatureSensorInput > 100.0 -> X(!HeaterOutput))    -- 高于 100 ℃ 判为传感器故障，下一周期不得加热（K4）
C9: G(OverheatProtection -> G[0,150](OverheatProtection))    -- 过热保护触发后至少保持 3 s 才能解除（K3）
C10: G[0,1](!HeaterOutput && !OverheatProtection)    -- 上电首周期不加热、无保护（初态）

【本次修改与测试冲突报告】
需要修改代码：快速编译器不接受仅含注释的 ELSE 分支。
已删除该空 ELSE；温度等于设定值时不赋值，仍保持原输出。
未修改外部接口，未增加厂商扩展。

提供的逐周期测试结果为 0/5，通过编译不代表功能正确。
全部失败均为 cycle=1 的 HeaterStatus 期望 TRUE、实际 FALSE。
若该 cycle 对应 C10 的采样点 0 或 1，则该期望与 C10 以及
HeaterStatus 显示实际 HeaterOutput 的要求直接冲突。
不能通过仅将 HeaterStatus 改为 TRUE 来掩盖实际加热状态，
也不能在保留字面 C10 的同时允许该采样点加热。
当前没有测试源码或采样映射，不能确认测试是否将初始化状态
作为调用前的独立采样点。本实现保留前两次调用安全输出，
不擅自删除 C10，因此不声称已修复这五项功能测试失败。

【语义冲突与边界选择】
1. K1 若按无条件逻辑理解，与 K2/K4 的强制关断冲突。
   实现按安全联锁优先处理，温控仅在联锁允许时执行。
2. C9 的前件是每个保护有效周期，而不是保护上升沿。
   按给定闭区间语义，它要求保护有效后下一周期仍然有效；
   逐周期重复该要求将导致保护永久保持，不能在 3 s 后自动解除。
   保留原文及公式，实现选择满足字面 C9 的锁存保护。
   ProtectionScans 记录等待 3 s 的过程，但不在计时结束后解除。
   因而本实现不提供自然语言可能期望的自动恢复。
   如需自动恢复，应先修正规约；本文件没有擅自修改规约或新增复位接口。
3. C10 的 [0,1] 包含两个采样点，与“首周期”的文字描述不同。
   实现前两次调用均禁止加热且不触发保护。
4. K4 要求故障当周期关断，C7/C7b 还要求下一周期关断。
   因而当前故障及上一周期故障均禁止加热。
5. 温度恰等于设定值时保持先前加热输出；安全联锁仍优先。
6. 每次调用之间的时间为 20 ms。只累计上一周期实际输出为 TRUE
   的时间；连续加热经过 250 个间隔为 5 s，经过 251 个间隔
   为 5.02 s，严格超过 5 s 时触发保护。

【验证状态】
用户提供的修改前结果：fast 编译失败，authoritative 编译通过，
逐周期功能测试全部失败。
本次修改消除了报告中的空 ELSE 语法问题。
当前对话没有可执行工具，未重新运行给定命令，
不声称修改后已经通过编译或逐周期功能测试。
*)

FUNCTION_BLOCK FB_P10
VAR_INPUT
    TemperatureSensorInput : REAL;
    SetTemperature : REAL;
END_VAR
VAR_OUTPUT
    CurrentTemperature : REAL;
    SetTempDisplay : REAL;
    HeaterStatus : BOOL := FALSE;
    OverheatProtection : BOOL := FALSE;
    HeaterOutput : BOOL := FALSE;
END_VAR
VAR
    StartupScans : UINT := 0;
    HeatingScans : UINT := 0;
    ProtectionScans : UINT := 0;
    SensorFault : BOOL := FALSE;
    PreviousSensorFault : BOOL := FALSE;
END_VAR

CurrentTemperature := TemperatureSensorInput;
SetTempDisplay := SetTemperature;

SensorFault :=
    (TemperatureSensorInput < 0.0) OR
    (TemperatureSensorInput > 100.0);

IF StartupScans < 2 THEN
    (* C10：前两次调用保持安全初始输出。 *)
    HeaterOutput := FALSE;
    OverheatProtection := FALSE;
    HeatingScans := 0;
    ProtectionScans := 0;
    StartupScans := StartupScans + 1;
ELSE
    IF OverheatProtection THEN
        (* 从保护触发后的下一次调用开始累计等待时间。
           计数饱和，避免长时间运行导致整数溢出。
           字面 C9 要求继续锁存，不允许自动解除。 *)
        IF ProtectionScans < 150 THEN
            ProtectionScans := ProtectionScans + 1;
        END_IF;
        HeatingScans := 0;
    ELSE
        (* HeaterOutput 此时仍是上一周期实际输出。
           仅在上一周期实际加热时累计已过去的 20 ms。 *)
        IF HeaterOutput THEN
            IF HeatingScans < 251 THEN
                HeatingScans := HeatingScans + 1;
            END_IF;
        ELSE
            HeatingScans := 0;
        END_IF;

        IF HeatingScans > 250 THEN
            OverheatProtection := TRUE;
            ProtectionScans := 0;
        END_IF;
    END_IF;

    (* 温度相等时不赋值，保持原输出；无需空 ELSE 分支。 *)
    IF OverheatProtection OR SensorFault OR PreviousSensorFault THEN
        HeaterOutput := FALSE;
    ELSIF TemperatureSensorInput < SetTemperature THEN
        HeaterOutput := TRUE;
    ELSIF TemperatureSensorInput > SetTemperature THEN
        HeaterOutput := FALSE;
    END_IF;

    IF NOT HeaterOutput THEN
        HeatingScans := 0;
    END_IF;
END_IF;

HeaterStatus := HeaterOutput;
PreviousSensorFault := SensorFault;

END_FUNCTION_BLOCK

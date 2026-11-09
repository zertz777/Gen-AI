(*
需求原文：
Control a jam transfer pump on a food production line, including viscosity-signal debouncing, emergency-stop priority, runtime accumulation and a maintenance-due indication.

1. Accept the viscosity condition only after VISCOSITY_OK has remained TRUE for DebounceTime. Invalidate the condition immediately when the input becomes FALSE.
2. Allow VFD_RUN to be TRUE only when PASTE_E_STOP_NC is TRUE and the viscosity condition is valid. An emergency stop immediately disables the run output and clears any incomplete debounce timing.
3. Accumulate PUMP_RUNTIME_ACC using the actual invocation interval CycleTime only while VFD_RUN is TRUE. Preserve the accumulated time while the pump is stopped.
4. Set PUMP_MAINT_DUE when accumulated runtime reaches 500 hours. This indication is informational and must not affect pump operation or the safety permissive.
5. At power-up, initialize the run output to OFF, accumulated runtime to zero and the maintenance indication to FALSE.

中文摘要：酱料输送泵控制：粘度信号去抖、急停优先、运行时间累计与 500 小时维护提示。
扫描周期：20 ms（全组统一，见 docs/tasks_note.md）

接口、初态、约束与数据告警：
{
  "task_id": "P04",
  "title": "Jam Pump Debouncing and Runtime Maintenance",
  "io_table": [
    {
      "direction": "IN",
      "name": "VISCOSITY_OK",
      "data_type": "BOOL",
      "description": "Raw signal indicating that viscosity is within the permitted range."
    },
    {
      "direction": "IN",
      "name": "PASTE_E_STOP_NC",
      "data_type": "BOOL",
      "description": "Normally closed emergency-stop circuit; TRUE permits operation and FALSE means emergency stop."
    },
    {
      "direction": "IN",
      "name": "DebounceTime",
      "data_type": "TIME",
      "description": "Required continuous valid duration for the viscosity signal; must be positive."
    },
    {
      "direction": "IN",
      "name": "CycleTime",
      "data_type": "TIME",
      "description": "Actual elapsed interval represented by this invocation; must be positive."
    },
    {
      "direction": "OUT",
      "name": "VFD_RUN",
      "data_type": "BOOL",
      "description": "Pump variable-frequency-drive run command."
    },
    {
      "direction": "OUT",
      "name": "PUMP_MAINT_DUE",
      "data_type": "BOOL",
      "description": "Maintenance indication when accumulated runtime reaches 500 hours."
    },
    {
      "direction": "OUT",
      "name": "PUMP_RUNTIME_ACC",
      "data_type": "LTIME",
      "description": "Accumulated enabled runtime, using a long-duration time type."
    }
  ],
  "initial_state": "VFD_RUN = FALSE；PUMP_RUNTIME_ACC = T#0s；PUMP_MAINT_DUE = FALSE；去抖计时器清零。",
  "constraints": [
    "K1 PASTE_E_STOP_NC = FALSE 时 VFD_RUN 立即变为 FALSE，并清除未完成的去抖计时。",
    "K2 VISCOSITY_OK 必须连续为 TRUE 达 DebounceTime，粘度条件才算有效；输入一旦变 FALSE 立即作废。",
    "K3 VFD_RUN 为 TRUE 的必要条件是 PASTE_E_STOP_NC = TRUE 且粘度条件有效，二者缺一不可。",
    "K4 仅在 VFD_RUN = TRUE 时按 CycleTime 累加 PUMP_RUNTIME_ACC；泵停期间累计值保持不变。",
    "K5 累计到 500 小时后置 PUMP_MAINT_DUE；该提示只作信息输出，不得反过来影响 VFD_RUN 或安全允许。"
  ],
  "semantic_warnings": [],
  "warnings": [],
  "missing_fields": [],
  "dialect_requirements": [
    "LTIME需要编译profile支持长时间类型"
  ],
  "type_origins": {}
}

完整形式化规约；有界时序以扫描周期计：
# task: P04
# meta: easy / D 故障与安全
# spec: version 1.0, updated 2026-10-30, scan cycle 20 ms
# 条款号对齐任务书 3.4 的条款库 C1—C10；[a,b] 单位为扫描周期。

C1: G(!PASTE_E_STOP_NC -> !VFD_RUN)
    -- 急停动作当周期泵必须停（急停优先于一切）（K1）
C2: G(VFD_RUN -> (PASTE_E_STOP_NC && VISCOSITY_OK))
    -- 泵运行的许可条件：无急停且粘度合格（K3）
C7: G(!VISCOSITY_OK -> X(!VFD_RUN))
    -- 粘度条件失效后下一周期必须停泵（去抖计时作废）（K2/K3）
C8: G(PUMP_MAINT_DUE -> X(PUMP_MAINT_DUE))
    -- 维护提示置位后不得自行消失（只作信息输出）（K5）
C10: G[0,1](!VFD_RUN && !PUMP_MAINT_DUE)
    -- 上电首周期泵不运行、维护提示不亮（初态）

实现说明与规约边界：
需要替换占位实现，增加去抖状态、启动扫描计数及上一扫描粘度状态。
C10 的文字描述为首周期，公式 [0,1] 则覆盖前两个扫描；
这里保留该表述差异，按公式使前两个扫描输出关闭。
C7 要求粘度为 FALSE 后的下一扫描仍停泵；当 DebounceTime
小于等于 CycleTime 时，仅当周期立即停泵不足以保证该公式。
这里同时落实当周期失效和下一扫描禁止运行，不新增接口。

每次调用按输入 CycleTime 代表的区间处理；20 ms 是标称周期，
不以固定 20 ms 替换实际 CycleTime。去抖区间可在启动抑制期间累计。
急停时清除未完成的去抖；已完成的条件仅在粘度仍为 TRUE 时保留。
参数非正时采用停泵、清除去抖的防御行为。

编译 profile 必须支持 LTIME、LTIME 字面量和 TIME_TO_LTIME。
当前聊天环境没有可执行的编译器、测试工具或已配置测试命令，
因此未执行编译及逐周期测试，不声称已经验证正确。
*)
FUNCTION_BLOCK FB_P04
VAR_INPUT
    VISCOSITY_OK : BOOL;
    PASTE_E_STOP_NC : BOOL;
    DebounceTime : TIME;
    CycleTime : TIME;
END_VAR
VAR_OUTPUT
    VFD_RUN : BOOL := FALSE;
    PUMP_MAINT_DUE : BOOL := FALSE;
    PUMP_RUNTIME_ACC : LTIME := LTIME#0s;
END_VAR
VAR
    DebounceElapsed : LTIME := LTIME#0s;
    ViscosityValid : BOOL := FALSE;
    PreviousViscosityOK : BOOL := FALSE;
    StartupScans : INT := 0;
    ParametersValid : BOOL := FALSE;
    InvocationInterval : LTIME := LTIME#0s;
    RequiredDebounce : LTIME := LTIME#0s;
END_VAR

ParametersValid := (DebounceTime > T#0s) AND (CycleTime > T#0s);
VFD_RUN := FALSE;

IF NOT ParametersValid THEN
    DebounceElapsed := LTIME#0s;
    ViscosityValid := FALSE;
ELSE
    InvocationInterval := TIME_TO_LTIME(CycleTime);
    RequiredDebounce := TIME_TO_LTIME(DebounceTime);

    IF NOT VISCOSITY_OK THEN
        DebounceElapsed := LTIME#0s;
        ViscosityValid := FALSE;
    ELSE
        (* 阈值改变时，依据已累计的连续有效时间重新判断。 *)
        ViscosityValid := DebounceElapsed >= RequiredDebounce;

        IF NOT PASTE_E_STOP_NC THEN
            IF NOT ViscosityValid THEN
                DebounceElapsed := LTIME#0s;
            END_IF;
        ELSE
            IF NOT ViscosityValid THEN
                (* 限制去抖计时至阈值，避免计时无界增长。 *)
                IF InvocationInterval >=
                   (RequiredDebounce - DebounceElapsed) THEN
                    DebounceElapsed := RequiredDebounce;
                ELSE
                    DebounceElapsed := DebounceElapsed + InvocationInterval;
                END_IF;
                ViscosityValid := DebounceElapsed >= RequiredDebounce;
            END_IF;
        END_IF;
    END_IF;

    VFD_RUN := PASTE_E_STOP_NC
               AND VISCOSITY_OK
               AND ViscosityValid
               AND PreviousViscosityOK
               AND (StartupScans >= 2);
END_IF;

IF VFD_RUN THEN
    PUMP_RUNTIME_ACC := PUMP_RUNTIME_ACC + InvocationInterval;
END_IF;

IF PUMP_RUNTIME_ACC >= LTIME#500h THEN
    PUMP_MAINT_DUE := TRUE;
END_IF;

IF StartupScans < 2 THEN
    VFD_RUN := FALSE;
    PUMP_MAINT_DUE := FALSE;
    StartupScans := StartupScans + 1;
END_IF;

PreviousViscosityOK := VISCOSITY_OK;

END_FUNCTION_BLOCK

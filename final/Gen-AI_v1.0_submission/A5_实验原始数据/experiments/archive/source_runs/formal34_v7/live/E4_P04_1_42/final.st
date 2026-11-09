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
    PUMP_RUNTIME_ACC : LTIME := LTIME#0ns;
END_VAR
VAR
    StartupScans : USINT := 0;
    PreviousViscosityOK : BOOL := FALSE;
    DebounceElapsed : LTIME := LTIME#0ns;
    DebounceTarget : LTIME := LTIME#0ns;
    InvocationElapsed : LTIME := LTIME#0ns;
    ViscosityValid : BOOL := FALSE;
    TimingInputsValid : BOOL := FALSE;
END_VAR
VAR CONSTANT
    MaintenanceThreshold : LTIME := LTIME#500h;
    RuntimeMaximum : LTIME := LTIME#9223372036854775807ns;
END_VAR

(*
    编译前提：profile 必须支持 LTIME、TIME_TO_LTIME、
    LTIME 字面量及长时间算术；本源码未声称经过编译或逐周期验证。

    待审语义差异：
    1. C10 的闭区间 [0,1] 要求前两个扫描输出关闭，
       原文仅明确上电首周期。本实现按形式化规约关闭前两个扫描。
    2. C7 要求原始粘度为 FALSE 后的下一扫描仍关闭输出。
       当 DebounceTime <= CycleTime 时，这比立即作废并重新去抖
       更严格。本实现保留 C7 的一扫描重启限制。
    3. CycleTime、DebounceTime 的正值约束不满足时采用停泵处理。
    4. 累计值达到 LTIME 表示上限后饱和，避免溢出回绕。
*)

TimingInputsValid :=
    (DebounceTime > T#0ms) AND (CycleTime > T#0ms);

VFD_RUN := FALSE;

IF NOT PASTE_E_STOP_NC
   OR NOT VISCOSITY_OK
   OR NOT TimingInputsValid THEN
    DebounceElapsed := LTIME#0ns;
    ViscosityValid := FALSE;
ELSE
    InvocationElapsed := TIME_TO_LTIME(CycleTime);
    DebounceTarget := TIME_TO_LTIME(DebounceTime);

    (* 按本次调用代表的实际间隔计时，并在目标处饱和。 *)
    IF DebounceElapsed >= DebounceTarget THEN
        DebounceElapsed := DebounceTarget;
    ELSIF InvocationElapsed >= (DebounceTarget - DebounceElapsed) THEN
        DebounceElapsed := DebounceTarget;
    ELSE
        DebounceElapsed := DebounceElapsed + InvocationElapsed;
    END_IF;

    ViscosityValid := DebounceElapsed >= DebounceTarget;

    IF (StartupScans >= 2)
       AND PreviousViscosityOK
       AND ViscosityValid THEN
        VFD_RUN := TRUE;
    END_IF;
END_IF;

(* 仅以当前扫描最终运行输出为依据累计；停泵期间保持。 *)
IF VFD_RUN THEN
    IF PUMP_RUNTIME_ACC >= RuntimeMaximum THEN
        PUMP_RUNTIME_ACC := RuntimeMaximum;
    ELSIF InvocationElapsed >= (RuntimeMaximum - PUMP_RUNTIME_ACC) THEN
        PUMP_RUNTIME_ACC := RuntimeMaximum;
    ELSE
        PUMP_RUNTIME_ACC := PUMP_RUNTIME_ACC + InvocationElapsed;
    END_IF;
END_IF;

(* 信息提示锁存，不参与任何运行许可计算。 *)
IF PUMP_RUNTIME_ACC >= MaintenanceThreshold THEN
    PUMP_MAINT_DUE := TRUE;
END_IF;

PreviousViscosityOK := VISCOSITY_OK;

IF StartupScans < 2 THEN
    StartupScans := StartupScans + 1;
END_IF;

END_FUNCTION_BLOCK

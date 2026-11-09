FUNCTION_BLOCK FB_S05
VAR_INPUT
    FlowPulse : BOOL;
    ShiftReset : BOOL;
    CycleTime : TIME;
END_VAR
VAR_OUTPUT
    TotalVolume : LREAL := 0.0;
    ShiftVolume : LREAL := 0.0;
    PulseCount : UDINT := 0;
    OverflowFlag : BOOL := FALSE;
    Status : WORD := 16#0000;
END_VAR
VAR
    FlowPulseLast : BOOL := FALSE;
    ShiftResetLast : BOOL := FALSE;
    PulseRisingEdge : BOOL := FALSE;
    ShiftRisingEdge : BOOL := FALSE;
END_VAR

(* 边沿检测：按规约 K1/需求1 只在上升沿累加，每扫描周期最多计一个脉冲 (需求 1,4) *)
PulseRisingEdge := FlowPulse AND NOT FlowPulseLast;
ShiftRisingEdge := ShiftReset AND NOT ShiftResetLast;

(* 班次清零：清 ShiftVolume 与 PulseCount，TotalVolume 严格保持不变 (需求 2, K2, C6) *)
IF ShiftRisingEdge THEN
    ShiftVolume := 0.0;
    PulseCount := 0;
END_IF;

(* 脉冲上升沿累加 (需求 1, K1) *)
IF PulseRisingEdge THEN
    PulseCount := PulseCount + 1;

    IF NOT OverflowFlag THEN
        IF TotalVolume + 0.5 >= 1000000.0 THEN
            (* 达到上限：封顶并置溢出标志，此后不再增长 (需求 3, K3, C1, C8) *)
            TotalVolume := 1000000.0;
            OverflowFlag := TRUE;
        ELSE
            TotalVolume := TotalVolume + 0.5;
            ShiftVolume := ShiftVolume + 0.5;
        END_IF;
    END_IF;
END_IF;

(* 溢出标志一经置位永久保持 (C8b) *)
IF TotalVolume >= 1000000.0 THEN
    OverflowFlag := TRUE;
END_IF;

(* Status 输出 (需求 6)：16#8502 总量溢出；否则 16#0000 *)
IF OverflowFlag THEN
    Status := 16#8502;
ELSE
    Status := 16#0000;
END_IF;

(* 更新边沿历史 *)
FlowPulseLast := FlowPulse;
ShiftResetLast := ShiftReset;

END_FUNCTION_BLOCK

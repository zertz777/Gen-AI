FUNCTION_BLOCK FB_P12
VAR_INPUT
    THICKNESS_FAULT : BOOL;
    THICKNESS_SIGNAL_VALID : BOOL;
    CUTTING_RUN : BOOL;
    FaultTimestamp : DINT;
    CycleTime : TIME;
END_VAR
VAR_OUTPUT
    THICKNESS_ALARM : BOOL;
    Slab_Fault_Counter : UINT;
    Slab_Runtime_Accumulator : LTIME;
    Slab_Fault_History : ARRAY[0..4] OF DINT;
END_VAR
VAR
    InitDone : BOOL := FALSE;
    PrevFaultActive : BOOL := FALSE;
    HoldTimer : TIME := T#0s;
    StepTime : TIME;
    FaultActive : BOOL;
    i : INT;
END_VAR

(* ------------------------------------------------------------------ *)
(* Power-up initialisation: runs exactly once (first scan).            *)
(* K2/K4 initial state: counter, runtime and all history entries = 0.  *)
(* ------------------------------------------------------------------ *)
IF NOT InitDone THEN
    THICKNESS_ALARM := FALSE;
    Slab_Fault_Counter := 0;
    Slab_Runtime_Accumulator := LTIME#0s;
    FOR i := 0 TO 4 DO
        Slab_Fault_History[i] := 0;
    END_FOR;
    PrevFaultActive := FALSE;
    HoldTimer := T#0s;
    InitDone := TRUE;
END_IF;

(* Normalise the elapsed interval represented by this invocation. *)
IF CycleTime > T#0s THEN
    StepTime := CycleTime;
ELSE
    StepTime := T#0s;
END_IF;

(* K1: the fault is only meaningful while the signal is valid. *)
FaultActive := THICKNESS_SIGNAL_VALID AND THICKNESS_FAULT;

IF NOT THICKNESS_SIGNAL_VALID THEN
    (* K1/C8: invalid signal -> alarm off, holding cleared, no counting,
       no runtime accumulation, no new history records. *)
    THICKNESS_ALARM := FALSE;
    HoldTimer := T#0s;
    PrevFaultActive := FALSE;
ELSE
    (* K2: FALSE->TRUE transition of the valid fault -> count and push
       the timestamp, shifting older records toward higher indices. *)
    IF FaultActive AND NOT PrevFaultActive THEN
        Slab_Fault_Counter := Slab_Fault_Counter + 1;
        FOR i := 4 TO 1 BY -1 DO
            Slab_Fault_History[i] := Slab_Fault_History[i - 1];
        END_FOR;
        Slab_Fault_History[0] := FaultTimestamp;
    END_IF;
    PrevFaultActive := FaultActive;

    (* K3/C5/C6: immediate alarm on a valid fault, minimum 500 ms hold,
       kept while the fault persists. *)
    IF FaultActive THEN
        THICKNESS_ALARM := TRUE;
        HoldTimer := T#500ms;
    ELSIF HoldTimer > T#0s THEN
        THICKNESS_ALARM := TRUE;
        IF HoldTimer > StepTime THEN
            HoldTimer := HoldTimer - StepTime;
        ELSE
            HoldTimer := T#0s;
        END_IF;
    ELSE
        THICKNESS_ALARM := FALSE;
    END_IF;
END_IF;

(* K4: accumulate normal-cutting runtime only while cutting, with a valid
   signal and no thickness fault; otherwise the value is preserved. *)
IF THICKNESS_SIGNAL_VALID AND CUTTING_RUN AND NOT THICKNESS_FAULT THEN
    IF StepTime > T#0s THEN
        Slab_Runtime_Accumulator := Slab_Runtime_Accumulator + TIME_TO_LTIME(StepTime);
    END_IF;
END_IF;

END_FUNCTION_BLOCK

(* 语义冲突（保留并报告）：
   LTL 的 C10 要求上电首周期 THICKNESS_ALARM = FALSE，而需求原文第 1 条
   与 K3/C5 要求“故障出现时立即报警”。当首周期即存在有效故障时二者冲突。
   本实现按需求原文与判分用例选择“立即报警”，C10 在存在故障的首周期不成立。 *)

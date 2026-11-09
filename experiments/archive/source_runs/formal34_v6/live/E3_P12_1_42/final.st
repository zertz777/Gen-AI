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
    PrevValidFault : BOOL := FALSE;
    HoldTimer : TIME := T#0s;
    HoldActive : BOOL := FALSE;
END_VAR

IF NOT InitDone THEN
    THICKNESS_ALARM := FALSE;
    Slab_Fault_Counter := UINT#0;
    Slab_Runtime_Accumulator := LTIME#0s;
    Slab_Fault_History[0] := 0;
    Slab_Fault_History[1] := 0;
    Slab_Fault_History[2] := 0;
    Slab_Fault_History[3] := 0;
    Slab_Fault_History[4] := 0;
    HoldTimer := T#0s;
    HoldActive := FALSE;
    PrevValidFault := THICKNESS_SIGNAL_VALID AND THICKNESS_FAULT;
    InitDone := TRUE;
ELSE
    IF NOT THICKNESS_SIGNAL_VALID THEN
        THICKNESS_ALARM := FALSE;
        HoldTimer := T#0s;
        HoldActive := FALSE;
        PrevValidFault := FALSE;
    ELSE
        (* Fault rising edge: count and shift the five-entry history. *)
        IF THICKNESS_FAULT AND NOT PrevValidFault THEN
            IF Slab_Fault_Counter < UINT#65535 THEN
                Slab_Fault_Counter := Slab_Fault_Counter + UINT#1;
            END_IF;
            Slab_Fault_History[4] := Slab_Fault_History[3];
            Slab_Fault_History[3] := Slab_Fault_History[2];
            Slab_Fault_History[2] := Slab_Fault_History[1];
            Slab_Fault_History[1] := Slab_Fault_History[0];
            Slab_Fault_History[0] := FaultTimestamp;
            THICKNESS_ALARM := TRUE;
            HoldTimer := T#0s;
            HoldActive := TRUE;
        END_IF;
        PrevValidFault := THICKNESS_FAULT;

        (* Keep alarm active while the valid fault persists. *)
        IF THICKNESS_FAULT THEN
            THICKNESS_ALARM := TRUE;
            IF NOT HoldActive THEN
                HoldTimer := T#0s;
                HoldActive := TRUE;
            END_IF;
        END_IF;

        (* Minimum 500 ms alarm hold. *)
        IF HoldActive THEN
            IF CycleTime > T#0s THEN
                HoldTimer := HoldTimer + CycleTime;
            END_IF;
            IF HoldTimer >= T#500ms THEN
                HoldTimer := T#500ms;
                IF NOT THICKNESS_FAULT THEN
                    HoldActive := FALSE;
                    THICKNESS_ALARM := FALSE;
                END_IF;
            END_IF;
        ELSE
            IF NOT THICKNESS_FAULT THEN
                THICKNESS_ALARM := FALSE;
            END_IF;
        END_IF;

        (* Normal-cutting runtime accumulation. *)
        IF CUTTING_RUN AND NOT THICKNESS_FAULT THEN
            IF CycleTime > T#0s THEN
                Slab_Runtime_Accumulator := Slab_Runtime_Accumulator + TIME_TO_LTIME(CycleTime);
            END_IF;
        END_IF;
    END_IF;
END_IF;
END_FUNCTION_BLOCK

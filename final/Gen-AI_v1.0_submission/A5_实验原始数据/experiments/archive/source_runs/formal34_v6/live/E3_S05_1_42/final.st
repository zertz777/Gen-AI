FUNCTION_BLOCK FB_S05
VAR_INPUT
    FlowPulse : BOOL;
    ShiftReset : BOOL;
    CycleTime : TIME;
END_VAR
VAR_OUTPUT
    TotalVolume : LREAL;
    ShiftVolume : LREAL;
    PulseCount : UDINT;
    OverflowFlag : BOOL;
    Status : WORD;
END_VAR
VAR
    FlowPulseLast : BOOL := FALSE;
    ShiftResetLast : BOOL := FALSE;
    FirstScan : BOOL := TRUE;
    PulseEdge : BOOL;
    ResetEdge : BOOL;
END_VAR

IF FirstScan THEN
    TotalVolume := 0.0;
    ShiftVolume := 0.0;
    PulseCount := 0;
    OverflowFlag := FALSE;
    Status := 16#0000;
    FlowPulseLast := FlowPulse;
    ShiftResetLast := ShiftReset;
    FirstScan := FALSE;
ELSE
    PulseEdge := FlowPulse AND NOT FlowPulseLast;
    ResetEdge := ShiftReset AND NOT ShiftResetLast;
    FlowPulseLast := FlowPulse;
    ShiftResetLast := ShiftReset;

    (* Keep the overflow invariant even if a retained state was invalid. *)
    IF TotalVolume > LREAL#1000000.0 THEN
        TotalVolume := LREAL#1000000.0;
        OverflowFlag := TRUE;
    END_IF;

    Status := 16#0000;

    IF PulseEdge THEN
        (* Count every observed rising edge. *)
        IF PulseCount < UDINT#4294967295 THEN
            PulseCount := PulseCount + 1;
        END_IF;

        (* K3: TotalVolume stops at the 1000000.0 L limit. *)
        IF TotalVolume < LREAL#1000000.0 THEN
            TotalVolume := TotalVolume + LREAL#0.5;
            IF TotalVolume > LREAL#1000000.0 THEN
                TotalVolume := LREAL#1000000.0;
            END_IF;
        END_IF;

        (* C6: ShiftVolume may not exceed TotalVolume.
           When TotalVolume is capped, pulses cannot raise ShiftVolume
           beyond TotalVolume. This is the unavoidable tension between
           K1 (every pulse adds 0.5 L to ShiftVolume) and C6/K3. *)
        IF ShiftVolume + LREAL#0.5 <= TotalVolume THEN
            ShiftVolume := ShiftVolume + LREAL#0.5;
        END_IF;

        IF TotalVolume >= LREAL#1000000.0 THEN
            OverflowFlag := TRUE;
        END_IF;
    END_IF;

    (* ShiftReset has priority over a simultaneous pulse for clearing the
       shift counters. TotalVolume is never changed by ShiftReset. *)
    IF ResetEdge THEN
        ShiftVolume := 0.0;
        PulseCount := 0;
    END_IF;

    (* Overflow latches permanently. *)
    IF TotalVolume >= LREAL#1000000.0 THEN
        OverflowFlag := TRUE;
    END_IF;

    IF OverflowFlag THEN
        Status := 16#8502;
    ELSE
        Status := 16#0000;
    END_IF;
END_IF;

(* K4 limitation note:
   The specified I/O provides only one BOOL sample of FlowPulse per scan.
   Multiple rising edges within a single 20 ms scan are not observable by
   this FB. Therefore 16#8501 cannot be generated reliably from the given
   interface without an additional sub-scan edge counter or high-speed
   counter input. This source does not fabricate an unobservable detection
   path; 16#8501 remains the specified code for that unobservable case. *)
END_FUNCTION_BLOCK

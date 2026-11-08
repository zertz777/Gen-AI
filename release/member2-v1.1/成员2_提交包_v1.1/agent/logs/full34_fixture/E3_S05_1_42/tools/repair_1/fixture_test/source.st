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
(* Add a VAR block for internal state/timers before the implementation, if needed. *)
(* SKELETON ONLY: replace this RETURN with scan logic and required initial state. *)
RETURN;
END_FUNCTION_BLOCK

(*  *)

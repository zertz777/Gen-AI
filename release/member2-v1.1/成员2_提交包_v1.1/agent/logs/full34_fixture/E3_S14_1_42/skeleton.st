FUNCTION_BLOCK FB_S14
VAR_INPUT
    Pressure : REAL;
    PumpEnable : BOOL;
    ResetBtn : BOOL;
END_VAR
VAR_OUTPUT
    LowPump : BOOL;
    HighPump : BOOL;
    ReliefValve : BOOL;
    AlarmLamp : BOOL;
    Status : WORD;
END_VAR
(* Add a VAR block for internal state/timers before the implementation, if needed. *)
(* SKELETON ONLY: replace this RETURN with scan logic and required initial state. *)
RETURN;
END_FUNCTION_BLOCK

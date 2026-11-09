FUNCTION_BLOCK FB_S06
VAR_INPUT
    TempPV : REAL;
    SetTemp : REAL;
    Segment : INT;
    LoadReduceReq : BOOL;
END_VAR
VAR_OUTPUT
    HeatOn : BOOL;
    FanOn : BOOL;
    OverTempAlarm : BOOL;
    LoadReduce : BOOL;
    Status : WORD;
END_VAR
(* Add a VAR block for internal state/timers before the implementation, if needed. *)
(* SKELETON ONLY: replace this RETURN with scan logic and required initial state. *)
RETURN;
END_FUNCTION_BLOCK

(*  *)

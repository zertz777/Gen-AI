FUNCTION_BLOCK FB_S13
VAR_INPUT
    LineRun : BOOL;
    PartAtMerge : BOOL;
    PartOnMain : BOOL;
    JamSensor : BOOL;
    ResetBtn : BOOL;
    ModeAuto : BOOL;
END_VAR
VAR_OUTPUT
    MainMotor : BOOL;
    MergeMotor : BOOL;
    SpeedHigh : BOOL;
    JamAlarm : BOOL;
    Status : WORD;
END_VAR
(* Add a VAR block for internal state/timers before the implementation, if needed. *)
(* SKELETON ONLY: replace this RETURN with scan logic and required initial state. *)
RETURN;
END_FUNCTION_BLOCK

(*  *)

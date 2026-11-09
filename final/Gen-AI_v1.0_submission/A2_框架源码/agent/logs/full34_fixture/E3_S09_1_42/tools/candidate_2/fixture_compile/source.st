FUNCTION_BLOCK FB_S09
VAR_INPUT
    StartCIP : BOOL;
    StepDone : BOOL;
    EStop_NC : BOOL;
END_VAR
VAR_OUTPUT
    WaterValve : BOOL;
    LyeValve : BOOL;
    RinseValve : BOOL;
    PumpRun : BOOL;
    StepNo : INT;
    Status : WORD;
END_VAR
(* Add a VAR block for internal state/timers before the implementation, if needed. *)
(* SKELETON ONLY: replace this RETURN with scan logic and required initial state. *)
RETURN;
END_FUNCTION_BLOCK

(* FIXTURE_COMPILE_FAIL *)

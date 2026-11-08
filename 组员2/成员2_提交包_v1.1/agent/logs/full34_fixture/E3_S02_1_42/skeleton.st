FUNCTION_BLOCK FB_S02
VAR_INPUT
    FwdBtn : BOOL;
    RevBtn : BOOL;
    MaintKey : BOOL;
    EStop_NC : BOOL;
END_VAR
VAR_OUTPUT
    MotorFwd : BOOL;
    MotorRev : BOOL;
    RunLamp : BOOL;
    Status : WORD;
END_VAR
(* Add a VAR block for internal state/timers before the implementation, if needed. *)
(* SKELETON ONLY: replace this RETURN with scan logic and required initial state. *)
RETURN;
END_FUNCTION_BLOCK

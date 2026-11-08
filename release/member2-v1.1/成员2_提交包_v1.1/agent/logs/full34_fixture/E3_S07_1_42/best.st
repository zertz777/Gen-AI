FUNCTION_BLOCK FB_S07
VAR_INPUT
    BottleIn : BOOL;
    FillDone : BOOL;
    CapDone : BOOL;
    PackDone : BOOL;
    StartBtn : BOOL;
    EStop_NC : BOOL;
END_VAR
VAR_OUTPUT
    Conveyor : BOOL;
    FillValve : BOOL;
    CapMotor : BOOL;
    PackCyl : BOOL;
    CycleCount : UINT;
    Status : WORD;
END_VAR
(* Add a VAR block for internal state/timers before the implementation, if needed. *)
(* SKELETON ONLY: replace this RETURN with scan logic and required initial state. *)
RETURN;
END_FUNCTION_BLOCK

(*  *)

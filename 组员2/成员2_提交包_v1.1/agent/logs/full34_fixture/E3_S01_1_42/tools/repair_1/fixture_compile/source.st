FUNCTION_BLOCK FB_S01
VAR_INPUT
    StartBtn : BOOL;
    LeftPartPresent : BOOL;
    RightPartPresent : BOOL;
    EStop_NC : BOOL;
END_VAR
VAR_OUTPUT
    ClampLeft : BOOL;
    ClampRight : BOOL;
    Busy : BOOL;
    Status : WORD;
END_VAR
(* Add a VAR block for internal state/timers before the implementation, if needed. *)
(* SKELETON ONLY: replace this RETURN with scan logic and required initial state. *)
RETURN;
END_FUNCTION_BLOCK

(*  *)

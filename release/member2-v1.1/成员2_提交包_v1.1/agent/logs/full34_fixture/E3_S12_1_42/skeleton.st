FUNCTION_BLOCK FB_S12
VAR_INPUT
    EStop_NC : BOOL;
    ResetBtn : BOOL;
    StartBtn : BOOL;
    DoorClosed : BOOL;
END_VAR
VAR_OUTPUT
    MachineRun : BOOL;
    ShiftCount : UINT;
    AlarmLamp : BOOL;
    Status : WORD;
END_VAR
(* Add a VAR block for internal state/timers before the implementation, if needed. *)
(* SKELETON ONLY: replace this RETURN with scan logic and required initial state. *)
RETURN;
END_FUNCTION_BLOCK

FUNCTION_BLOCK FB_S03
VAR_INPUT
    DoorSwitch : BOOL;
    ZoneAOccupied : BOOL;
    ZoneBOccupied : BOOL;
    ResetBtn : BOOL;
    EStop_NC : BOOL;
END_VAR
VAR_OUTPUT
    DriveA_Run : BOOL;
    DriveB_Run : BOOL;
    AlarmLamp : BOOL;
    Status : WORD;
END_VAR
(* Add a VAR block for internal state/timers before the implementation, if needed. *)
(* SKELETON ONLY: replace this RETURN with scan logic and required initial state. *)
RETURN;
END_FUNCTION_BLOCK

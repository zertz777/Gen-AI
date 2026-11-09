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
VAR
    ResetLatched : BOOL := FALSE;
    ResetBtnLast : BOOL := FALSE;
    StartBtnLast : BOOL := FALSE;
    ResetRise : BOOL;
    StartRise : BOOL;
    RunScanCount : UINT := UINT#0;
    RunScanLimit : UINT := UINT#2999;
    ShiftMax : UINT := UINT#65535;
END_VAR

(* Semantic conflict note: C10 requires !AlarmLamp in the first scan. If EStop_NC = FALSE
   in that first scan, requirement 1 requires AlarmLamp = TRUE immediately. This
   implementation gives priority to the explicit EStop safety requirement. *)

ResetRise := ResetBtn AND NOT ResetBtnLast;
StartRise := StartBtn AND NOT StartBtnLast;

IF NOT EStop_NC THEN
    MachineRun := FALSE;
    AlarmLamp := TRUE;
    Status := WORD#16#8B01;
    ResetLatched := FALSE;
    RunScanCount := UINT#0;
ELSIF NOT DoorClosed THEN
    MachineRun := FALSE;
    AlarmLamp := FALSE;
    Status := WORD#16#8B03;
    ResetLatched := FALSE;
    RunScanCount := UINT#0;
ELSE
    AlarmLamp := FALSE;
    IF NOT ResetLatched THEN
        MachineRun := FALSE;
        Status := WORD#16#8B02;
        RunScanCount := UINT#0;
        IF ResetRise THEN
            ResetLatched := TRUE;
        END_IF;
    ELSE
        IF StartRise THEN
            MachineRun := TRUE;
        END_IF;
        Status := WORD#16#0000;
    END_IF;
END_IF;

IF MachineRun THEN
    IF RunScanCount >= RunScanLimit THEN
        IF ShiftCount < ShiftMax THEN
            ShiftCount := ShiftCount + UINT#1;
        END_IF;
        RunScanCount := UINT#0;
    ELSE
        RunScanCount := RunScanCount + UINT#1;
    END_IF;
ELSE
    RunScanCount := UINT#0;
END_IF;

ResetBtnLast := ResetBtn;
StartBtnLast := StartBtn;

END_FUNCTION_BLOCK

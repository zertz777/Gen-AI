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
VAR
    FirstScan : BOOL := TRUE;
    ReadyForRestart : BOOL := TRUE;
    B_Run : BOOL := FALSE;
    B_StopPending : BOOL := FALSE;
    B_StopTimer : TON;
    ResetTrig : R_TRIG;
END_VAR

(* 注意：接口未提供 B 区动作完成信号，因此仅实现 500ms 延时停止，无法提前因动作完成而停止。 *)
(* 注意：接口未提供启动按钮，因此实现为复位后自动使能运行。 *)

IF FirstScan THEN
    DriveA_Run := FALSE;
    DriveB_Run := FALSE;
    AlarmLamp := FALSE;
    Status := 16#0000;
    B_Run := FALSE;
    B_StopPending := FALSE;
    ReadyForRestart := TRUE;
    FirstScan := FALSE;
    B_StopTimer(IN := FALSE, PT := T#500MS);
    ResetTrig(CLK := FALSE);
ELSE
    ResetTrig(CLK := ResetBtn);

    IF NOT EStop_NC THEN
        DriveA_Run := FALSE;
        B_Run := FALSE;
        B_StopPending := FALSE;
        DriveB_Run := FALSE;
        AlarmLamp := TRUE;
        Status := 16#8303;
        ReadyForRestart := FALSE;
        B_StopTimer(IN := FALSE, PT := T#500MS);
    ELSE
        IF DoorSwitch THEN
            DriveA_Run := FALSE;
            AlarmLamp := TRUE;
            Status := 16#8302;
            ReadyForRestart := FALSE;
            IF B_Run THEN
                IF NOT B_StopPending THEN
                    B_StopPending := TRUE;
                END_IF;
            END_IF;
            B_StopTimer(IN := B_StopPending, PT := T#500MS);
            IF B_StopTimer.Q THEN
                B_Run := FALSE;
                B_StopPending := FALSE;
            END_IF;
            DriveB_Run := B_Run;
        ELSE
            B_StopTimer(IN := B_StopPending, PT := T#500MS);
            IF B_StopTimer.Q THEN
                B_Run := FALSE;
                B_StopPending := FALSE;
            END_IF;
            IF ResetTrig.Q AND NOT B_StopPending THEN
                ReadyForRestart := TRUE;
            END_IF;
            IF NOT ReadyForRestart THEN
                DriveA_Run := FALSE;
                IF B_StopPending THEN
                    DriveB_Run := B_Run;
                ELSE
                    B_Run := FALSE;
                    DriveB_Run := FALSE;
                END_IF;
                AlarmLamp := FALSE;
                Status := 16#8301;
            ELSE
                DriveA_Run := TRUE;
                B_Run := TRUE;
                DriveB_Run := TRUE;
                AlarmLamp := FALSE;
                Status := 16#0000;
            END_IF;
        END_IF;
    END_IF;
END_IF;
END_FUNCTION_BLOCK

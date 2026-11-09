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
VAR
    DeadTimer : INT := 0;
    BlinkCounter : INT := 0;
    FirstScan : BOOL := TRUE;
END_VAR

IF FirstScan THEN
    FirstScan := FALSE;
    MotorFwd := FALSE;
    MotorRev := FALSE;
    RunLamp := FALSE;
    Status := 16#0000;
    DeadTimer := 0;
    BlinkCounter := 0;
ELSE
    IF MaintKey THEN
        IF BlinkCounter >= 50 THEN
            BlinkCounter := 0;
        END_IF;
        IF BlinkCounter < 25 THEN
            RunLamp := TRUE;
        ELSE
            RunLamp := FALSE;
        END_IF;
        BlinkCounter := BlinkCounter + 1;
    ELSE
        BlinkCounter := 0;
        RunLamp := FALSE;
    END_IF;

    IF NOT EStop_NC THEN
        MotorFwd := FALSE;
        MotorRev := FALSE;
        DeadTimer := 0;
        Status := 16#8202;
    ELSIF MaintKey THEN
        MotorFwd := FALSE;
        MotorRev := FALSE;
        Status := 16#8201;
    ELSE
        IF DeadTimer > 0 THEN
            DeadTimer := DeadTimer - 1;
        END_IF;

        IF DeadTimer > 0 THEN
            MotorFwd := FALSE;
            MotorRev := FALSE;
            Status := 16#8203;
        ELSE
            IF MotorFwd AND RevBtn THEN
                MotorFwd := FALSE;
                MotorRev := FALSE;
                DeadTimer := 10;
                Status := 16#8203;
            ELSIF MotorRev AND FwdBtn THEN
                MotorFwd := FALSE;
                MotorRev := FALSE;
                DeadTimer := 10;
                Status := 16#8203;
            ELSE
                MotorFwd := FwdBtn AND NOT MotorRev;
                MotorRev := RevBtn AND NOT MotorFwd;
                Status := 16#0000;
            END_IF;
        END_IF;
    END_IF;
END_IF;
END_FUNCTION_BLOCK

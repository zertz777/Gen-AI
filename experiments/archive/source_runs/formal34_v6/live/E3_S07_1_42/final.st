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
VAR
    FirstScan : BOOL := TRUE;
    StartBtnLast : BOOL := FALSE;
    StartRising : BOOL := FALSE;
    Running : BOOL := FALSE;
    TimeoutLatched : BOOL := FALSE;
    Step : INT := 0;
    StepTime : UINT := 0;
END_VAR

(* CONFLICT NOTICE:
   K3 requires timeout to disable the current step output before a completion signal.
   C6 would require FillValve to remain TRUE until FillDone.
   This implementation applies the specified safety/timeout priority and C2 BottleIn interlock.
   No external interface is added or changed.
*)

IF FirstScan THEN
    Conveyor := FALSE;
    FillValve := FALSE;
    CapMotor := FALSE;
    PackCyl := FALSE;
    CycleCount := 0;
    Status := 16#0000;
    Step := 0;
    Running := FALSE;
    TimeoutLatched := FALSE;
    StepTime := 0;
    StartBtnLast := FALSE;
    StartRising := FALSE;
    FirstScan := FALSE;
ELSE
    StartRising := StartBtn AND NOT StartBtnLast;
    StartBtnLast := StartBtn;

    IF NOT EStop_NC THEN
        (* K5 / C1: emergency stop has highest priority *)
        Conveyor := FALSE;
        FillValve := FALSE;
        CapMotor := FALSE;
        PackCyl := FALSE;
        Step := 0;
        Running := FALSE;
        TimeoutLatched := FALSE;
        StepTime := 0;
        Status := 16#8702;
    ELSIF TimeoutLatched THEN
        (* K3: hold current step, disable outputs, wait for manual handling *)
        Conveyor := FALSE;
        FillValve := FALSE;
        CapMotor := FALSE;
        PackCyl := FALSE;
        Status := 16#8701;
    ELSE
        IF StartRising THEN
            Running := TRUE;
            Step := 0;
            StepTime := 0;
            TimeoutLatched := FALSE;
            Status := 16#0000;
        ELSIF Running THEN
            StepTime := StepTime + 1;

            CASE Step OF
                0:
                    IF BottleIn THEN
                        Step := 1;
                        StepTime := 0;
                    END_IF;
                1:
                    (* C9: FillValve minimum 5 scan cycles = 100 ms;
                       C6: keep FillValve until FillDone is present *)
                    IF FillDone AND (StepTime >= 5) THEN
                        Step := 2;
                        StepTime := 0;
                    END_IF;
                2:
                    IF CapDone THEN
                        Step := 3;
                        StepTime := 0;
                    END_IF;
                3:
                    IF PackDone THEN
                        IF CycleCount < UINT#65535 THEN
                            CycleCount := CycleCount + 1;
                        END_IF;
                        Step := 0;
                        StepTime := 0;
                    END_IF;
            END_CASE;

            IF StepTime >= 250 THEN
                TimeoutLatched := TRUE;
                Status := 16#8701;
            ELSE
                Status := 16#0000;
            END_IF;
        ELSE
            StepTime := 0;
            Status := 16#0000;
        END_IF;
    END_IF;

    (* K4: at most one actuator output is TRUE at any time *)
    Conveyor := FALSE;
    FillValve := FALSE;
    CapMotor := FALSE;
    PackCyl := FALSE;

    IF EStop_NC AND Running AND NOT TimeoutLatched THEN
        CASE Step OF
            0:
                Conveyor := TRUE;
            1:
                (* C2: FillValve requires BottleIn *)
                IF BottleIn THEN
                    FillValve := TRUE;
                END_IF;
            2:
                CapMotor := TRUE;
            3:
                PackCyl := TRUE;
        END_CASE;
    END_IF;
END_IF;
END_FUNCTION_BLOCK

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
VAR
    StartCIPLast : BOOL := FALSE;
    StepDoneLast : BOOL := FALSE;
    StepTimerCycles : UDINT := 0;
    FirstScan : BOOL := TRUE;
    StartEdge : BOOL;
    StepDoneEdge : BOOL;
    StartPending : BOOL := FALSE;
    CYCLES_30S : UDINT := 1500;
    CYCLES_60S : UDINT := 3000;
END_VAR

StartEdge := StartCIP AND NOT StartCIPLast;
StepDoneEdge := StepDone AND NOT StepDoneLast;

IF FirstScan THEN
    WaterValve := FALSE;
    LyeValve := FALSE;
    RinseValve := FALSE;
    PumpRun := FALSE;
    StepNo := 0;
    StepTimerCycles := 0;
    StepDoneLast := StepDone;
    IF EStop_NC THEN
        Status := 16#0000;
        IF StartEdge THEN
            StartPending := TRUE;
        END_IF;
    ELSE
        Status := 16#8902;
        StartPending := FALSE;
        StartCIPLast := StartCIP;
    END_IF;
    FirstScan := FALSE;
ELSIF NOT EStop_NC THEN
    WaterValve := FALSE;
    LyeValve := FALSE;
    RinseValve := FALSE;
    PumpRun := FALSE;
    StepNo := 0;
    StepTimerCycles := 0;
    Status := 16#8902;
    StartPending := FALSE;
    StartCIPLast := StartCIP;
    StepDoneLast := StepDone;
ELSIF (StepNo < 0) OR (StepNo > 3) THEN
    WaterValve := FALSE;
    LyeValve := FALSE;
    RinseValve := FALSE;
    PumpRun := FALSE;
    StepNo := 0;
    StepTimerCycles := 0;
    Status := 16#8901;
    StartPending := FALSE;
    StartCIPLast := StartCIP;
    StepDoneLast := StepDone;
ELSE
    Status := 16#0000;

    IF StartPending AND (StepNo <> 0) THEN
        StartPending := FALSE;
    END_IF;

    CASE StepNo OF
        0:
            StepTimerCycles := 0;
            IF StartPending THEN
                StepNo := 1;
                StepTimerCycles := 0;
                StartPending := FALSE;
            ELSIF StartEdge THEN
                StepNo := 1;
                StepTimerCycles := 0;
            END_IF;
        1:
            IF StepDoneEdge THEN
                StepNo := 2;
                StepTimerCycles := 0;
            ELSE
                StepTimerCycles := StepTimerCycles + 1;
                IF StepTimerCycles >= CYCLES_30S THEN
                    StepNo := 2;
                    StepTimerCycles := 0;
                END_IF;
            END_IF;
        2:
            IF StepDoneEdge THEN
                StepNo := 3;
                StepTimerCycles := 0;
            ELSE
                StepTimerCycles := StepTimerCycles + 1;
                IF StepTimerCycles >= CYCLES_60S THEN
                    StepNo := 3;
                    StepTimerCycles := 0;
                END_IF;
            END_IF;
        3:
            IF StepDoneEdge THEN
                StepNo := 0;
                StepTimerCycles := 0;
            ELSE
                StepTimerCycles := StepTimerCycles + 1;
                IF StepTimerCycles >= CYCLES_30S THEN
                    StepNo := 0;
                    StepTimerCycles := 0;
                END_IF;
            END_IF;
        ELSE
            StepNo := 0;
            StepTimerCycles := 0;
            Status := 16#8901;
    END_CASE;

    CASE StepNo OF
        0:
            WaterValve := FALSE;
            LyeValve := FALSE;
            RinseValve := FALSE;
            PumpRun := FALSE;
        1:
            WaterValve := TRUE;
            LyeValve := FALSE;
            RinseValve := FALSE;
            PumpRun := TRUE;
        2:
            WaterValve := FALSE;
            LyeValve := TRUE;
            RinseValve := FALSE;
            PumpRun := TRUE;
        3:
            WaterValve := FALSE;
            LyeValve := FALSE;
            RinseValve := TRUE;
            PumpRun := TRUE;
        ELSE
            WaterValve := FALSE;
            LyeValve := FALSE;
            RinseValve := FALSE;
            PumpRun := FALSE;
            StepNo := 0;
            Status := 16#8901;
    END_CASE;

    StartCIPLast := StartCIP;
    StepDoneLast := StepDone;
END_IF;

END_FUNCTION_BLOCK

FUNCTION_BLOCK FB_P15
VAR_INPUT
    estop : BOOL;
    opeMode : BOOL;
    valveAStart : BOOL;
    valveBStart : BOOL;
    valveCStart : BOOL;
    valveDStart : BOOL;
    mixMotorStart : BOOL;
    autoStart : BOOL;
    processMode : BOOL;
    levelSensor : INT;
    mixMotorComplete : BOOL;
END_VAR
VAR_OUTPUT
    valveARun : BOOL;
    valveBRun : BOOL;
    valveCRun : BOOL;
    valveDRun : BOOL;
    mixMotorRun : BOOL;
END_VAR
VAR
    initCnt : INT := 0;
    prevOpeMode : BOOL := FALSE;
    prevValveAStart : BOOL := FALSE;
    prevValveBStart : BOOL := FALSE;
    prevValveCStart : BOOL := FALSE;
    prevValveDStart : BOOL := FALSE;
    prevMixMotorStart : BOOL := FALSE;
    prevAutoStart : BOOL := FALSE;

    riseValveA : BOOL;
    riseValveB : BOOL;
    riseValveC : BOOL;
    riseValveD : BOOL;
    riseMixMotor : BOOL;
    riseAutoStart : BOOL;

    manValveA : BOOL := FALSE;
    manValveB : BOOL := FALSE;
    manValveC : BOOL := FALSE;
    manValveD : BOOL := FALSE;
    manMixMotor : BOOL := FALSE;

    autoStep : INT := 0;
    modeLatchedProcess : BOOL := FALSE;
END_VAR

riseValveA := valveAStart AND NOT prevValveAStart;
riseValveB := valveBStart AND NOT prevValveBStart;
riseValveC := valveCStart AND NOT prevValveCStart;
riseValveD := valveDStart AND NOT prevValveDStart;
riseMixMotor := mixMotorStart AND NOT prevMixMotorStart;
riseAutoStart := autoStart AND NOT prevAutoStart;

IF initCnt < 2 THEN
    valveARun := FALSE;
    valveBRun := FALSE;
    valveCRun := FALSE;
    valveDRun := FALSE;
    mixMotorRun := FALSE;

    manValveA := FALSE;
    manValveB := FALSE;
    manValveC := FALSE;
    manValveD := FALSE;
    manMixMotor := FALSE;

    autoStep := 0;
    modeLatchedProcess := FALSE;
    initCnt := initCnt + 1;

ELSIF NOT estop THEN
    valveARun := FALSE;
    valveBRun := FALSE;
    valveCRun := FALSE;
    valveDRun := FALSE;
    mixMotorRun := FALSE;

    manValveA := FALSE;
    manValveB := FALSE;
    manValveC := FALSE;
    manValveD := FALSE;
    manMixMotor := FALSE;

    autoStep := 0;
    modeLatchedProcess := FALSE;

ELSE
    IF opeMode <> prevOpeMode THEN
        manValveA := FALSE;
        manValveB := FALSE;
        manValveC := FALSE;
        manValveD := FALSE;
        manMixMotor := FALSE;

        autoStep := 0;
        modeLatchedProcess := FALSE;

        valveARun := FALSE;
        valveBRun := FALSE;
        valveCRun := FALSE;
        valveDRun := FALSE;
        mixMotorRun := FALSE;
    END_IF;

    IF NOT opeMode THEN
        autoStep := 0;

        IF riseValveA THEN
            manValveA := NOT manValveA;
            IF manValveA THEN
                manValveD := FALSE;
            END_IF;
        END_IF;

        IF riseValveB THEN
            manValveB := NOT manValveB;
            IF manValveB THEN
                manValveD := FALSE;
            END_IF;
        END_IF;

        IF riseValveC THEN
            manValveC := NOT manValveC;
            IF manValveC THEN
                manValveD := FALSE;
            END_IF;
        END_IF;

        IF riseValveD THEN
            manValveD := NOT manValveD;
            IF manValveD THEN
                manValveA := FALSE;
                manValveB := FALSE;
                manValveC := FALSE;
            END_IF;
        END_IF;

        IF riseMixMotor THEN
            IF manMixMotor THEN
                IF mixMotorComplete THEN
                    manMixMotor := FALSE;
                END_IF;
            ELSE
                manMixMotor := TRUE;
            END_IF;
        END_IF;

        valveARun := manValveA;
        valveBRun := manValveB;
        valveCRun := manValveC;
        valveDRun := manValveD;
        mixMotorRun := manMixMotor;

        IF manValveD THEN
            manValveA := FALSE;
            manValveB := FALSE;
            manValveC := FALSE;
            valveARun := FALSE;
            valveBRun := FALSE;
            valveCRun := FALSE;
            valveDRun := TRUE;
        ELSE
            valveDRun := FALSE;
        END_IF;

    ELSE
        manValveA := FALSE;
        manValveB := FALSE;
        manValveC := FALSE;
        manValveD := FALSE;
        manMixMotor := FALSE;

        IF riseAutoStart AND ((autoStep = 0) OR (autoStep = 60)) THEN
            autoStep := 10;
            modeLatchedProcess := processMode;
        END_IF;

        valveARun := FALSE;
        valveBRun := FALSE;
        valveCRun := FALSE;
        valveDRun := FALSE;
        mixMotorRun := FALSE;

        CASE autoStep OF
            0:
                autoStep := 0;

            10:
                valveARun := TRUE;
                IF levelSensor >= 50 THEN
                    valveARun := FALSE;
                    valveBRun := TRUE;
                    autoStep := 20;
                END_IF;

            20:
                valveBRun := TRUE;
                IF levelSensor >= 80 THEN
                    valveBRun := FALSE;
                    IF modeLatchedProcess THEN
                        valveCRun := TRUE;
                        autoStep := 30;
                    ELSE
                        mixMotorRun := TRUE;
                        autoStep := 50;
                    END_IF;
                END_IF;

            30:
                valveCRun := TRUE;
                IF levelSensor >= 100 THEN
                    valveCRun := FALSE;
                    mixMotorRun := TRUE;
                    autoStep := 50;
                END_IF;

            50:
                mixMotorRun := TRUE;
                IF mixMotorComplete THEN
                    mixMotorRun := FALSE;
                    valveDRun := TRUE;
                    autoStep := 60;
                END_IF;

            60:
                valveDRun := TRUE;

            ELSE
                autoStep := 0;
        END_CASE;
    END_IF;
END_IF;

prevValveAStart := valveAStart;
prevValveBStart := valveBStart;
prevValveCStart := valveCStart;
prevValveDStart := valveDStart;
prevMixMotorStart := mixMotorStart;
prevAutoStart := autoStart;
prevOpeMode := opeMode;

END_FUNCTION_BLOCK

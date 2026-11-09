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
    valveARun : BOOL := FALSE;
    valveBRun : BOOL := FALSE;
    valveCRun : BOOL := FALSE;
    valveDRun : BOOL := FALSE;
    mixMotorRun : BOOL := FALSE;
END_VAR
VAR
    startupScans : INT := 0;
    previousMode : BOOL := FALSE;
    emergencySeen : BOOL := FALSE;

    previousA : BOOL := FALSE;
    previousB : BOOL := FALSE;
    previousC : BOOL := FALSE;
    previousD : BOOL := FALSE;
    previousMotor : BOOL := FALSE;
    previousAuto : BOOL := FALSE;

    edgeA : BOOL;
    edgeB : BOOL;
    edgeC : BOOL;
    edgeD : BOOL;
    edgeMotor : BOOL;
    edgeAuto : BOOL;

    (* 0: idle; 1: A; 2: B; 3: C; 4: mixing; 5: discharge. *)
    step : INT := 0;
END_VAR

(*
    Scan period: 20 ms. No timing library is required.

    REQUIREMENT CONFLICTS -- PENDING REVIEW:
    1. C2 states mixMotorRun -> NOT estop. The interface defines
       estop=FALSE as emergency stop. Together with C1, literal C2
       prohibits mixing in every condition. This implementation uses
       the interface definition and K1; literal C2 is not satisfied.
    2. Unconditional C6 conflicts with emergency stopping and manual
       motor toggle-off before completion. Emergency stop and manual
       start/stop requirements take precedence here; unconditional C6
       is not satisfied.
    3. Unrestricted independent manual valve toggles conflict with C4
       when discharge and proportioning are requested together.
       C4 is enforced: opening a proportioning valve closes D;
       opening D closes A/B/C. A simultaneous opening request for D
       takes priority.
    4. K4 is implemented by preserving the automatic step during
       emergency stop, then clearing it on recovery. Restart requires
       a fresh autoStart rising edge.

    C10's inclusive interval [0,1] is implemented as two inhibited
    startup scans. Button histories are sampled even while inhibited,
    so held buttons do not cause an automatic restart.

    Compilation and cycle-by-cycle verification have not been performed.
*)

edgeA := valveAStart AND NOT previousA;
edgeB := valveBStart AND NOT previousB;
edgeC := valveCStart AND NOT previousC;
edgeD := valveDStart AND NOT previousD;
edgeMotor := mixMotorStart AND NOT previousMotor;
edgeAuto := autoStart AND NOT previousAuto;

previousA := valveAStart;
previousB := valveBStart;
previousC := valveCStart;
previousD := valveDStart;
previousMotor := mixMotorStart;
previousAuto := autoStart;

IF NOT estop THEN
    (* Highest priority: stop outputs without advancing the sequence. *)
    valveARun := FALSE;
    valveBRun := FALSE;
    valveCRun := FALSE;
    valveDRun := FALSE;
    mixMotorRun := FALSE;
    emergencySeen := TRUE;

    IF startupScans < 2 THEN
        startupScans := startupScans + 1;
    END_IF;

ELSIF startupScans < 2 THEN
    valveARun := FALSE;
    valveBRun := FALSE;
    valveCRun := FALSE;
    valveDRun := FALSE;
    mixMotorRun := FALSE;
    step := 0;
    startupScans := startupScans + 1;

ELSIF emergencySeen THEN
    (* Recovery is a safe reset, never continuation of the old step. *)
    valveARun := FALSE;
    valveBRun := FALSE;
    valveCRun := FALSE;
    valveDRun := FALSE;
    mixMotorRun := FALSE;
    step := 0;
    emergencySeen := FALSE;
    previousMode := opeMode;

ELSIF opeMode <> previousMode THEN
    (* Mode changes cancel retained manual commands and automatic work. *)
    valveARun := FALSE;
    valveBRun := FALSE;
    valveCRun := FALSE;
    valveDRun := FALSE;
    mixMotorRun := FALSE;
    step := 0;
    previousMode := opeMode;

ELSIF NOT opeMode THEN
    step := 0;

    IF edgeA THEN
        valveARun := NOT valveARun;
        IF valveARun THEN
            valveDRun := FALSE;
        END_IF;
    END_IF;

    IF edgeB THEN
        valveBRun := NOT valveBRun;
        IF valveBRun THEN
            valveDRun := FALSE;
        END_IF;
    END_IF;

    IF edgeC THEN
        valveCRun := NOT valveCRun;
        IF valveCRun THEN
            valveDRun := FALSE;
        END_IF;
    END_IF;

    IF edgeD THEN
        valveDRun := NOT valveDRun;
        IF valveDRun THEN
            valveARun := FALSE;
            valveBRun := FALSE;
            valveCRun := FALSE;
        END_IF;
    END_IF;

    IF edgeMotor THEN
        mixMotorRun := NOT mixMotorRun;
    END_IF;

ELSE
    (* All automatic commands are decoded from a single sequence step. *)
    valveARun := FALSE;
    valveBRun := FALSE;
    valveCRun := FALSE;
    valveDRun := FALSE;
    mixMotorRun := FALSE;

    CASE step OF
        0:
            IF edgeAuto THEN
                step := 1;
            END_IF;

        1:
            IF levelSensor >= 50 THEN
                step := 2;
            END_IF;

        2:
            IF levelSensor >= 80 THEN
                IF processMode THEN
                    step := 3;
                ELSE
                    step := 4;
                END_IF;
            END_IF;

        3:
            IF levelSensor >= 100 THEN
                step := 4;
            END_IF;

        4:
            IF mixMotorComplete THEN
                step := 5;
            END_IF;

        5:
            (* No discharge-complete input exists: D remains open
               until a new cycle, mode change, or emergency stop. *)
            IF edgeAuto THEN
                step := 1;
            END_IF;

    ELSE
        step := 0;
    END_CASE;

    CASE step OF
        1:
            valveARun := TRUE;
        2:
            valveBRun := TRUE;
        3:
            valveCRun := TRUE;
        4:
            mixMotorRun := TRUE;
        5:
            valveDRun := TRUE;
    END_CASE;
END_IF;

END_FUNCTION_BLOCK

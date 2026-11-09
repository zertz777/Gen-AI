FUNCTION_BLOCK FB_P03
VAR_INPUT
    Value : REAL;
    hiLevel : REAL;
    loLevel : REAL;
    hystWindow : REAL;
END_VAR
VAR_OUTPUT
    hiAlarm : BOOL;
    loAlarm : BOOL;
    error : BOOL;
    status : WORD;
END_VAR

(* Conflict note: C10 requires first-scan !hiAlarm && !loAlarm && !error && status=16#0000.
   If K1/K2 invalid parameters or K3/K4 alarm conditions are true on the first scan,
   this conflicts with immediate error/alarm handling. This implementation prioritizes
   K1-K4 immediate safety/error logic; initial output values are as declared by the task. *)

(* K1: loLevel >= hiLevel -> error 16#8001 and skip alarm logic *)
IF loLevel >= hiLevel THEN
    error := TRUE;
    status := WORD#16#8001;
    hiAlarm := FALSE;
    loAlarm := FALSE;

(* K2: hystWindow >= (hiLevel - loLevel) -> error 16#8002 and skip alarm logic *)
ELSIF hystWindow >= (hiLevel - loLevel) THEN
    error := TRUE;
    status := WORD#16#8002;
    hiAlarm := FALSE;
    loAlarm := FALSE;

(* Valid parameters: execute hysteresis alarm logic *)
ELSE
    error := FALSE;
    status := WORD#16#0000;

    (* K3: high alarm with hysteresis *)
    IF Value > hiLevel THEN
        hiAlarm := TRUE;
    ELSIF Value < (hiLevel - hystWindow) THEN
        hiAlarm := FALSE;
    END_IF;

    (* K4: low alarm with hysteresis *)
    IF Value < loLevel THEN
        loAlarm := TRUE;
    ELSIF Value > (loLevel + hystWindow) THEN
        loAlarm := FALSE;
    END_IF;
END_IF;

END_FUNCTION_BLOCK

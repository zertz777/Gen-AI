FUNCTION_BLOCK FB_P13
VAR_INPUT
    OCCUPANCY_DETECTED : BOOL;
    ENERGY_SAVING_MODE : BOOL;
    HVAC_MODE_SELECTOR : INT;
END_VAR
VAR_OUTPUT
    SUPPLY_FAN_RUN : BOOL;
    TEMP_SETPOINT_ADJUST : INT;
END_VAR
VAR
    Initialized : BOOL := FALSE;
    StartDelayCounter : INT := 0;
    TempAdjust : INT := 0;
END_VAR
VAR CONSTANT
    START_DELAY_SCANS : INT := 1500; (* 30 s / 20 ms scan *)
    TEMP_ADJUST_MAX : INT := 4;
    TEMP_ADJUST_MIN : INT := -4;
END_VAR

(* C10: power-up scan must keep outputs at initial state. *)
IF NOT Initialized THEN
    SUPPLY_FAN_RUN := FALSE;
    TEMP_SETPOINT_ADJUST := 0;
    StartDelayCounter := 0;
    TempAdjust := 0;
    Initialized := TRUE;
ELSE
    (* K1/K2/C2/C3/C6: 30 s fan start delay, immediate stop on occupancy loss or Night mode. *)
    IF OCCUPANCY_DETECTED AND (HVAC_MODE_SELECTOR <> 3) THEN
        IF StartDelayCounter < START_DELAY_SCANS THEN
            StartDelayCounter := StartDelayCounter + 1;
        END_IF;

        IF StartDelayCounter >= START_DELAY_SCANS THEN
            SUPPLY_FAN_RUN := TRUE;
        ELSE
            SUPPLY_FAN_RUN := FALSE;
        END_IF;
    ELSE
        StartDelayCounter := 0;
        SUPPLY_FAN_RUN := FALSE;
    END_IF;

    (* K3: temperature-setpoint adjustment by HVAC mode and occupancy. *)
    IF HVAC_MODE_SELECTOR = 3 THEN
        (* Night mode: +4 degC regardless of occupancy. *)
        TempAdjust := 4;
    ELSIF HVAC_MODE_SELECTOR = 0 THEN
        (* Auto mode. *)
        IF OCCUPANCY_DETECTED THEN
            TempAdjust := 0;
        ELSE
            IF ENERGY_SAVING_MODE THEN
                TempAdjust := 3;
            ELSE
                TempAdjust := 2;
            END_IF;
        END_IF;
    ELSIF HVAC_MODE_SELECTOR = 1 THEN
        (* Comfort mode. *)
        IF OCCUPANCY_DETECTED THEN
            TempAdjust := 0;
        ELSE
            TempAdjust := 1;
        END_IF;
    ELSIF HVAC_MODE_SELECTOR = 2 THEN
        (* Economy mode. *)
        IF OCCUPANCY_DETECTED THEN
            TempAdjust := 0;
        ELSE
            TempAdjust := 4;
        END_IF;
    ELSE
        (* Callers supply a valid selector; keep a defined value for other inputs. *)
        TempAdjust := 0;
    END_IF;

    (* K4/C4: clamp temperature adjustment to +/-4 degC. *)
    IF TempAdjust > TEMP_ADJUST_MAX THEN
        TEMP_SETPOINT_ADJUST := TEMP_ADJUST_MAX;
    ELSIF TempAdjust < TEMP_ADJUST_MIN THEN
        TEMP_SETPOINT_ADJUST := TEMP_ADJUST_MIN;
    ELSE
        TEMP_SETPOINT_ADJUST := TempAdjust;
    END_IF;
END_IF;

END_FUNCTION_BLOCK

FUNCTION_BLOCK FB_P13
VAR_INPUT
    OCCUPANCY_DETECTED : BOOL;
    ENERGY_SAVING_MODE : BOOL;
    HVAC_MODE_SELECTOR : INT;
END_VAR
VAR_OUTPUT
    SUPPLY_FAN_RUN : BOOL := FALSE;
    TEMP_SETPOINT_ADJUST : INT := 0;
END_VAR
VAR
    Initialized : BOOL := FALSE;
    StartDelayScans : INT := 0;
    FanPermitted : BOOL := FALSE;
END_VAR

IF NOT Initialized THEN
    (* Power-up scan: preserve the specified initial outputs and reset timing. *)
    SUPPLY_FAN_RUN := FALSE;
    TEMP_SETPOINT_ADJUST := 0;
    StartDelayScans := 0;
    FanPermitted := FALSE;
    Initialized := TRUE;
ELSE
    FanPermitted := OCCUPANCY_DETECTED
                    AND (HVAC_MODE_SELECTOR >= 0)
                    AND (HVAC_MODE_SELECTOR <= 2);

    (* 1500 consecutive normal scans at 20 ms give a 30-second delay.
       Loss of permission stops the fan and resets timing on this scan. *)
    IF NOT FanPermitted THEN
        StartDelayScans := 0;
        SUPPLY_FAN_RUN := FALSE;
    ELSE
        IF StartDelayScans < 1500 THEN
            StartDelayScans := StartDelayScans + 1;
        END_IF;
        SUPPLY_FAN_RUN := StartDelayScans >= 1500;
    END_IF;

    CASE HVAC_MODE_SELECTOR OF
        0:
            IF OCCUPANCY_DETECTED THEN
                TEMP_SETPOINT_ADJUST := 0;
            ELSIF ENERGY_SAVING_MODE THEN
                TEMP_SETPOINT_ADJUST := 3;
            ELSE
                TEMP_SETPOINT_ADJUST := 2;
            END_IF;

        1:
            IF OCCUPANCY_DETECTED THEN
                TEMP_SETPOINT_ADJUST := 0;
            ELSE
                TEMP_SETPOINT_ADJUST := 1;
            END_IF;

        2:
            IF OCCUPANCY_DETECTED THEN
                TEMP_SETPOINT_ADJUST := 0;
            ELSE
                TEMP_SETPOINT_ADJUST := 4;
            END_IF;

        3:
            TEMP_SETPOINT_ADJUST := 4;

        ELSE
            (* Defensive fallback; callers are required to supply valid modes. *)
            TEMP_SETPOINT_ADJUST := 0;
    END_CASE;

    IF TEMP_SETPOINT_ADJUST > 4 THEN
        TEMP_SETPOINT_ADJUST := 4;
    ELSIF TEMP_SETPOINT_ADJUST < -4 THEN
        TEMP_SETPOINT_ADJUST := -4;
    END_IF;
END_IF;

END_FUNCTION_BLOCK

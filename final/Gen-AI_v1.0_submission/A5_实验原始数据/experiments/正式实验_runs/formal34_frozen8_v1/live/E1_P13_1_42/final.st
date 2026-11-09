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
VAR CONSTANT
    (* 30 s start delay expressed in scan cycles: 30 s / 20 ms = 1500 *)
    STARTUP_DELAY_SCANS : INT := 1500;
END_VAR
VAR
    (* Scan-cycle counter for the 30 s start delay *)
    StartupCounter : INT := 0;
    (* Power-up first-scan flag, used to arm the start-delay timing *)
    FirstScan : BOOL := TRUE;
END_VAR

(* Start-delay timing (K1/K2):
   accumulate only while occupied and Night mode is NOT selected;
   reset immediately on loss of occupancy or on Night mode. *)
IF OCCUPANCY_DETECTED AND (HVAC_MODE_SELECTOR <> 3) THEN
    IF StartupCounter < STARTUP_DELAY_SCANS THEN
        StartupCounter := StartupCounter + 1;
    END_IF;
ELSE
    StartupCounter := 0;
END_IF;

(* Power-up: clear the start-delay timing on the very first scan so the
   delay is measured over whole scan periods (K1/K2). *)
IF FirstScan THEN
    FirstScan := FALSE;
    StartupCounter := 0;
END_IF;

(* Fan enable: TRUE only after the delay has been held for 30 s (K1/K2).
   Because the counter above is reset whenever the permit condition is
   lost, this output is FALSE in the same scan that occupancy drops or
   Night mode is selected (C2/C3/C6). *)
SUPPLY_FAN_RUN := (StartupCounter >= STARTUP_DELAY_SCANS);

(* Temperature-setpoint adjustment (K3):
   computed from the current inputs on every scan, including the first.
   The energy-saving selection affects Auto mode only. *)
CASE HVAC_MODE_SELECTOR OF
    0:  (* Auto: occupied 0; unoccupied +3 (energy-saving) / +2 (standard) *)
        IF OCCUPANCY_DETECTED THEN
            TEMP_SETPOINT_ADJUST := 0;
        ELSIF ENERGY_SAVING_MODE THEN
            TEMP_SETPOINT_ADJUST := 3;
        ELSE
            TEMP_SETPOINT_ADJUST := 2;
        END_IF;
    1:  (* Comfort: occupied 0; unoccupied +1 *)
        IF OCCUPANCY_DETECTED THEN
            TEMP_SETPOINT_ADJUST := 0;
        ELSE
            TEMP_SETPOINT_ADJUST := 1;
        END_IF;
    2:  (* Economy: occupied 0; unoccupied +4 *)
        IF OCCUPANCY_DETECTED THEN
            TEMP_SETPOINT_ADJUST := 0;
        ELSE
            TEMP_SETPOINT_ADJUST := 4;
        END_IF;
    3:  (* Night: +4 regardless of occupancy *)
        TEMP_SETPOINT_ADJUST := 4;
    ELSE
        (* Undefined selector value: hold a safe neutral adjustment *)
        TEMP_SETPOINT_ADJUST := 0;
END_CASE;

(* Clamp the adjustment to ±4 °C (K4/C4). *)
IF TEMP_SETPOINT_ADJUST > 4 THEN
    TEMP_SETPOINT_ADJUST := 4;
ELSIF TEMP_SETPOINT_ADJUST < -4 THEN
    TEMP_SETPOINT_ADJUST := -4;
END_IF;
END_FUNCTION_BLOCK

(*
  Semantic conflict retained for cycle-level testing:
  Control requirement 1 defines SensorValid TRUE for 4..20 mA.
  K1 / requirement 3 define recovery validity for 3.8..20.5 mA.
  This implementation follows K1 hysteresis; the 3.8..4.0 mA and 20.0..20.5 mA
  boundaries are therefore retained as specified and must be verified by tests.
*)

FUNCTION_BLOCK FB_S11
VAR_INPUT
    SensorCurrent : REAL;
    FallbackValue : REAL;
END_VAR
VAR_OUTPUT
    SensorValid : BOOL;
    DegradedMode : BOOL;
    ControlValue : REAL;
    AlarmLamp : BOOL;
    Status : WORD;
END_VAR
VAR
    FirstScan : BOOL := TRUE;
    FaultCounter : INT := 0;
    RecoveryCounter : INT := 0;
    BlinkCounter : INT := 0;
    LastControlValue : REAL := 0.0;
END_VAR

(* First scan keeps the specified initial state, including C10. *)
IF FirstScan THEN
    SensorValid := FALSE;
    DegradedMode := FALSE;
    ControlValue := 0.0;
    AlarmLamp := FALSE;
    Status := 16#0000;
    FaultCounter := 0;
    RecoveryCounter := 0;
    BlinkCounter := 0;
    LastControlValue := 0.0;
    FirstScan := FALSE;
ELSE
    (* 1 Hz blink: 20 ms scan, 50 scans = 1 s, 25 scans ON / 25 scans OFF. *)
    BlinkCounter := BlinkCounter + 1;
    IF BlinkCounter >= 50 THEN
        BlinkCounter := 0;
    END_IF;

    (* Sensor validity with K1 hysteresis:
       invalid if < 3.6 mA or > 21 mA;
       valid if 3.8..20.5 mA;
       otherwise keep previous validity. *)
    IF (SensorCurrent < 3.6) OR (SensorCurrent > 21.0) THEN
        SensorValid := FALSE;
    ELSIF (SensorCurrent >= 3.8) AND (SensorCurrent <= 20.5) THEN
        SensorValid := TRUE;
    ELSE
        (* keep previous SensorValid *)
        ;
    END_IF;

    IF DegradedMode THEN
        (* K3/K4: during degraded mode, including recovery confirmation,
           ControlValue is the fallback value. *)
        ControlValue := FallbackValue;
        AlarmLamp := TRUE;

        IF SensorValid THEN
            (* Recovery confirmation period: SensorValid and DegradedMode may
               both be TRUE; Status = 16#8A03. Hold for at least 3 s
               (150 scans), then exit on the following scan. *)
            RecoveryCounter := RecoveryCounter + 1;
            Status := 16#8A03;

            IF RecoveryCounter >= 151 THEN
                DegradedMode := FALSE;
                RecoveryCounter := 0;
                FaultCounter := 0;
                Status := 16#0000;
                AlarmLamp := FALSE;
                ControlValue := (SensorCurrent - 4.0) / 16.0 * 100.0;
                LastControlValue := ControlValue;
            END_IF;
        ELSE
            (* Still broken while degraded: Status = 16#8A02. *)
            RecoveryCounter := 0;
            Status := 16#8A02;
        END_IF;
    ELSE
        IF SensorValid THEN
            (* Normal operation. *)
            FaultCounter := 0;
            RecoveryCounter := 0;
            Status := 16#0000;
            AlarmLamp := FALSE;
            ControlValue := (SensorCurrent - 4.0) / 16.0 * 100.0;
            LastControlValue := ControlValue;
        ELSE
            (* Broken signal but not yet degraded: Status = 16#8A01,
               AlarmLamp blinks. After 2 s (100 scans), enter degraded mode. *)
            FaultCounter := FaultCounter + 1;

            IF FaultCounter >= 100 THEN
                DegradedMode := TRUE;
                Status := 16#8A02;
                AlarmLamp := TRUE;
                ControlValue := FallbackValue;
                RecoveryCounter := 0;
            ELSE
                Status := 16#8A01;
                AlarmLamp := (BlinkCounter < 25);
                ControlValue := LastControlValue;
            END_IF;
        END_IF;
    END_IF;
END_IF;

END_FUNCTION_BLOCK

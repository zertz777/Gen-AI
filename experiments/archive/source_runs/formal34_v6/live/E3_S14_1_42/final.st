FUNCTION_BLOCK FB_S14
VAR_INPUT
    Pressure : REAL;
    PumpEnable : BOOL;
    ResetBtn : BOOL;
END_VAR
VAR_OUTPUT
    LowPump : BOOL := FALSE;
    HighPump : BOOL := FALSE;
    ReliefValve : BOOL := FALSE;
    AlarmLamp : BOOL := FALSE;
    Status : WORD := 16#0000;
END_VAR
VAR
    ResetBtnLast : BOOL := FALSE;
    ResetEdge : BOOL := FALSE;
    HighPumpLatched : BOOL := FALSE;
    ReliefLatched : BOOL := FALSE;
    SensorFaultLatched : BOOL := FALSE;
    SensorFaultActive : BOOL := FALSE;
    NormalEnable : BOOL := FALSE;
END_VAR

(* SEMANTIC CONFLICT NOTE:
   Req.3 requires HighPump, once on, to drop only when Pressure < 100.0 bar.
   Req.4 requires Pressure > 160.0 bar to force LowPump/HighPump OFF and ReliefValve ON.
   This implementation applies the safety override: >160.0 bar forces pumps OFF and
   clears HighPumpLatched. K1 same-cycle overpressure protection is prioritized over
   the formal X(next-cycle) wording. *)

ResetEdge := ResetBtn AND NOT ResetBtnLast;
ResetBtnLast := ResetBtn;

SensorFaultActive := (Pressure < 0.5) OR (Pressure > 250.0);

IF Pressure > 160.0 THEN
    ReliefLatched := TRUE;
ELSIF Pressure < 150.0 THEN
    ReliefLatched := FALSE;
END_IF;
ReliefValve := ReliefLatched;

IF SensorFaultActive THEN
    SensorFaultLatched := TRUE;
    Status := 16#8D01;
    AlarmLamp := TRUE;
    LowPump := FALSE;
    HighPump := FALSE;
    HighPumpLatched := FALSE;
ELSIF SensorFaultLatched THEN
    IF ResetEdge THEN
        SensorFaultLatched := FALSE;
    ELSE
        Status := 16#8D02;
        AlarmLamp := TRUE;
        LowPump := FALSE;
        HighPump := FALSE;
        HighPumpLatched := FALSE;
    END_IF;
END_IF;

IF (NOT SensorFaultActive) AND (NOT SensorFaultLatched) THEN
    Status := 16#0000;
    AlarmLamp := FALSE;
    NormalEnable := PumpEnable;

    IF Pressure >= 140.0 THEN
        HighPumpLatched := TRUE;
    ELSIF Pressure < 100.0 THEN
        HighPumpLatched := FALSE;
    END_IF;

    IF ReliefValve OR NOT NormalEnable THEN
        HighPumpLatched := FALSE;
    END_IF;

    LowPump := NormalEnable AND NOT ReliefValve AND (Pressure < 120.0);
    HighPump := NormalEnable AND NOT ReliefValve AND HighPumpLatched;
END_IF;

END_FUNCTION_BLOCK

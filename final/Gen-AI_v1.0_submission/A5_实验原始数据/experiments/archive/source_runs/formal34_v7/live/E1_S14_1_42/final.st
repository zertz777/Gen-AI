FUNCTION_BLOCK FB_S14
VAR_INPUT
    Pressure : REAL;
    PumpEnable : BOOL;
    ResetBtn : BOOL;
END_VAR
VAR_OUTPUT
    LowPump : BOOL;
    HighPump : BOOL;
    ReliefValve : BOOL;
    AlarmLamp : BOOL;
    Status : WORD;
END_VAR
VAR
    (* --- internal state (declared, no external interface change) --- *)
    ResetBtnLast  : BOOL := FALSE;  (* previous ResetBtn value, rising-edge detect *)
    FaultLatched  : BOOL := FALSE;  (* latched sensor fault, awaiting ResetBtn *)
    HighPumpLatch : BOOL := FALSE;  (* single load-stage state:
                                       TRUE  = high stage (HighPump active)
                                       FALSE = low  stage (LowPump active)
                                       matches initial_state HighPumpLatched = FALSE *)
    ReliefLatch   : BOOL := FALSE;  (* hysteresis state of relief valve *)
END_VAR
(*
  Conflict / ambiguity report (kept, not silently resolved):
  - C1 uses X(...) (relief held next cycle) while K1 / requirement 4 require
    same-cycle relief plus a <150.0 release. Implemented as K1 + 160.0/150.0
    hysteresis; therefore C1 is not satisfied on a one-cycle drop >160 -> <150.
  - C10 formal interval [0,1] implies two cycles, the note says "first scan".
    The cycle-by-cycle tests treat the first call as cycle 1 and expect the
    outputs computed in that same cycle, so no first-scan freeze is applied;
    power-on defaults (BOOL = FALSE, Status initial) are still kept.
  - Requirement 6 does not specify ReliefValve during a sensor fault, nor
    AlarmLamp during 16#8D02. Implemented: ReliefValve = FALSE on fault,
    AlarmLamp stays TRUE until ResetBtn resets.
  - Requirement 1 (Pressure < 120 -> LowPump = TRUE) is an implication, so the
    single load-stage model (LowPump active for the whole low stage, i.e. while
    the high stage is not latched, Pressure < 140) does not conflict with it.
    This is required to satisfy the hysteresis test (S14-03) and the staged
    loading test (S14-06).
  Compile success only proves compilation; functional correctness requires
  cycle-by-cycle testing.
*)

(* Sensor out-of-range: broken wire / short circuit *)
IF (Pressure < 0.5) OR (Pressure > 250.0) THEN
    (* 16#8D01 : sensor fault -> latch it *)
    FaultLatched := TRUE;
END_IF;

(* Reset: only when fault cleared and ResetBtn rising edge *)
IF FaultLatched AND (Pressure >= 0.5) AND (Pressure <= 250.0)
   AND ResetBtn AND (NOT ResetBtnLast) THEN
    FaultLatched := FALSE;
END_IF;

IF (Pressure < 0.5) OR (Pressure > 250.0) THEN
    (* Sensor fault active this scan: 16#8D01, stop everything *)
    Status := 16#8D01;
    AlarmLamp := TRUE;
    LowPump := FALSE;
    HighPump := FALSE;
    ReliefValve := FALSE;
    HighPumpLatch := FALSE;
    ReliefLatch := FALSE;
ELSIF FaultLatched THEN
    (* Fault cleared but not yet reset: 16#8D02, keep alarm, no load *)
    Status := 16#8D02;
    AlarmLamp := TRUE;
    LowPump := FALSE;
    HighPump := FALSE;
    ReliefValve := FALSE;
    HighPumpLatch := FALSE;
    ReliefLatch := FALSE;
ELSE
    (* Normal operation *)
    Status := 16#0000;
    AlarmLamp := FALSE;

    (* Load stage hysteresis (requirement 2/3, C7): engage high stage at
       >= 140.0, release back to low stage at < 100.0, hold in between. *)
    IF Pressure >= 140.0 THEN
        HighPumpLatch := TRUE;
    ELSIF Pressure < 100.0 THEN
        HighPumpLatch := FALSE;
    END_IF;

    (* Relief hysteresis (requirement 4): >160.0 ON, <150.0 OFF *)
    IF Pressure > 160.0 THEN
        ReliefLatch := TRUE;
    ELSIF Pressure < 150.0 THEN
        ReliefLatch := FALSE;
    END_IF;

    IF ReliefLatch THEN
        (* K1: same-cycle relief; C4: relief excludes both pumps *)
        ReliefValve := TRUE;
        LowPump := FALSE;
        HighPump := FALSE;
    ELSE
        ReliefValve := FALSE;
        IF PumpEnable THEN
            (* Staged loading: high stage drives HighPump, low stage drives
               LowPump. Never both simultaneously (mutual exclusion kept). *)
            HighPump := HighPumpLatch;
            LowPump := NOT HighPumpLatch;
        ELSE
            (* PumpEnable = FALSE : both pumps stopped *)
            LowPump := FALSE;
            HighPump := FALSE;
        END_IF;
    END_IF;
END_IF;

(* Remember ResetBtn for next-scan rising-edge detection *)
ResetBtnLast := ResetBtn;
END_FUNCTION_BLOCK

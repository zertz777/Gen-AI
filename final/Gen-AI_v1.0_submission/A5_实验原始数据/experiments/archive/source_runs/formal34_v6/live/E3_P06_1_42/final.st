(*
  P06 Aeration Blower Delayed Start
  Scan cycle: 20 ms -> 5 s start delay = 250 scans.

  Conflict report:
  Formal C6 (G(BLOWER_RUN -> (BLOWER_RUN W !DO_LOW))) and C1/K3 emergency-stop
  priority can conflict if AERATION_E_STOP_NC falls while DO_LOW remains TRUE and
  BLOWER_RUN is TRUE. This implementation applies the task's emergency-stop priority:
  AERATION_E_STOP_NC = FALSE forces BLOWER_RUN = FALSE immediately.
*)
FUNCTION_BLOCK FB_P06
VAR_INPUT
    DO_LOW : BOOL;
    AERATION_E_STOP_NC : BOOL;
END_VAR
VAR_OUTPUT
    BLOWER_RUN : BOOL;
    AERATION_BLOWER_CYCLE_COUNT : UINT;
END_VAR
VAR
    initDone : BOOL := FALSE;
    prevBlowerRun : BOOL := FALSE;
    startDelayCount : UINT := 0;
END_VAR

(* Power-up initial state. *)
IF NOT initDone THEN
    BLOWER_RUN := FALSE;
    AERATION_BLOWER_CYCLE_COUNT := 0;
    prevBlowerRun := FALSE;
    startDelayCount := 0;
    initDone := TRUE;
END_IF;

(* Safety priority: emergency stop active. *)
IF NOT AERATION_E_STOP_NC THEN
    BLOWER_RUN := FALSE;
    startDelayCount := 0;

(* Demand lost: stop immediately and reset start delay. *)
ELSIF NOT DO_LOW THEN
    BLOWER_RUN := FALSE;
    startDelayCount := 0;

ELSE
    (* Both permissive conditions are TRUE. Count scans up to 5 s. *)
    IF startDelayCount < UINT#250 THEN
        startDelayCount := startDelayCount + UINT#1;
    END_IF;

    IF startDelayCount >= UINT#250 THEN
        BLOWER_RUN := TRUE;
    ELSE
        BLOWER_RUN := FALSE;
    END_IF;
END_IF;

(* Count one FALSE->TRUE transition of BLOWER_RUN. Saturation at UINT max. *)
IF BLOWER_RUN AND NOT prevBlowerRun THEN
    IF AERATION_BLOWER_CYCLE_COUNT < UINT#65535 THEN
        AERATION_BLOWER_CYCLE_COUNT := AERATION_BLOWER_CYCLE_COUNT + UINT#1;
    END_IF;
END_IF;

prevBlowerRun := BLOWER_RUN;

END_FUNCTION_BLOCK

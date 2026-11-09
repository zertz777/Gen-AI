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
    (* Start-delay elapsed time in scans. 5 s / 20 ms = 250 scans.    *)
    (* IEC default at power-up: UINT -> 0, BOOL -> FALSE (K1, C10).   *)
    start_delay_scans : UINT;
    (* Previous BLOWER_RUN value for FALSE->TRUE edge detection (K4). *)
    prev_blower_run : BOOL;
END_VAR

(* Permissive lost (demand gone or emergency stop active): stop now   *)
(* and reset the start timer so a new demand waits a full 5 s (K3).   *)
IF (NOT AERATION_E_STOP_NC) OR (NOT DO_LOW) THEN
    BLOWER_RUN := FALSE;
    start_delay_scans := 0;
ELSE
    (* Both permissives hold this scan: advance the start delay.      *)
    IF start_delay_scans < 250 THEN
        start_delay_scans := start_delay_scans + 1;
    ELSE
        start_delay_scans := 250;
    END_IF;

    (* Enable the blower only after a full 5 s of sustained demand.   *)
    IF start_delay_scans >= 250 THEN
        BLOWER_RUN := TRUE;
    END_IF;
END_IF;

(* Count one start per FALSE->TRUE transition of BLOWER_RUN only (K4). *)
IF BLOWER_RUN AND (NOT prev_blower_run) THEN
    AERATION_BLOWER_CYCLE_COUNT := AERATION_BLOWER_CYCLE_COUNT + 1;
END_IF;
prev_blower_run := BLOWER_RUN;

END_FUNCTION_BLOCK

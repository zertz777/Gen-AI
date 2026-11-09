FUNCTION_BLOCK FB_P05
VAR_INPUT
    Gap_Exceeded : BOOL;
    Weld_E_Stop_NC : BOOL;
    DebounceTime : TIME;
END_VAR
VAR_OUTPUT
    Operator_Alert : BOOL;
    Weld_Soft_Start_Active : BOOL;
END_VAR
VAR
    (* Internal state only - the external interface is left unchanged. *)
    Init_Elapsed : TIME := T#0s;          (* time since power-up        *)
    Deb_Elapsed : TIME := T#0s;           (* accumulated gap TRUE time  *)
    EStop_Active : BOOL := FALSE;         (* decoded emergency stop     *)
    Init_Inhibition_Active : BOOL := TRUE;(* power-up inhibition window *)
END_VAR

(* =====================================================================
   FB_P05 - weld gap alarm with power-up monitoring inhibition, input
   debouncing during normal monitoring and emergency-stop priority.

   Scan cycle: 20 ms (5 s inhibition = 250 scans).  Timers are built
   only from IEC TIME arithmetic and comparisons, because this compiler
   provides no standard-library timer FB (TON was unknown to it).

   Declared building blocks: base types, TIME +/- and comparisons,
   BOOL logic.  No standard FB instance, no vendor extension, no
   VARIANT, no open array, no dynamic memory, no file/network access,
   no GOTO, no undeclared variable.

   Required initial state is produced on the first scan: Init_Elapsed is
   T#0s so Init_Inhibition_Active is TRUE (Weld_Soft_Start_Active TRUE),
   Operator_Alert is FALSE and Deb_Elapsed is T#0s.
   ===================================================================== *)

(* --- decode the normally-closed emergency-stop input ----------------- *)
(* TRUE in Weld_E_Stop_NC means "e-stop not pressed" (see I/O table). *)
EStop_Active := NOT Weld_E_Stop_NC;

(* --- power-up 5 s inhibition window (K1 / requirement 2 / C10) ------- *)
(* Init_Elapsed holds the time already spent since power-up.  On the
   very first scan it is still T#0s, hence the window is active and
   Weld_Soft_Start_Active is TRUE (C10).  It counts absolute time since
   power-up and is deliberately not influenced by the emergency stop. *)
Init_Inhibition_Active := (Init_Elapsed < T#5s);

(* --- priority chain: K4 (e-stop) > K1 (inhibition) > K2/K3 ----------- *)
IF EStop_Active THEN
    (* K4 / C1 / C2 : the emergency stop has priority over the
       initialization period and over normal monitoring.  The alarm is
       released in this very scan and any incomplete debounce timing is
       cleared. *)
    Deb_Elapsed := T#0s;
    Operator_Alert := FALSE;
ELSIF Init_Inhibition_Active THEN
    (* K1 / requirement 2 : no alarm during initialization and the
       gap-signal debounce time must NOT accumulate in this period. *)
    Deb_Elapsed := T#0s;
    Operator_Alert := FALSE;
ELSE
    (* K2 / K3 / requirement 3 : normal monitoring.
       The elapsed time only grows while Gap_Exceeded is TRUE, so the
       alarm can be set only after Gap_Exceeded has remained TRUE for
       DebounceTime.  When the signal becomes FALSE the timing is
       cleared in the same scan and the alarm drops immediately. *)
    IF Gap_Exceeded THEN
        IF Deb_Elapsed < DebounceTime THEN
            Deb_Elapsed := Deb_Elapsed + T#20ms;
        END_IF;
    ELSE
        Deb_Elapsed := T#0s;
    END_IF;
    Operator_Alert := Gap_Exceeded AND (Deb_Elapsed >= DebounceTime);
END_IF;

(* --- Weld_Soft_Start_Active ----------------------------------------- *)
(* Requirement 5 : this output marks only the power-up inhibition
   window; it is not a continuous speed ramp and it is not influenced by
   the emergency stop. *)
Weld_Soft_Start_Active := Init_Inhibition_Active;

(* --- advance the power-up timer at the end of the scan -------------- *)
IF Init_Elapsed < T#5s THEN
    Init_Elapsed := Init_Elapsed + T#20ms;
END_IF;

(* =====================================================================
   REPORTED SPEC CONFLICT - preserved, not silently resolved.

   Requirement 3 / constraint K3 :
       "When the signal becomes FALSE, switch off the alarm and clear
        debounce timing."  -> immediate release.
   LTL C9 :
       G(Operator_Alert -> G[0,25](Operator_Alert))  -> the alarm, once
       set, must stay TRUE at least 25 scans (500 ms at 20 ms/scan).

   If Gap_Exceeded returns to FALSE within 500 ms after the alarm was
   set, the two clauses contradict each other: K3 demands release in the
   same scan, C9 forbids release before 500 ms.  Both cannot hold.

   This implementation follows the primary requirement text, the
   constraint list K1-K4 and the remaining LTL clauses C1/C2/C6/C10
   (C6, "Operator_Alert W !Gap_Exceeded", explicitly permits the release
   in the very scan in which the gap signal falls).  Consequently C9 is
   NOT satisfied in that boundary case - this is reported, not hidden.

   No interface was added or changed.  No artificial 500 ms hold was
   inserted, because that would silently break requirement 3 / K3.  No
   claim is made that this text is functionally verified: compilation
   only proves that it compiles; functional correctness has to be
   established by per-cycle tests, and any C9 counterexample produced by
   those tests is exactly the conflict reported above.
   ===================================================================== *)
END_FUNCTION_BLOCK

FUNCTION_BLOCK FB_P19
VAR_INPUT
    ManualMode : BOOL;
    SingleStepMode : BOOL;
    SingleCycleMode : BOOL;
    ContinuousMode : BOOL;
    EmergencyStop : BOOL;
    Start : BOOL;
    DownButton : BOOL;
    UpButton : BOOL;
    LeftButton : BOOL;
    RightButton : BOOL;
    GripButton : BOOL;
    ReleaseButton : BOOL;
    DownLimitSwitch : BOOL;
    UpLimitSwitch : BOOL;
    LeftLimitSwitch : BOOL;
    RightLimitSwitch : BOOL;
    GripLimitSwitch : BOOL;
    ReleaseLimitSwitch : BOOL;
END_VAR
VAR_OUTPUT
    MoveDown : BOOL;
    MoveUp : BOOL;
    MoveLeft : BOOL;
    MoveRight : BOOL;
    ActivateGrip : BOOL;
    ActivateRelease : BOOL;
END_VAR
VAR
    (* internal state, no timers required (no time-bounded requirement) *)
    StartPrev : BOOL;    (* Start value of previous scan, for edge detection *)
    StartEdge : BOOL;    (* Start rising edge in current scan *)
    AutoRun : BOOL;      (* automatic sequence running (single cycle / continuous) *)
    Step : INT;          (* 0 = idle, 1..8 = sequence action index *)
END_VAR

(*
    P19 Mechanical Arm Control                            scan cycle = 20 ms

    Retained semantic conflict (not resolved silently):
      K1  : in manual mode an action is output only while its button is pressed and
            the corresponding limit is not yet reached; releasing the button stops it.
      C6  : G(ActivateGrip -> (ActivateGrip W GripLimitSwitch)) requires the grip
            output to be held until GripLimitSwitch.
      In automatic and single-step modes the grip is held by the step machine until
      the limit switch, so C6 holds there. In manual mode the operator may release
      GripButton before the grip limit is reached, which follows K1 but would violate
      C6 if the LTL oracle applies C6 to manual mode as well.

    Mode inputs are assumed mutually exclusive by the caller (K2). Priority used here:
      EmergencyStop > Manual > SingleStep > (SingleCycle = Continuous).
*)

(* ---- Start push-button rising-edge detection ---- *)
StartEdge := Start AND NOT StartPrev;
StartPrev := Start;

(* ---- safe default: all six actions OFF (C10: no output on first scan) ---- *)
MoveDown := FALSE;
MoveUp := FALSE;
MoveLeft := FALSE;
MoveRight := FALSE;
ActivateGrip := FALSE;
ActivateRelease := FALSE;

IF NOT EmergencyStop THEN
    (* C1 / K4: emergency stop -> all actions OFF, clear automatic progress *)
    AutoRun := FALSE;
    Step := 0;

ELSIF ManualMode THEN
    (* K1 / K2 / C2 / C4: manual jog, at most one action, stop on button release
       or when the corresponding limit switch is reached *)
    AutoRun := FALSE;
    Step := 0;
    IF DownButton AND NOT DownLimitSwitch THEN
        MoveDown := TRUE;
    ELSIF UpButton AND NOT UpLimitSwitch THEN
        MoveUp := TRUE;
    ELSIF LeftButton AND NOT LeftLimitSwitch THEN
        MoveLeft := TRUE;
    ELSIF RightButton AND NOT RightLimitSwitch THEN
        MoveRight := TRUE;
    ELSIF GripButton AND NOT GripLimitSwitch THEN
        ActivateGrip := TRUE;
    ELSIF ReleaseButton AND NOT ReleaseLimitSwitch THEN
        ActivateRelease := TRUE;
    END_IF;

ELSIF SingleStepMode THEN
    (* K3: each Start press confirms and executes exactly one preset action.
       C7: the current action is dropped as soon as its limit switch is reached.
       C6: grip output is held (step stays) until GripLimitSwitch. *)
    AutoRun := FALSE;
    IF StartEdge THEN
        Step := Step + 1;
        IF Step > 8 THEN
            Step := 1;   (* sequence finished, restart from the beginning *)
        END_IF;
    END_IF;
    CASE Step OF
        1:
            MoveDown := NOT DownLimitSwitch;            (* down *)
        2:
            ActivateGrip := NOT GripLimitSwitch;        (* grip *)
        3:
            MoveUp := NOT UpLimitSwitch;                (* up *)
        4:
            MoveRight := NOT RightLimitSwitch;          (* right *)
        5:
            MoveDown := NOT DownLimitSwitch;            (* down *)
        6:
            ActivateRelease := NOT ReleaseLimitSwitch;  (* release *)
        7:
            MoveUp := NOT UpLimitSwitch;                (* up *)
        8:
            MoveLeft := NOT LeftLimitSwitch;            (* left *)
    END_CASE;

ELSIF SingleCycleMode OR ContinuousMode THEN
    (* automatic handling cycle:
       down -> grip -> up -> right -> down -> release -> up -> left *)
    IF StartEdge AND NOT AutoRun THEN
        AutoRun := TRUE;
        Step := 1;
    END_IF;

    IF AutoRun THEN
        CASE Step OF
            1:
                IF DownLimitSwitch THEN
                    Step := 2;
                ELSE
                    MoveDown := TRUE;
                END_IF;
            2:
                IF GripLimitSwitch THEN
                    Step := 3;
                ELSE
                    ActivateGrip := TRUE;
                END_IF;
            3:
                IF UpLimitSwitch THEN
                    Step := 4;
                ELSE
                    MoveUp := TRUE;
                END_IF;
            4:
                IF RightLimitSwitch THEN
                    Step := 5;
                ELSE
                    MoveRight := TRUE;
                END_IF;
            5:
                IF DownLimitSwitch THEN
                    Step := 6;
                ELSE
                    MoveDown := TRUE;
                END_IF;
            6:
                IF ReleaseLimitSwitch THEN
                    Step := 7;
                ELSE
                    ActivateRelease := TRUE;
                END_IF;
            7:
                IF UpLimitSwitch THEN
                    Step := 8;
                ELSE
                    MoveUp := TRUE;
                END_IF;
            8:
                IF LeftLimitSwitch THEN
                    IF ContinuousMode THEN
                        Step := 1;            (* continuous: keep cycling *)
                    ELSE
                        AutoRun := FALSE;     (* single cycle: stop and wait for Start *)
                        Step := 0;
                    END_IF;
                ELSE
                    MoveLeft := TRUE;
                END_IF;
        END_CASE;
    END_IF;

END_IF;

END_FUNCTION_BLOCK

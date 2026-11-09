FUNCTION_BLOCK FB_P11
VAR_INPUT
    Mode : BOOL;
    ForwardButton : BOOL;
    ReverseButton : BOOL;
    SensorA : BOOL;
    SensorB : BOOL;
    SensorC : BOOL;
    ButtonA : BOOL;
    ButtonB : BOOL;
    ButtonC : BOOL;
END_VAR
VAR_OUTPUT
    MotorForward : BOOL := FALSE;
    MotorReverse : BOOL := FALSE;
    CompletionLight : BOOL := FALSE;
END_VAR
VAR
    (* 0: IDLE / A, 1: A->B, 2: B, 3: B->C, 4: C, 5: COMPLETE *)
    StationState : INT := 0;
    StartupScans : INT := 0;
    PreviousMode : BOOL := FALSE;
    PreviousButtonA : BOOL := FALSE;
    PreviousButtonB : BOOL := FALSE;
    PreviousButtonC : BOOL := FALSE;
    ButtonARise : BOOL := FALSE;
    ButtonBRise : BOOL := FALSE;
    ButtonCRise : BOOL := FALSE;
END_VAR

(*
    Each invocation represents one 20 ms scan.
    C10's explicit interval [0,1] is implemented as two inhibited scans.
    Mode changes cancel transport sequencing, but do not clear a completed
    product's light while SensorC remains TRUE.

    Review limitation: the specification references emergency-stop testing,
    but supplies no emergency-stop input or evaluable C1 requirement.
    No emergency-stop behavior can be implemented from this interface.
    Compilation and cycle-by-cycle functional validation are not claimed.
*)

ButtonARise := ButtonA AND NOT PreviousButtonA;
ButtonBRise := ButtonB AND NOT PreviousButtonB;
ButtonCRise := ButtonC AND NOT PreviousButtonC;

MotorForward := FALSE;
MotorReverse := FALSE;

IF StartupScans < 2 THEN
    StartupScans := StartupScans + 1;
    StationState := 0;
    CompletionLight := FALSE;
ELSE
    (* Completion remains latched independently of the selected mode. *)
    IF NOT SensorC THEN
        CompletionLight := FALSE;
    END_IF;

    IF Mode <> PreviousMode THEN
        StationState := 0;
    END_IF;

    IF NOT Mode THEN
        StationState := 0;

        (* Simultaneous manual direction requests produce a stop. *)
        MotorForward := ForwardButton AND NOT ReverseButton;
        MotorReverse := ReverseButton AND NOT ForwardButton;
    ELSE
        IF CompletionLight THEN
            StationState := 5;
        END_IF;

        CASE StationState OF
            0:
                IF SensorA AND ButtonARise THEN
                    StationState := 1;
                END_IF;

            1:
                IF SensorB THEN
                    StationState := 2;
                    IF ButtonBRise THEN
                        StationState := 3;
                    END_IF;
                END_IF;

            2:
                IF SensorB AND ButtonBRise THEN
                    StationState := 3;
                END_IF;

            3:
                IF SensorC THEN
                    StationState := 4;
                    IF ButtonCRise THEN
                        CompletionLight := TRUE;
                        StationState := 5;
                    END_IF;
                END_IF;

            4:
                IF SensorC AND ButtonCRise THEN
                    CompletionLight := TRUE;
                    StationState := 5;
                END_IF;

            5:
                IF NOT SensorC THEN
                    StationState := 0;
                END_IF;

            ELSE
                (* Invalid internal states recover stopped at A. *)
                StationState := 0;
        END_CASE;

        (* Destination sensors stop transport in the current scan. *)
        IF StationState = 1 THEN
            MotorForward := NOT SensorB;
        ELSIF StationState = 3 THEN
            MotorForward := NOT SensorC;
        END_IF;

        MotorReverse := FALSE;
    END_IF;
END_IF;

(* Sample edges in all modes and during startup to prevent queued events. *)
PreviousButtonA := ButtonA;
PreviousButtonB := ButtonB;
PreviousButtonC := ButtonC;
PreviousMode := Mode;

END_FUNCTION_BLOCK

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
    StartTrig : R_TRIG;
    FirstScan : BOOL := TRUE;
    StartBlocked : BOOL := FALSE;
    StartAccepted : BOOL := FALSE;
    AutoStep : INT := 1;
    AutoRunning : BOOL := FALSE;
    StepActionActive : BOOL := FALSE;
    ManualGripLatch : BOOL := FALSE;
    ManualReleaseLatch : BOOL := FALSE;
END_VAR

(*
    Semantic conflict note:
    - C6/K5 require ActivateGrip/ActivateRelease to be held until the corresponding
      limit switch is reached.
    - A general manual-mode reading says releasing a button stops that action.
    This implementation latches manual grip/release until their limit switches,
    prioritizing C6/K5. EmergencyStop still clears all outputs immediately per K4/C1.
*)

(* Safe default: no outputs in the current scan. *)
MoveDown := FALSE;
MoveUp := FALSE;
MoveLeft := FALSE;
MoveRight := FALSE;
ActivateGrip := FALSE;
ActivateRelease := FALSE;

StartTrig(CLK := Start);

IF FirstScan THEN
    (* C10: power-up scan produces no motion outputs. *)
    FirstScan := FALSE;
    AutoStep := 1;
    AutoRunning := FALSE;
    StepActionActive := FALSE;
    ManualGripLatch := FALSE;
    ManualReleaseLatch := FALSE;
    StartBlocked := Start;
ELSE
    StartAccepted := FALSE;

    IF NOT EmergencyStop THEN
        (* K4/C1: emergency stop active. Clear all actions and automatic progress. *)
        AutoStep := 1;
        AutoRunning := FALSE;
        StepActionActive := FALSE;
        ManualGripLatch := FALSE;
        ManualReleaseLatch := FALSE;
        IF Start THEN
            StartBlocked := TRUE;
        END_IF;

    ELSE
        (* EmergencyStop = TRUE: normal operation. Require a new Start after E-stop. *)
        IF StartBlocked AND NOT Start THEN
            StartBlocked := FALSE;
        END_IF;

        StartAccepted := StartTrig.Q AND NOT StartBlocked;

        IF ManualMode THEN
            (* K1/K2: manual mode. Automatic progress is stopped. *)
            AutoRunning := FALSE;
            StepActionActive := FALSE;

            MoveDown := DownButton AND NOT DownLimitSwitch;
            MoveUp := UpButton AND NOT UpLimitSwitch AND NOT MoveDown;

            MoveLeft := LeftButton AND NOT LeftLimitSwitch;
            MoveRight := RightButton AND NOT RightLimitSwitch AND NOT MoveLeft;

            (* Manual grip/release with C6/K5 latch until limit. *)
            IF GripButton AND NOT GripLimitSwitch THEN
                ManualGripLatch := TRUE;
            END_IF;
            IF GripLimitSwitch THEN
                ManualGripLatch := FALSE;
            END_IF;

            IF ReleaseButton AND NOT ReleaseLimitSwitch THEN
                ManualReleaseLatch := TRUE;
            END_IF;
            IF ReleaseLimitSwitch THEN
                ManualReleaseLatch := FALSE;
            END_IF;

            IF ManualGripLatch THEN
                ActivateGrip := TRUE;
                ActivateRelease := FALSE;
                ManualReleaseLatch := FALSE;
            ELSIF ManualReleaseLatch THEN
                ActivateRelease := TRUE;
                ActivateGrip := FALSE;
            ELSE
                ActivateGrip := FALSE;
                ActivateRelease := FALSE;
            END_IF;

        ELSIF SingleStepMode THEN
            (* K3: one programmed action per Start edge, then wait for next Start. *)
            AutoRunning := FALSE;
            ManualGripLatch := FALSE;
            ManualReleaseLatch := FALSE;

            IF StartAccepted AND NOT StepActionActive THEN
                StepActionActive := TRUE;
            END_IF;

            IF StepActionActive THEN
                CASE AutoStep OF
                    1: (* down to down limit *)
                        IF DownLimitSwitch THEN
                            StepActionActive := FALSE;
                            AutoStep := 2;
                        ELSE
                            MoveDown := TRUE;
                        END_IF;

                    2: (* grip until grip limit *)
                        IF GripLimitSwitch THEN
                            StepActionActive := FALSE;
                            AutoStep := 3;
                        ELSE
                            ActivateGrip := TRUE;
                        END_IF;

                    3: (* up to up limit *)
                        IF UpLimitSwitch THEN
                            StepActionActive := FALSE;
                            AutoStep := 4;
                        ELSE
                            MoveUp := TRUE;
                        END_IF;

                    4: (* right to right limit *)
                        IF RightLimitSwitch THEN
                            StepActionActive := FALSE;
                            AutoStep := 5;
                        ELSE
                            MoveRight := TRUE;
                        END_IF;

                    5: (* down to down limit *)
                        IF DownLimitSwitch THEN
                            StepActionActive := FALSE;
                            AutoStep := 6;
                        ELSE
                            MoveDown := TRUE;
                        END_IF;

                    6: (* release until release limit *)
                        IF ReleaseLimitSwitch THEN
                            StepActionActive := FALSE;
                            AutoStep := 7;
                        ELSE
                            ActivateRelease := TRUE;
                        END_IF;

                    7: (* up to up limit *)
                        IF UpLimitSwitch THEN
                            StepActionActive := FALSE;
                            AutoStep := 8;
                        ELSE
                            MoveUp := TRUE;
                        END_IF;

                    8: (* left to left limit *)
                        IF LeftLimitSwitch THEN
                            StepActionActive := FALSE;
                            AutoStep := 1;
                        ELSE
                            MoveLeft := TRUE;
                        END_IF;

                    ELSE
                        AutoStep := 1;
                        StepActionActive := FALSE;
                END_CASE;
            END_IF;

        ELSIF SingleCycleMode THEN
            (* Run one complete cycle, then stop and wait for a new Start. *)
            StepActionActive := FALSE;
            ManualGripLatch := FALSE;
            ManualReleaseLatch := FALSE;

            IF StartAccepted AND NOT AutoRunning THEN
                AutoRunning := TRUE;
                AutoStep := 1;
            END_IF;

            IF AutoRunning THEN
                CASE AutoStep OF
                    1:
                        IF DownLimitSwitch THEN
                            AutoStep := 2;
                        ELSE
                            MoveDown := TRUE;
                        END_IF;

                    2:
                        IF GripLimitSwitch THEN
                            AutoStep := 3;
                        ELSE
                            ActivateGrip := TRUE;
                        END_IF;

                    3:
                        IF UpLimitSwitch THEN
                            AutoStep := 4;
                        ELSE
                            MoveUp := TRUE;
                        END_IF;

                    4:
                        IF RightLimitSwitch THEN
                            AutoStep := 5;
                        ELSE
                            MoveRight := TRUE;
                        END_IF;

                    5:
                        IF DownLimitSwitch THEN
                            AutoStep := 6;
                        ELSE
                            MoveDown := TRUE;
                        END_IF;

                    6:
                        IF ReleaseLimitSwitch THEN
                            AutoStep := 7;
                        ELSE
                            ActivateRelease := TRUE;
                        END_IF;

                    7:
                        IF UpLimitSwitch THEN
                            AutoStep := 8;
                        ELSE
                            MoveUp := TRUE;
                        END_IF;

                    8:
                        IF LeftLimitSwitch THEN
                            AutoRunning := FALSE;
                            AutoStep := 1;
                        ELSE
                            MoveLeft := TRUE;
                        END_IF;

                    ELSE
                        AutoRunning := FALSE;
                        AutoStep := 1;
                END_CASE;
            END_IF;

        ELSIF ContinuousMode THEN
            (* Run the single-cycle handling sequence continuously. *)
            StepActionActive := FALSE;
            ManualGripLatch := FALSE;
            ManualReleaseLatch := FALSE;

            IF StartAccepted AND NOT AutoRunning THEN
                AutoRunning := TRUE;
                AutoStep := 1;
            END_IF;

            IF AutoRunning THEN
                CASE AutoStep OF
                    1:
                        IF DownLimitSwitch THEN
                            AutoStep := 2;
                        ELSE
                            MoveDown := TRUE;
                        END_IF;

                    2:
                        IF GripLimitSwitch THEN
                            AutoStep := 3;
                        ELSE
                            ActivateGrip := TRUE;
                        END_IF;

                    3:
                        IF UpLimitSwitch THEN
                            AutoStep := 4;
                        ELSE
                            MoveUp := TRUE;
                        END_IF;

                    4:
                        IF RightLimitSwitch THEN
                            AutoStep := 5;
                        ELSE
                            MoveRight := TRUE;
                        END_IF;

                    5:
                        IF DownLimitSwitch THEN
                            AutoStep := 6;
                        ELSE
                            MoveDown := TRUE;
                        END_IF;

                    6:
                        IF ReleaseLimitSwitch THEN
                            AutoStep := 7;
                        ELSE
                            ActivateRelease := TRUE;
                        END_IF;

                    7:
                        IF UpLimitSwitch THEN
                            AutoStep := 8;
                        ELSE
                            MoveUp := TRUE;
                        END_IF;

                    8:
                        IF LeftLimitSwitch THEN
                            AutoStep := 1;
                        ELSE
                            MoveLeft := TRUE;
                        END_IF;

                    ELSE
                        AutoStep := 1;
                END_CASE;
            END_IF;

        ELSE
            (* No valid mode selected: hold all outputs false. *)
            AutoRunning := FALSE;
            StepActionActive := FALSE;
            ManualGripLatch := FALSE;
            ManualReleaseLatch := FALSE;
        END_IF;
    END_IF;
END_IF;

END_FUNCTION_BLOCK

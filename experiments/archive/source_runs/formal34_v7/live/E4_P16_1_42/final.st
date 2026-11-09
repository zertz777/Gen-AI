FUNCTION_BLOCK FB_P16
VAR_INPUT
    processLength : USINT;
    sensor1 : BOOL;
    sensor2 : BOOL;
    sensor3 : BOOL;
    sensor4 : BOOL;
    sensor5 : BOOL;
    station1Start : BOOL;
    station2Complete : BOOL;
    station3Complete : BOOL;
    station4Complete : BOOL;
    processSequence : ARRAY[1..8] OF USINT;
END_VAR
VAR_OUTPUT
    conveyorLeft : BOOL := FALSE;
    conveyorRight : BOOL := FALSE;
END_VAR
VAR
    (* States: 0 idle, 1 transfer, 2 processing, 3 latched error. *)
    state : USINT := 0;
    bootScans : USINT := 0;
    stepIndex : USINT := 0;
    activeLength : USINT := 0;
    activeSequence : ARRAY[1..8] OF USINT;
    currentStation : USINT := 1;
    targetStation : USINT := 0;

    previousStart : BOOL := FALSE;
    startRise : BOOL;
    invalidSequence : BOOL;
    errorLatched : BOOL := FALSE;

    targetPresent : BOOL;
    processingPresent : BOOL;
    processingComplete : BOOL;

    (* Ten complete scans following every left-running scan block right. *)
    rightInhibitScans : USINT := 0;
    rightBlocked : BOOL;
    i : INT;
END_VAR

(* Each invocation is one 20 ms scan.
   The recipe is copied when a new workpiece is accepted.
   No reset input exists: a latched error requires FB reinitialization.
   Completion inputs are valid levels, qualified by the station sensor.
   No compilation or cycle-test verification is claimed. *)

conveyorLeft := FALSE;
conveyorRight := FALSE;

startRise := station1Start AND NOT previousStart;
previousStart := station1Start;

rightBlocked := rightInhibitScans > 0;
IF rightInhibitScans > 0 THEN
    rightInhibitScans := rightInhibitScans - 1;
END_IF;

(* Validate only the active entries; never index with an invalid length. *)
invalidSequence := FALSE;
IF (processLength < 1) OR (processLength > 8) THEN
    invalidSequence := TRUE;
ELSE
    FOR i := 1 TO 8 DO
        IF i <= USINT_TO_INT(processLength) THEN
            IF i = USINT_TO_INT(processLength) THEN
                IF processSequence[i] <> 5 THEN
                    invalidSequence := TRUE;
                END_IF;
            ELSE
                IF (processSequence[i] < 2)
                    OR (processSequence[i] > 4) THEN
                    invalidSequence := TRUE;
                END_IF;
            END_IF;
        END_IF;
    END_FOR;
END_IF;

IF invalidSequence THEN
    errorLatched := TRUE;
END_IF;

IF errorLatched THEN
    state := 3;
    stepIndex := 0;
END_IF;

(* Both initial scans are stopped, covering G[0,1]. *)
IF bootScans < 2 THEN
    bootScans := bootScans + 1;
ELSIF NOT errorLatched THEN
    CASE state OF
        0:
            IF startRise AND sensor1 THEN
                activeLength := processLength;
                FOR i := 1 TO 8 DO
                    activeSequence[i] := processSequence[i];
                END_FOR;
                stepIndex := 1;
                currentStation := 1;
                targetStation := activeSequence[1];
                state := 1;
            END_IF;

        1:
            (* Transfer and arrival are evaluated below. *)

        2:
            processingPresent := FALSE;
            processingComplete := FALSE;

            CASE currentStation OF
                2:
                    processingPresent := sensor2;
                    processingComplete := station2Complete;
                3:
                    processingPresent := sensor3;
                    processingComplete := station3Complete;
                4:
                    processingPresent := sensor4;
                    processingComplete := station4Complete;
            END_CASE;

            IF processingPresent AND processingComplete THEN
                IF stepIndex < activeLength THEN
                    stepIndex := stepIndex + 1;
                    targetStation := activeSequence[stepIndex];
                    state := 1;
                ELSE
                    (* Unreachable for a valid captured recipe. *)
                    errorLatched := TRUE;
                    state := 3;
                END_IF;
            END_IF;

        3:
            (* Latched error: outputs remain stopped. *)

        ELSE
            errorLatched := TRUE;
            state := 3;
    END_CASE;

    IF state = 1 THEN
        targetPresent := FALSE;
        CASE targetStation OF
            2: targetPresent := sensor2;
            3: targetPresent := sensor3;
            4: targetPresent := sensor4;
            5: targetPresent := sensor5;
            ELSE
                errorLatched := TRUE;
                state := 3;
        END_CASE;

        IF state = 1 THEN
            IF targetPresent THEN
                currentStation := targetStation;
                IF targetStation = 5 THEN
                    state := 0;
                    stepIndex := 0;
                ELSE
                    state := 2;
                END_IF;
            ELSIF targetStation < currentStation THEN
                conveyorLeft := TRUE;
            ELSIF targetStation > currentStation THEN
                IF NOT rightBlocked THEN
                    conveyorRight := TRUE;
                END_IF;
            END_IF;
            (* Consecutive identical stations require no conveyor motion.
               Their entries are consumed separately, only with sensor
               and completion valid in the processing state. *)
        END_IF;
    END_IF;
END_IF;

IF errorLatched THEN
    conveyorLeft := FALSE;
    conveyorRight := FALSE;
END_IF;

IF conveyorLeft THEN
    conveyorRight := FALSE;
    rightInhibitScans := 10;
END_IF;

END_FUNCTION_BLOCK

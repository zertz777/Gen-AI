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
    conveyorLeft : BOOL;
    conveyorRight : BOOL;
END_VAR
VAR
    (* --- internal state --- *)
    state : INT := 0;           (* 0=IDLE 1=MOVING 2=WAIT_COMPLETE 3=DONE 4=ERROR   *)
    stepIdx : INT := 0;         (* index into processSequence for the active work piece  *)
    currentStation : INT := 0;  (* station where the work piece currently is           *)
    targetStation : INT := 0;   (* commanded destination station                       *)
    dir : INT := 0;             (* -1 = left, 0 = stop, +1 = right (this scan)         *)
    cd : INT := 0;              (* C9 dead band: block a right run after a left run    *)
    sensorAtTarget : BOOL := FALSE;
    completionSignal : BOOL := FALSE;
    zeroNow : BOOL := FALSE;
    lenI : INT := 0;            (* processLength expressed as INT for comparisons      *)
END_VAR

(* ============================================================================
   FB_P16  Flexible Processing Control           scan cycle = 20 ms
   ----------------------------------------------------------------------------
   Direction convention (derived, not an interface): stations are numbered
   1#..5# left to right, so a move towards a HIGHER station number is
   conveyorRight and a move towards a LOWER station number is conveyorLeft.

   Output model: the conveyor outputs are DIRECT (combinationally derived from
   the direction command computed in the SAME scan). The start condition is
   therefore effective in the scan in which it appears, and an arrival stops
   the belt in the scan in which the target sensor is seen; the next segment is
   issued in the scan in which the station completion signal is seen (K3), with
   no artificial extra delay.

   C9 (no left->right switch inside 200 ms) is realised as an OUTPUT-LEVEL
   suppression of conveyorRight for 10 scans after a left command, so that it
   never delays a legitimately requested right move that is not a reversal.

   Reported semantic conflict (kept, not silently resolved):
     * K4  => processLength outside the array range means ERROR + stop.
     * C1  => processLength = 0 means "empty process": the conveyor must not run.
   Implementation: processLength = 0  -> no start and outputs forced off (C1);
                   processLength > 8  -> ERROR state, conveyor stopped (K4).
   ============================================================================ *)

(* --- 1) normalise processLength to INT to keep comparisons type-safe --- *)
lenI := USINT_TO_INT(processLength);

(* --- 2) empty-process flag (C1) --- *)
zeroNow := (lenI = 0);

(* --- 3) current target sensor --- *)
sensorAtTarget := FALSE;
CASE targetStation OF
    1: sensorAtTarget := sensor1;
    2: sensorAtTarget := sensor2;
    3: sensorAtTarget := sensor3;
    4: sensorAtTarget := sensor4;
    5: sensorAtTarget := sensor5;
ELSE
    sensorAtTarget := FALSE;
END_CASE;

(* --- 4) completion signal of the station currently occupied --- *)
completionSignal := FALSE;
CASE currentStation OF
    2: completionSignal := station2Complete;
    3: completionSignal := station3Complete;
    4: completionSignal := station4Complete;
ELSE
    completionSignal := FALSE;
END_CASE;

(* --- 5) state machine --- *)
dir := 0;

CASE state OF

    0: (* ---------------- IDLE ---------------- *)
        IF lenI > 8 THEN
            state := 4;                                  (* K4 *)
        ELSIF (lenI >= 1) AND station1Start AND sensor1 THEN
            stepIdx := 1;
            currentStation := 1;
            targetStation := USINT_TO_INT(processSequence[1]);
            IF (targetStation < 1) OR (targetStation > 5) THEN
                state := 4;                              (* K4: bad station number *)
            ELSE
                IF targetStation > currentStation THEN
                    dir := 1;
                ELSIF targetStation < currentStation THEN
                    dir := -1;
                ELSE
                    dir := 0;
                END_IF;
                state := 1;
            END_IF;
        END_IF;

    1: (* ---------------- MOVING ---------------- *)
        IF sensorAtTarget THEN
            dir := 0;
            currentStation := targetStation;
            IF currentStation = 5 THEN
                state := 3;                              (* delivered to 5# *)
            ELSE
                state := 2;                              (* wait for processing *)
            END_IF;
        ELSIF targetStation > currentStation THEN
            dir := 1;
        ELSIF targetStation < currentStation THEN
            dir := -1;
        ELSE
            dir := 0;
        END_IF;

    2: (* ------------- WAIT COMPLETE ------------ *)
        dir := 0;
        (* K3: arrival sensor of the station AND its completion signal *)
        IF sensorAtTarget AND completionSignal THEN
            stepIdx := stepIdx + 1;
            IF (stepIdx < 1) OR (stepIdx > 8) OR (stepIdx > lenI) THEN
                state := 4;                              (* sequence exhausted / K1+K4 *)
            ELSE
                targetStation := USINT_TO_INT(processSequence[stepIdx]);
                IF (targetStation < 1) OR (targetStation > 5) THEN
                    state := 4;                          (* K4 *)
                ELSE
                    IF targetStation > currentStation THEN
                        dir := 1;
                    ELSIF targetStation < currentStation THEN
                        dir := -1;
                    ELSE
                        dir := 0;
                    END_IF;
                    state := 1;
                END_IF;
            END_IF;
        END_IF;

    3: (* ---------------- DONE ----------------- *)
        dir := 0;
        stepIdx := 0;
        currentStation := 0;
        state := 0;

    4: (* ---------------- ERROR ---------------- *)
        dir := 0;
        stepIdx := 0;
        currentStation := 0;
        IF (lenI >= 1) AND (lenI <= 8) THEN
            state := 0;                                  (* recover when input is sane *)
        END_IF;

ELSE
    dir := 0;
    state := 0;

END_CASE;

(* --- 6) empty process must not drive the conveyor (C1) --- *)
IF zeroNow THEN
    dir := 0;
END_IF;

(* --- 7) C9 dead band: after a left command, forbid right for 10 scans --- *)
IF dir = -1 THEN
    cd := 10;
ELSIF cd > 0 THEN
    cd := cd - 1;
END_IF;

(* --- 8) mutually exclusive outputs (C2, C4) with the C9 guard --- *)
conveyorLeft  := (dir = -1);
conveyorRight := (dir =  1) AND (cd = 0);

END_FUNCTION_BLOCK

FUNCTION_BLOCK FB_P09
VAR_INPUT
    cyclicExecution : BOOL;
    trigger : BOOL;
    value : LREAL;
    windowSize : INT;
    reset : BOOL;
END_VAR
VAR_OUTPUT
    average : LREAL := 0.0;
    windowSizeReached : BOOL := FALSE;
    error : BOOL := FALSE;
    status : WORD := 16#0000;
END_VAR
VAR
    buffer : ARRAY[0..99] OF LREAL;
    writeIndex : INT := 0;
    sampleCount : INT := 0;
    prevTrigger : BOOL := FALSE;
    newSample : BOOL := FALSE;
    triggerEdge : BOOL := FALSE;
    i : INT;
    idx : INT;
    sum : LREAL;
END_VAR

(* --------------------------------------------------------------- *)
(* K3 / C3 / C3b: window size must be within 1..100                 *)
(* --------------------------------------------------------------- *)
IF (windowSize < 1) OR (windowSize > 100) THEN
    error := TRUE;
    status := 16#8200;
ELSE
    error := FALSE;
    status := 16#0000;
END_IF

(* --------------------------------------------------------------- *)
(* C2: windowSizeReached and error must never both be TRUE          *)
(* --------------------------------------------------------------- *)
IF error THEN
    windowSizeReached := FALSE;
END_IF

(* --------------------------------------------------------------- *)
(* K4 / C1: reset has priority over cyclic execution and trigger    *)
(* --------------------------------------------------------------- *)
IF reset THEN
    writeIndex := 0;
    sampleCount := 0;
    average := 0.0;
    windowSizeReached := FALSE;
    FOR i := 0 TO 99 DO
        buffer[i] := 0.0;
    END_FOR;
    prevTrigger := trigger;
ELSIF error THEN
    (* K3: invalid window -> do not update average, keep last value *)
    prevTrigger := trigger;
ELSE
    (* keep ring-buffer consistent if windowSize changed while running *)
    IF writeIndex >= windowSize THEN
        writeIndex := 0;
    END_IF
    IF sampleCount > windowSize THEN
        sampleCount := windowSize;
    END_IF

    (* K2: detect rising edge of external trigger *)
    triggerEdge := trigger AND NOT prevTrigger;

    (* K1 / K2: cyclic execution takes precedence; no double counting *)
    newSample := FALSE;
    IF cyclicExecution THEN
        newSample := TRUE;
    ELSIF triggerEdge THEN
        newSample := TRUE;
    END_IF

    IF newSample THEN
        buffer[writeIndex] := value;
        writeIndex := writeIndex + 1;
        IF writeIndex >= windowSize THEN
            writeIndex := 0;
        END_IF
        IF sampleCount < windowSize THEN
            sampleCount := sampleCount + 1;
        END_IF

        (* arithmetic mean over the sampleCount most recent samples *)
        sum := 0.0;
        FOR i := 0 TO sampleCount - 1 DO
            idx := (writeIndex - 1 - i) MOD windowSize;
            IF idx < 0 THEN
                idx := idx + windowSize;
            END_IF
            sum := sum + buffer[idx];
        END_FOR
        average := sum / INT_TO_LREAL(sampleCount);

        IF sampleCount >= windowSize THEN
            windowSizeReached := TRUE;
        ELSE
            windowSizeReached := FALSE;
        END_IF
    END_IF

    prevTrigger := trigger;
END_IF

END_FUNCTION_BLOCK

FUNCTION_BLOCK FB_P09
VAR_INPUT
    cyclicExecution : BOOL;
    trigger : BOOL;
    value : LREAL;
    windowSize : INT;
    reset : BOOL;
END_VAR
VAR_OUTPUT
    average : LREAL;
    windowSizeReached : BOOL;
    error : BOOL;
    status : WORD;
END_VAR
VAR
    buffer : ARRAY[0..99] OF LREAL;
    writeIndex : INT := 0;
    sampleCount : INT := 0;
    prevTrigger : BOOL := FALSE;
    i : INT;
    n : INT;
    startIdx : INT;
    idx : INT;
    sumLocal : LREAL;
    validWindow : BOOL;
    addSample : BOOL;
END_VAR

(* Reset has priority over cyclic execution and trigger. *)
IF reset THEN
    writeIndex := 0;
    sampleCount := 0;
    average := 0.0;
    windowSizeReached := FALSE;
END_IF;

validWindow := (windowSize >= 1) AND (windowSize <= 100);

addSample := FALSE;
IF NOT reset AND validWindow THEN
    IF cyclicExecution THEN
        addSample := TRUE;
    ELSIF trigger AND NOT prevTrigger THEN
        addSample := TRUE;
    END_IF;
END_IF;

IF addSample THEN
    buffer[writeIndex] := value;
    writeIndex := writeIndex + 1;
    IF writeIndex >= 100 THEN
        writeIndex := 0;
    END_IF;
    sampleCount := sampleCount + 1;
    IF sampleCount > 100 THEN
        sampleCount := 100;
    END_IF;
END_IF;

IF NOT validWindow THEN
    error := TRUE;
    status := 16#8200;
    windowSizeReached := FALSE;
ELSE
    error := FALSE;
    status := 16#0000;

    n := sampleCount;
    IF n > windowSize THEN
        n := windowSize;
    END_IF;

    IF n <= 0 THEN
        average := 0.0;
        windowSizeReached := FALSE;
    ELSE
        startIdx := writeIndex - n;
        IF startIdx < 0 THEN
            startIdx := startIdx + 100;
        END_IF;

        idx := startIdx;
        sumLocal := 0.0;
        FOR i := 1 TO n DO
            sumLocal := sumLocal + buffer[idx];
            idx := idx + 1;
            IF idx >= 100 THEN
                idx := 0;
            END_IF;
        END_FOR;

        average := sumLocal / INT_TO_LREAL(n);
        windowSizeReached := (sampleCount >= windowSize);
    END_IF;
END_IF;

prevTrigger := trigger;

END_FUNCTION_BLOCK

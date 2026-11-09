FUNCTION_BLOCK FB_P18
VAR_INPUT
    enqueue : BOOL;
    dequeue : BOOL;
    reset : BOOL;
END_VAR
VAR_OUTPUT
    elementCount : DINT := 0;
    status : WORD := WORD#16#0000;
END_VAR
VAR_IN_OUT
    item : INT;
    buffer : ARRAY[*] OF INT;
END_VAR
VAR
    prevEnqueue : BOOL := FALSE;
    prevDequeue : BOOL := FALSE;
    head : DINT := 0;
    tail : DINT := 0;
    count : DINT := 0;
    capacity : DINT;
    lowerBound : DINT;
    idx : DINT;
END_VAR

// Derive queue capacity from the actual length of the caller-supplied buffer
capacity := UPPER_BOUND(buffer, 1) - LOWER_BOUND(buffer, 1) + 1;
lowerBound := LOWER_BOUND(buffer, 1);

// Reset takes priority over enqueue and dequeue
IF reset THEN
    head := 0;
    tail := 0;
    count := 0;
    elementCount := 0;
    status := WORD#16#0000;
ELSIF enqueue AND NOT prevEnqueue THEN
    IF count >= capacity THEN
        status := WORD#16#8002; // enqueue rejected: queue full
    ELSE
        idx := lowerBound + tail;
        buffer[idx] := item;
        tail := tail + 1;
        IF tail >= capacity THEN
            tail := 0;
        END_IF;
        count := count + 1;
        status := WORD#16#0000;
    END_IF;
    elementCount := count;
ELSIF dequeue AND NOT prevDequeue THEN
    IF count <= 0 THEN
        status := WORD#16#8001; // dequeue rejected: queue empty
    ELSE
        idx := lowerBound + head;
        item := buffer[idx];
        head := head + 1;
        IF head >= capacity THEN
            head := 0;
        END_IF;
        count := count - 1;
        status := WORD#16#0000;
    END_IF;
    elementCount := count;
ELSE
    elementCount := count;
    status := WORD#16#0000;
END_IF;

// Update edge detection memory for next invocation
prevEnqueue := enqueue;
prevDequeue := dequeue;

END_FUNCTION_BLOCK

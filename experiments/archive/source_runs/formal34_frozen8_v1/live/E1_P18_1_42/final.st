FUNCTION_BLOCK FB_P18
VAR_INPUT
    enqueue : BOOL;
    dequeue : BOOL;
    reset : BOOL;
END_VAR
VAR_OUTPUT
    elementCount : DINT;
    status : WORD;
END_VAR
VAR_IN_OUT
    item : INT;
    buffer : ARRAY[*] OF INT;
END_VAR
VAR
    (* internal state; not exposed through the interface *)
    enqueuePrev : BOOL := FALSE;
    dequeuePrev : BOOL := FALSE;
    head : DINT := 0;
    tail : DINT := 0;
    count : DINT := 0;
    lower : DINT := 0;
    capacity : DINT := 0;
    idx : DINT := 0;
    enqueueRise : BOOL := FALSE;
    dequeueRise : BOOL := FALSE;
END_VAR

(* derive lower bound and capacity from the actual caller-supplied buffer *)
lower := LOWER_BOUND(buffer, 1);
capacity := UPPER_BOUND(buffer, 1) - lower + 1;

(* one operation per rising edge *)
enqueueRise := enqueue AND NOT enqueuePrev;
dequeueRise := dequeue AND NOT dequeuePrev;
enqueuePrev := enqueue;
dequeuePrev := dequeue;

(* default status: no error this invocation *)
status := 16#0000;

IF reset THEN
    (* reset has priority over enqueue and dequeue *)
    head := 0;
    tail := 0;
    count := 0;
ELSIF enqueueRise THEN
    IF count < capacity THEN
        idx := lower + tail;
        buffer[idx] := item;
        tail := tail + 1;
        IF tail >= capacity THEN
            tail := 0;
        END_IF;
        count := count + 1;
    ELSE
        (* queue is full: reject, leave queue and item unchanged *)
        status := 16#8002;
    END_IF;
ELSIF dequeueRise THEN
    IF count > 0 THEN
        idx := lower + head;
        item := buffer[idx];
        head := head + 1;
        IF head >= capacity THEN
            head := 0;
        END_IF;
        count := count - 1;
    ELSE
        (* queue is empty: reject, leave queue and item unchanged *)
        status := 16#8001;
    END_IF;
END_IF;

elementCount := count;

END_FUNCTION_BLOCK

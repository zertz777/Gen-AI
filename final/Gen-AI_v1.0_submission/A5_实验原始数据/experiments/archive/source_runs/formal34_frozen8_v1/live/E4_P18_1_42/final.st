FUNCTION_BLOCK FB_P18
VAR_INPUT
    enqueue : BOOL;
    dequeue : BOOL;
    reset : BOOL;
END_VAR
VAR_OUTPUT
    elementCount : DINT := 0;
    status : WORD := 16#0000;
END_VAR
VAR_IN_OUT
    item : INT;
    buffer : ARRAY[*] OF INT;
END_VAR
VAR
    initialized : BOOL := FALSE;
    previousEnqueue : BOOL := FALSE;
    previousDequeue : BOOL := FALSE;
    enqueueEdge : BOOL;
    dequeueEdge : BOOL;
    head : DINT := 0;
    tail : DINT := 0;
    lowerIndex : DINT;
    upperIndex : DINT;
    capacity : DINT;
END_VAR

(*
    编译profile须支持VAR_IN_OUT开放数组及LOWER_BOUND/UPPER_BOUND。
    本源码未经过编译或逐周期测试验证。

    待审语义冲突：
    首次调用若enqueue=TRUE且reset=FALSE，K2要求入队，
    而C10要求该调用输出elementCount=0；两者不能同时满足。
    本实现先建立空队列初态，再执行该调用的上升沿操作，
    因而上述输入下遵循K2，但不满足C10的当拍输出断言。
    此冲突仍待需求方裁定。

    调用方须提供非空数组，且容量须能由DINT表示；
    同一队列存续期间须保持绑定的缓冲区及其边界不变。
    同时请求入队和出队违反调用方前置条件：
    本实现不执行操作，不新增未定义的状态码。
*)

lowerIndex := LOWER_BOUND(buffer, 1);
upperIndex := UPPER_BOUND(buffer, 1);
capacity := upperIndex - lowerIndex + 1;

IF NOT initialized THEN
    head := 0;
    tail := 0;
    elementCount := 0;
    previousEnqueue := FALSE;
    previousDequeue := FALSE;
    initialized := TRUE;
END_IF;

enqueueEdge := enqueue AND NOT previousEnqueue;
dequeueEdge := dequeue AND NOT previousDequeue;

(* 复位期间也采样输入，避免持续高电平在复位释放后重复触发。 *)
previousEnqueue := enqueue;
previousDequeue := dequeue;

status := 16#0000;

IF reset THEN
    head := 0;
    tail := 0;
    elementCount := 0;

ELSIF enqueue AND dequeue THEN
    (* 非法的同时请求：保持队列、缓冲区及item。 *)

ELSIF enqueueEdge THEN
    IF elementCount = capacity THEN
        status := 16#8002;
    ELSE
        buffer[lowerIndex + tail] := item;
        IF tail = capacity - 1 THEN
            tail := 0;
        ELSE
            tail := tail + 1;
        END_IF;
        elementCount := elementCount + 1;
    END_IF;

ELSIF dequeueEdge THEN
    IF elementCount = 0 THEN
        status := 16#8001;
    ELSE
        item := buffer[lowerIndex + head];
        IF head = capacity - 1 THEN
            head := 0;
        ELSE
            head := head + 1;
        END_IF;
        elementCount := elementCount - 1;
    END_IF;
END_IF;

END_FUNCTION_BLOCK

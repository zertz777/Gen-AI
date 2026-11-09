(*
需求原文：
Write a function block FB implementing a First-In-First-Out (FIFO) circular queue for INT items. Derive queue capacity from the actual length of the caller-supplied INT buffer.

1. Each rising edge of enqueue requests one enqueue operation. If the queue is not full, append the current item value to its tail.
2. Each rising edge of dequeue requests one dequeue operation. If the queue is not empty, remove its front element and write that value back to item. The caller must not request enqueue and dequeue in the same invocation.
3. When reset is TRUE, empty the queue and set elementCount to zero. Reset takes priority over enqueue and dequeue; stored buffer values need not be overwritten.
4. Output the current number of valid elements through elementCount. Zero means the queue is empty; a count equal to the actual buffer array length means it is full.
5. Reject a dequeue request on an empty queue or an enqueue request on a full queue. Leave the queue and item unchanged and report the reason through status.
6. The queue is empty on its first invocation. Define head and tail positions and other internal state within the implementation; do not expose them as interface parameters.

Status codes:
- 16#0000: No error in this invocation, including idle, reset and successful operations.
- 16#8001: The dequeue request was rejected because the queue is empty.
- 16#8002: The enqueue request was rejected because the queue is full.

中文摘要：FIFO 环形队列：入队/出队按上升沿各触发一次，
reset 优先清空，空队出队或满队入队被拒绝并给出状态码。

任务：P18，FIFO First-In-First-Out Queue。
每次调用代表一个 20 ms 扫描周期。
buffer 为调用者提供的非空一维 INT 数组。
初态：head = tail = 0；elementCount = 0；status = 16#0000。
head、tail 使用相对于数组下界的偏移，不要求数组下界为零。

完整形式化规约：
# task: P18
# meta: hard / B 模拟量与数据处理
# spec: version 1.0, updated 2026-10-30, scan cycle 20 ms
# 条款号对齐任务书 3.4 的条款库 C1—C10；[a,b] 单位为扫描周期。

C1: G(reset -> elementCount == 0)
    复位当周期队列必须清空，优先于同周期的入队/出队。（K1）
C4: G(reset && enqueue -> elementCount == 0)
    复位与入队同时请求时当拍以复位为准。（K1）
C2: G(elementCount >= 0)
    元素计数不得为负。（K3/K4）
C9: G(status == 16#8001 -> elementCount == 0)
    空队出队被拒绝时仍为空。（K3）
C10: G[0,0](elementCount == 0)
    上电当拍队列为空。（初态）

语义冲突报告：
若 C10 指首次调用结束后的输出，则它与“每个入队上升沿均执行”
在首次调用 enqueue = TRUE 且 reset = FALSE 时冲突。
本实现将初态定义为首次调用处理请求之前的空队列，
并处理首次调用的上升沿；因此不能声称满足上述扫描后解释的 C10。

实现约定：
复位也采样请求电平，复位期间出现的上升沿不会延迟执行。
同时置位 enqueue 与 dequeue 违反调用约束；本实现不执行任何
队列操作，但仍采样电平。没有新增未定义的错误码。
非空队列使用期间，调用者须保持同一个缓冲区及其边界不变。

编译与测试说明：
保留 ARRAY[*] OF INT，使用 LOWER_BOUND 和 UPPER_BOUND。
需由支持开放数组及其边界查询的编译 profile 验证。
当前对话未提供可执行工具或已配置的测试命令，
未运行真实编译器或逐周期测试，不声称已经验证正确。
*)

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
    initialized : BOOL := FALSE;
    previousEnqueue : BOOL := FALSE;
    previousDequeue : BOOL := FALSE;
    enqueueEdge : BOOL := FALSE;
    dequeueEdge : BOOL := FALSE;
    head : DINT := 0;
    tail : DINT := 0;
    lowerBound : DINT;
    upperBound : DINT;
    capacity : DINT;
END_VAR

lowerBound := LOWER_BOUND(buffer, 1);
upperBound := UPPER_BOUND(buffer, 1);
capacity := upperBound - lowerBound + 1;

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
status := WORD#16#0000;

IF reset THEN
    head := 0;
    tail := 0;
    elementCount := 0;
ELSIF NOT (enqueue AND dequeue) THEN
    IF enqueueEdge THEN
        IF elementCount >= capacity THEN
            status := WORD#16#8002;
        ELSE
            buffer[lowerBound + tail] := item;
            IF tail = capacity - 1 THEN
                tail := 0;
            ELSE
                tail := tail + 1;
            END_IF;
            elementCount := elementCount + 1;
        END_IF;
    ELSIF dequeueEdge THEN
        IF elementCount = 0 THEN
            status := WORD#16#8001;
        ELSE
            item := buffer[lowerBound + head];
            IF head = capacity - 1 THEN
                head := 0;
            ELSE
                head := head + 1;
            END_IF;
            elementCount := elementCount - 1;
        END_IF;
    END_IF;
END_IF;

previousEnqueue := enqueue;
previousDequeue := dequeue;

END_FUNCTION_BLOCK

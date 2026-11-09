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
    status : WORD := WORD#16#0000;
END_VAR
VAR
    samples : ARRAY[0..99] OF LREAL;
    writeIndex : INT := 0;
    sampleCount : INT := 0;
    activeWindowSize : INT := 0;
    previousTrigger : BOOL := FALSE;
    risingEdge : BOOL := FALSE;
    acquire : BOOL := FALSE;
    validWindow : BOOL := FALSE;
    total : LREAL := 0.0;
    i : INT := 0;
END_VAR

(*
需求原文：
Write a function block FB that calculates and updates a moving arithmetic mean.
The moving arithmetic mean is a method of averaging over consecutive data
points, where each new data point replaces the oldest data point, and then
the average is recalculated.

1. When cyclicExecution is TRUE, a new data value is automatically read and
   the moving average average is updated every scan cycle.
2. Provide an external trigger signal trigger, which reads a new data value
   and updates the moving average upon each rising edge.
3. Provide a reset function reset, which resets the moving average calculation
   when the reset signal is TRUE. If the window size is less than 1 or greater
   than 100, output an error status and status code.

The status parameter indicates the execution status of the program:
- 16#0000: Execution successful
- 16#8200: Window length setting error, please set a value between 1 and 100.

接口保持原名称、方向和类型。
cyclicExecution 为 TRUE 时，trigger 不影响采样，每扫描最多采样一次。
扫描周期：20 ms。窗口容量：1..100。
初态：窗口为空，average = 0.0，windowSizeReached = FALSE，
error = FALSE，status = 16#0000，写入指针 = 0。

约束：
K1 cyclicExecution = TRUE 时每个扫描周期读入一个新数据并更新 average。
K2 trigger 的每个上升沿读入一个新数据并更新 average，
   与周期模式二选一，不重复计数。
K3 windowSize 不在 1..100 时置 error = TRUE、status = 16#8200，
   且不更新 average。
K4 reset = TRUE 时清空窗口、把 windowSizeReached 置 FALSE，
   其优先级高于 cyclicExecution 与 trigger。

完整形式化规约：
# task: P09
# meta: medium / B 模拟量与数据处理
# spec: version 1.0, updated 2026-10-30, scan cycle 20 ms
# 条款号对齐任务书 3.4 的条款库 C1—C10；[a,b] 单位为扫描周期。

C1: G(reset -> !windowSizeReached)
    -- 复位当周期必须清除窗口满标志（复位优先于周期与触发）（K4）
C3: G(windowSize < 1 -> F[0,1](error))
    -- 窗口长度小于 1 时必须报错（不得静默）（K3）
C3b: G(windowSize > 100 -> F[0,1](error))
     -- 窗口长度大于 100 时必须报错（K3）
C2: G(windowSizeReached -> !error)
    -- 窗口满标志与错误标志不得同时为真（K3）
C10: G[0,1](!windowSizeReached && !error && average == 0.0)
     -- 上电首周期无窗口、无错误、平均值为 0（初态）

原始数据告警：
semantic_warnings、warnings、missing_fields、dialect_requirements 均为空；
type_origins 为空。

语义冲突报告：
C10 若约束上电后的实际扫描输出，则与 K1 存在冲突：
首扫描周期启用周期采样且 value 非零时，average 必须更新。
首扫描窗口长度为 1 时，满标志也必须置 TRUE。
初始扫描持续非法窗口时，C10 与 C3/C3b 的限时报错亦存在冲突。
本实现保留声明初态，但实际调用立即执行采样及校验，
不通过延迟采样或屏蔽错误来声称同时满足这些冲突条款。

边界选择：
有效窗口长度改变时清空旧窗口；当周期允许采样时立即采入新值。
未填满窗口时，按实际已采集数量计算平均值。
非法窗口时冻结 average 和采样数据，并清除满标志。
非法窗口与 reset 同时出现时清空内部窗口，但依据 K3 保留 average；
恢复有效配置后空窗口的 average 归零，或更新为当周期新样本。
trigger 历史每扫描更新，包括周期模式、复位和错误期间，
因此不会在模式切换或恢复时补采已经发生的上升沿。

实现变更：
替换占位 RETURN，增加固定容量窗口、采样沿检测、复位及错误处理。
当前对话无编译或测试执行工具，也未提供测试命令；
未执行编译或逐周期测试，未声称已经验证正确。
*)

risingEdge := trigger AND NOT previousTrigger;
previousTrigger := trigger;

validWindow := (windowSize >= 1) AND (windowSize <= 100);
acquire := cyclicExecution OR risingEdge;

error := NOT validWindow;
IF validWindow THEN
    status := WORD#16#0000;
ELSE
    status := WORD#16#8200;
END_IF;

IF reset THEN
    FOR i := 0 TO 99 DO
        samples[i] := 0.0;
    END_FOR;
    writeIndex := 0;
    sampleCount := 0;
    total := 0.0;
    activeWindowSize := 0;
    windowSizeReached := FALSE;

    IF validWindow THEN
        activeWindowSize := windowSize;
        average := 0.0;
    END_IF;

ELSIF NOT validWindow THEN
    windowSizeReached := FALSE;

ELSE
    IF activeWindowSize <> windowSize THEN
        FOR i := 0 TO 99 DO
            samples[i] := 0.0;
        END_FOR;
        writeIndex := 0;
        sampleCount := 0;
        total := 0.0;
        average := 0.0;
        activeWindowSize := windowSize;
    END_IF;

    IF acquire THEN
        samples[writeIndex] := value;

        IF sampleCount < activeWindowSize THEN
            sampleCount := sampleCount + 1;
        END_IF;

        writeIndex := writeIndex + 1;
        IF writeIndex >= activeWindowSize THEN
            writeIndex := 0;
        END_IF;

        total := 0.0;
        FOR i := 0 TO sampleCount - 1 DO
            total := total + samples[i];
        END_FOR;

        average := total / INT_TO_LREAL(sampleCount);
    ELSIF sampleCount = 0 THEN
        average := 0.0;
    END_IF;

    windowSizeReached := (sampleCount = activeWindowSize);
END_IF;

END_FUNCTION_BLOCK

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
    samples : ARRAY[0..99] OF LREAL;
    writeIndex : INT := 0;
    sampleCount : INT := 0;
    previousTrigger : BOOL := FALSE;
    triggerRise : BOOL;
    validWindow : BOOL;
    acquire : BOOL;
    readIndex : INT;
    i : INT;
    divisor : LREAL;
    meanValue : LREAL;
END_VAR

(*
    待审语义冲突：
    C10 若约束上电后的实际扫描输出始终为零且无错误，则与首扫描
    cyclicExecution=TRUE 时 K1 的采样要求，以及非法 windowSize 时
    K3 的立即报错要求不能同时满足。
    本实现保留指定的声明初态；实际扫描执行 K1、K3、K4，
    不通过跳过首扫描来声称满足 C10。

    reset 与非法 windowSize 同时出现时，清空内部窗口并清除满标志，
    但按 K3 保持 average；这与将 reset 理解为无条件输出零存在冲突，
    留待需求确认。

    窗口在线变更未给出规则。本实现采用保留已有最新样本的处理：
    缩小时丢弃超出新长度的最旧样本；扩大时不恢复已丢弃样本。
    该处理属于待审实现约定，并非新增的外部接口要求。
    未声称经过编译或逐周期功能验证。
*)

triggerRise := trigger AND NOT previousTrigger;
previousTrigger := trigger;

validWindow := (windowSize >= 1) AND (windowSize <= 100);
error := NOT validWindow;

IF validWindow THEN
    status := 16#0000;
ELSE
    status := 16#8200;
END_IF;

IF reset THEN
    writeIndex := 0;
    sampleCount := 0;
    windowSizeReached := FALSE;

    FOR i := 0 TO 99 DO
        samples[i] := 0.0;
    END_FOR;

    IF validWindow THEN
        average := 0.0;
    END_IF;

ELSIF NOT validWindow THEN
    (* 非法长度时不采样、不改变 average；保证 C2。 *)
    windowSizeReached := FALSE;

ELSE
    IF sampleCount > windowSize THEN
        sampleCount := windowSize;
    END_IF;

    acquire := cyclicExecution OR
               ((NOT cyclicExecution) AND triggerRise);

    IF acquire THEN
        samples[writeIndex] := value;

        writeIndex := writeIndex + 1;
        IF writeIndex >= 100 THEN
            writeIndex := 0;
        END_IF;

        IF sampleCount < windowSize THEN
            sampleCount := sampleCount + 1;
        END_IF;
    END_IF;

    IF sampleCount = 0 THEN
        average := 0.0;
    ELSE
        (* 先除以样本数，避免先累加原始值造成不必要的溢出。 *)
        divisor := INT_TO_LREAL(sampleCount);
        meanValue := 0.0;
        readIndex := writeIndex;

        FOR i := 1 TO sampleCount DO
            readIndex := readIndex - 1;
            IF readIndex < 0 THEN
                readIndex := 99;
            END_IF;
            meanValue := meanValue + (samples[readIndex] / divisor);
        END_FOR;

        average := meanValue;
    END_IF;

    windowSizeReached := (sampleCount = windowSize);
END_IF;

END_FUNCTION_BLOCK

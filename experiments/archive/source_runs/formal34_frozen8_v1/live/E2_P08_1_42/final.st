TYPE ST_AnalogChannel :
STRUCT
    enable : BOOL;
    hiLIM : REAL;
    loLIM : REAL;
    bipolar : BOOL;
    measuringMode : INT;
    retVal : WORD;
    outputValue : REAL;
END_STRUCT
END_TYPE

FUNCTION_BLOCK FB_P08
VAR_INPUT
    count : DINT;
END_VAR
VAR_IN_OUT
    analogValues : ARRAY[*] OF INT;
    channels : ARRAY[*] OF ST_AnalogChannel;
END_VAR
VAR
    firstScan : BOOL := TRUE;
    analogLower : DINT;
    analogUpper : DINT;
    channelLower : DINT;
    channelUpper : DINT;
    analogLength : DINT;
    channelLength : DINT;
    remaining : DINT;
    analogIndex : DINT;
    channelIndex : DINT;
    rawValue : REAL;
    normalizedValue : REAL;
END_VAR

(*
需求原文：
Write a PLC function block that processes analog inputs in batches and converts them into engineering values.

1. analogValues supplies the raw-value array. channels supplies per-channel settings and receives conversion results. count specifies how many channels to process from the beginning of the arrays. The caller must provide count from zero through the smaller of the two array lengths. Match channels by ordinal position starting at each array's own lower bound. Read analogValues without modifying it.
2. Each channel is enabled by its enable field and converted according to measuringMode. Read configuration fields without modifying them; write only retVal and outputValue.
3. For measuringMode 0, perform non-temperature linear scaling: when bipolar is FALSE, map raw values 0..27648 to loLIM..hiLIM; when TRUE, map -27648..27648 to loLIM..hiLIM.
4. For measuringMode 1, perform standard-temperature conversion: outputValue is one tenth of the raw analog value.
5. For measuringMode 2, perform climatic-temperature conversion: outputValue is one hundredth of the raw analog value.
6. If measuringMode is not 0, 1 or 2, set that channel's retVal to 16#8001 and skip its conversion.
7. If hiLIM is less than or equal to loLIM, set that channel's retVal to 16#8002 and skip its conversion.
8. A channel error affects only that channel. Continue processing subsequent channels; count is limited by the actual lengths of both arrays, with no separate fixed channel cap.

修改说明：
替换占位 RETURN，按各数组下界逐通道匹配，每次清零当前处理
通道的结果和状态，再独立检查配置并转换。无需定时器；
每次调用对应一个 20 ms 扫描。

语义冲突报告：
“每次调用按当前输入重算”与 C10“上电当拍输出为零”在首次
调用存在非零转换结果时冲突。本实现选择首次调用仅清零当前
处理通道的输出并检查错误，从第二次调用开始转换。
C1、C6、C10 若量化至所有数组元素，会与 K1 仅允许处理前 count
个通道以及 count = 0 不做任何通道冲突。本实现仅对本次处理
范围保证这些输出约束；范围之外的字段完全不修改。
firstScan 在首次调用结束后清除，包括 count = 0 的首次调用。

边界选择：
未使能通道的 retVal 和 outputValue 均为零。
非法模式优先于上下限错误；上下限检查适用于全部合法模式。
原始值超出标定区间时按公式外推，不添加未规定的钳位。
调用者必须提供合法 count；此处另作防御性范围限制，不设置
固定通道上限，也不新增接口错误码。

编译与测试状态：
当前会话无可用编译器、测试执行工具或已配置测试命令，
未运行编译及逐周期测试，不声称已验证正确。
目标编译 profile 必须验证 VAR_IN_OUT 开放数组、LOWER_BOUND、
UPPER_BOUND、DINT 数组索引和标准数值转换的支持。
*)

analogLower := LOWER_BOUND(analogValues, 1);
analogUpper := UPPER_BOUND(analogValues, 1);
channelLower := LOWER_BOUND(channels, 1);
channelUpper := UPPER_BOUND(channels, 1);

analogLength := analogUpper - analogLower + DINT#1;
channelLength := channelUpper - channelLower + DINT#1;

remaining := count;
IF remaining < DINT#0 THEN
    remaining := DINT#0;
END_IF;
IF remaining > analogLength THEN
    remaining := analogLength;
END_IF;
IF remaining > channelLength THEN
    remaining := channelLength;
END_IF;

analogIndex := analogLower;
channelIndex := channelLower;

WHILE remaining > DINT#0 DO
    channels[channelIndex].retVal := WORD#16#0000;
    channels[channelIndex].outputValue := REAL#0.0;

    IF channels[channelIndex].enable THEN
        IF (channels[channelIndex].measuringMode < INT#0)
            OR (channels[channelIndex].measuringMode > INT#2) THEN
            channels[channelIndex].retVal := WORD#16#8001;

        ELSIF channels[channelIndex].hiLIM
            <= channels[channelIndex].loLIM THEN
            channels[channelIndex].retVal := WORD#16#8002;

        ELSIF NOT firstScan THEN
            rawValue := INT_TO_REAL(analogValues[analogIndex]);

            CASE channels[channelIndex].measuringMode OF
                0:
                    IF channels[channelIndex].bipolar THEN
                        normalizedValue :=
                            (rawValue + REAL#27648.0) / REAL#55296.0;
                    ELSE
                        normalizedValue := rawValue / REAL#27648.0;
                    END_IF;

                    channels[channelIndex].outputValue :=
                        channels[channelIndex].loLIM
                        + normalizedValue
                        * (channels[channelIndex].hiLIM
                           - channels[channelIndex].loLIM);

                1:
                    channels[channelIndex].outputValue :=
                        rawValue / REAL#10.0;

                2:
                    channels[channelIndex].outputValue :=
                        rawValue / REAL#100.0;
            END_CASE;
        END_IF;
    END_IF;

    remaining := remaining - DINT#1;
    IF remaining > DINT#0 THEN
        analogIndex := analogIndex + DINT#1;
        channelIndex := channelIndex + DINT#1;
    END_IF;
END_WHILE;

firstScan := FALSE;

END_FUNCTION_BLOCK

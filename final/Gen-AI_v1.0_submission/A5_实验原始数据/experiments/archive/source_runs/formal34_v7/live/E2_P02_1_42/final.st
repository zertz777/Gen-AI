(*
需求原文：
Write a function block FB that checks for rising and falling edges in each bit of a dual-word (DWord) input value every cycle. The function block should be able to detect and report changes, rising edges, and falling edges in the input value.

中文摘要：双字（DWORD）逐位边沿检测：每周期比较本期与上期值，
输出变化标志、上升沿位、下降沿位及其个数。
扫描周期：20 ms。

完整形式化规约：
C2: G(hasChanged -> (hasRisingEdges || hasFallingEdges))
C2b: G((hasRisingEdges || hasFallingEdges) -> hasChanged)
C7: G(!hasChanged -> X(!hasRisingEdges && !hasFallingEdges))
C8: G(hasChanged == FALSE -> noOfRisingBits == 0 && noOfFallingBits == 0)
C10: G[0,1](!hasChanged && !hasRisingEdges && !hasFallingEdges && noOfRisingBits == 0 && noOfFallingBits == 0)

约束：
K1 每周期比较本周期 value 与上一周期保存的 value。
K2 risingBits 仅标记 0 到 1；fallingBits 仅标记 1 到 0。
K3 两个计数分别等于对应边沿位图中 1 的个数。
K4 首周期三个标志均为 FALSE，避免上电误报。

语义冲突报告：
C7 禁止无变化周期之后的下一周期报告任何边沿，即使输入确实变化，
与 K1、K2 及逐周期边沿检测需求冲突。
结合 C2 和首周期无变化，C7 会使之后所有周期都无法报告变化。
若 G[0,1] 包含扫描索引 0 和 1，C10 要求前两个周期均不报告变化，
与 K4 仅抑制首周期及第二周期按 K1、K2 检测真实变化冲突。
实现选择遵循 K1 至 K4：仅首周期抑制，随后逐周期检测。
不声称同时满足上述互相冲突的全部形式化条款。

修改说明：
增加上一周期值和首周期状态；每周期重置输出，计算两类边沿位图，
逐位统计数量，最后保存本周期输入。未新增或修改外部接口。

验证状态：
当前对话未提供可执行的测试环境或已配置测试命令，
因此未运行真实编译或逐周期测试；不声称已经验证正确。
*)

FUNCTION_BLOCK FB_P02
VAR_INPUT
    value : DWORD;
END_VAR
VAR_OUTPUT
    hasChanged : BOOL := FALSE;
    hasRisingEdges : BOOL := FALSE;
    risingBits : DWORD := DWORD#16#00000000;
    noOfRisingBits : USINT := USINT#0;
    hasFallingEdges : BOOL := FALSE;
    fallingBits : DWORD := DWORD#16#00000000;
    noOfFallingBits : USINT := USINT#0;
END_VAR
VAR
    lastValue : DWORD := DWORD#16#00000000;
    initialized : BOOL := FALSE;
    currentValue : DWORD := DWORD#16#00000000;
    changedBits : DWORD := DWORD#16#00000000;
    bitMask : DWORD := DWORD#16#00000001;
    bitIndex : INT := INT#0;
END_VAR

currentValue := value;

hasChanged := FALSE;
hasRisingEdges := FALSE;
risingBits := DWORD#16#00000000;
noOfRisingBits := USINT#0;
hasFallingEdges := FALSE;
fallingBits := DWORD#16#00000000;
noOfFallingBits := USINT#0;
changedBits := DWORD#16#00000000;

IF initialized THEN
    changedBits := currentValue XOR lastValue;
    risingBits := changedBits AND currentValue;
    fallingBits := changedBits AND lastValue;

    hasChanged := changedBits <> DWORD#16#00000000;
    hasRisingEdges := risingBits <> DWORD#16#00000000;
    hasFallingEdges := fallingBits <> DWORD#16#00000000;

    bitMask := DWORD#16#00000001;
    FOR bitIndex := INT#0 TO INT#31 DO
        IF (risingBits AND bitMask) <> DWORD#16#00000000 THEN
            noOfRisingBits := noOfRisingBits + USINT#1;
        END_IF;
        IF (fallingBits AND bitMask) <> DWORD#16#00000000 THEN
            noOfFallingBits := noOfFallingBits + USINT#1;
        END_IF;
        bitMask := SHL(bitMask, INT#1);
    END_FOR;
ELSE
    initialized := TRUE;
END_IF;

lastValue := currentValue;

END_FUNCTION_BLOCK

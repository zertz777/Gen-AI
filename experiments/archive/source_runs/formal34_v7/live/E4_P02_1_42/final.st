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
    currentValue : DWORD;
    changedBits : DWORD;
    risingWork : DWORD;
    fallingWork : DWORD;
    bitIndex : INT;
END_VAR

(*
需求原文：
Write a function block FB that checks for rising and falling edges in
each bit of a dual-word (DWord) input value every cycle. The function
block should be able to detect and report changes, rising edges, and
falling edges in the input value.

每次调用为一个20 ms扫描周期。

规约冲突，保留并报告为待审：
C7: G(!hasChanged -> X(!hasRisingEdges && !hasFallingEdges))
要求无变化之后的下一周期也无边沿，与K1/K2要求检测下一周期
实际发生的变化冲突。例如输入依次为0、0、1时无法同时满足。

C10: G[0,1](!hasChanged && !hasRisingEdges && !hasFallingEdges &&
           noOfRisingBits == 0 && noOfFallingBits == 0)
若[0,1]按包含两个扫描周期解释，则要求前两个周期均不报告；
这与K4仅抑制首周期、K1/K2从第二周期开始比较的要求冲突。

本实现采用候选策略：按I/O及K1至K4逐周期实现。
不声称同时满足上述冲突条款；未声明编译或逐周期验证通过。
*)

currentValue := value;

hasChanged := FALSE;
hasRisingEdges := FALSE;
hasFallingEdges := FALSE;
risingBits := DWORD#16#00000000;
fallingBits := DWORD#16#00000000;
noOfRisingBits := USINT#0;
noOfFallingBits := USINT#0;

IF initialized THEN
    (* 本周期快照与上一周期值只生成一次变化掩码。 *)
    changedBits := currentValue XOR lastValue;
    risingBits := changedBits AND currentValue;
    fallingBits := changedBits AND lastValue;

    hasChanged := changedBits <> DWORD#16#00000000;
    hasRisingEdges := risingBits <> DWORD#16#00000000;
    hasFallingEdges := fallingBits <> DWORD#16#00000000;

    risingWork := risingBits;
    fallingWork := fallingBits;

    (* DWORD共32位，两个计数的范围均为0至32。 *)
    FOR bitIndex := 0 TO 31 DO
        IF (risingWork AND DWORD#16#00000001) <> DWORD#16#00000000 THEN
            noOfRisingBits := noOfRisingBits + USINT#1;
        END_IF;
        IF (fallingWork AND DWORD#16#00000001) <> DWORD#16#00000000 THEN
            noOfFallingBits := noOfFallingBits + USINT#1;
        END_IF;

        risingWork := SHR(risingWork, 1);
        fallingWork := SHR(fallingWork, 1);
    END_FOR;
ELSE
    (* 首周期只建立基准，所有输出保持本周期清零结果。 *)
    initialized := TRUE;
END_IF;

lastValue := currentValue;

END_FUNCTION_BLOCK

FUNCTION_BLOCK FB_P02
VAR_INPUT
    value : DWORD;
END_VAR
VAR_OUTPUT
    hasChanged : BOOL;
    hasRisingEdges : BOOL;
    risingBits : DWORD;
    noOfRisingBits : USINT;
    hasFallingEdges : BOOL;
    fallingBits : DWORD;
    noOfFallingBits : USINT;
END_VAR
VAR
    (* 内部状态：上一周期保存的输入值，初态 16#00000000 *)
    lastValue : DWORD := 16#00000000;
    (* 上电首周期标志：首周期没有“上一周期”可比，禁止上报任何变化 *)
    firstScan : BOOL := TRUE;
    (* 位计数用局部量 *)
    i : INT;
    tempBits : DWORD;
    cnt : USINT;
END_VAR

(* K4 / C10: 上电后的第一个扫描周期，统一复位/清零并只记录本周期值 *)
IF firstScan THEN
    hasChanged := FALSE;
    hasRisingEdges := FALSE;
    hasFallingEdges := FALSE;
    risingBits := 16#00000000;
    fallingBits := 16#00000000;
    noOfRisingBits := 0;
    noOfFallingBits := 0;
    lastValue := value;
    firstScan := FALSE;
ELSE
    (* K1: 每个扫描周期只做一次比较：本周期 value 与上一周期保存的 lastValue *)
    hasChanged := (value <> lastValue);

    (* K2: 上升沿位流只在本周期为 1 且上周期为 0 的位上置 1 *)
    risingBits := value AND (NOT lastValue);
    (* K2: 下降沿位流只在本周期为 0 且上周期为 1 的位上置 1 *)
    fallingBits := (NOT value) AND lastValue;

    (* C2 / C2b: 边沿标志与 hasChanged 必须同源一致 *)
    IF risingBits <> 16#00000000 THEN
        hasRisingEdges := TRUE;
    ELSE
        hasRisingEdges := FALSE;
    END_IF;

    IF fallingBits <> 16#00000000 THEN
        hasFallingEdges := TRUE;
    ELSE
        hasFallingEdges := FALSE;
    END_IF;

    (* K3 / C8: 计数必须等于对应位流中 1 的个数；无变化时自然为 0 *)
    cnt := 0;
    tempBits := risingBits;
    FOR i := 0 TO 31 DO
        IF (tempBits AND 16#00000001) <> 16#00000000 THEN
            cnt := cnt + 1;
        END_IF;
        tempBits := SHR(tempBits, 1);
    END_FOR;
    noOfRisingBits := cnt;

    cnt := 0;
    tempBits := fallingBits;
    FOR i := 0 TO 31 DO
        IF (tempBits AND 16#00000001) <> 16#00000000 THEN
            cnt := cnt + 1;
        END_IF;
        tempBits := SHR(tempBits, 1);
    END_FOR;
    noOfFallingBits := cnt;

    (* 保存本周期值，供下一周期比较（每周期仅一次状态更新） *)
    lastValue := value;
END_IF;

END_FUNCTION_BLOCK

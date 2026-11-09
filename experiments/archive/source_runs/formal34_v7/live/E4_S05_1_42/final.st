FUNCTION_BLOCK FB_S05
VAR_INPUT
    FlowPulse : BOOL;
    ShiftReset : BOOL;
    CycleTime : TIME;
END_VAR
VAR_OUTPUT
    TotalVolume : LREAL := LREAL#0.0;
    ShiftVolume : LREAL := LREAL#0.0;
    PulseCount : UDINT := UDINT#0;
    OverflowFlag : BOOL := FALSE;
    Status : WORD := WORD#16#0000;
END_VAR
VAR
    FlowPulseLast : BOOL := FALSE;
    ShiftResetLast : BOOL := FALSE;
    FlowRise : BOOL := FALSE;
    ResetRise : BOOL := FALSE;
END_VAR

(*
    待审事项（未声称已通过编译或逐周期功能验证）：

    1. FlowPulse 每扫描仅提供一个 BOOL 样本。CycleTime 即使为
       T#20ms，也不能揭示扫描间发生的多个上升沿。
       K4 所需的多脉冲检测及对应 16#8501 无法由本接口可靠实现；
       不以电平持续时间或 CycleTime 偏差伪造脉冲过快判断。

    2. 总量封顶后，原文要求当班量继续每脉冲增加 0.5 L，
       与 C6 的 ShiftVolume <= TotalVolume 存在冲突。
       以下保留原文的独立当班累计，不暗中截断当班量；
       因此不能宣称满足 C6。

    3. 若 C10 要求执行首扫描后仍为零，则与首扫描输入为 TRUE
       时按 K1 计上升沿冲突。以下按给定初态初始化，
       首扫描仍执行边沿计数，不屏蔽首扫描输入。

    4. PulseCount 达 UDINT 上限后无法继续表达“加 1”。
       以下采用饱和防回绕；该数值边界行为仍须需求确认。

    同扫描出现计量与班次复位上升沿时：
    先计量，再清当班量和当班计数；总量保留本扫描计量。
*)

FlowRise := FlowPulse AND NOT FlowPulseLast;
ResetRise := ShiftReset AND NOT ShiftResetLast;

IF FlowRise THEN
    IF PulseCount < UDINT#4294967295 THEN
        PulseCount := PulseCount + UDINT#1;
    END_IF;

    ShiftVolume := ShiftVolume + LREAL#0.5;

    IF NOT OverflowFlag THEN
        IF TotalVolume < LREAL#999999.5 THEN
            TotalVolume := TotalVolume + LREAL#0.5;
        ELSE
            TotalVolume := LREAL#1000000.0;
            OverflowFlag := TRUE;
        END_IF;
    END_IF;
END_IF;

IF ResetRise THEN
    ShiftVolume := LREAL#0.0;
    PulseCount := UDINT#0;
END_IF;

IF TotalVolume >= LREAL#1000000.0 THEN
    OverflowFlag := TRUE;
END_IF;

(* 溢出永久保持；班次复位不清除总量、溢出标志或溢出状态。 *)
IF OverflowFlag THEN
    Status := WORD#16#8502;
ELSE
    (* 无可观测的多脉冲证据；此状态不保证不存在漏采脉冲。 *)
    Status := WORD#16#0000;
END_IF;

FlowPulseLast := FlowPulse;
ShiftResetLast := ShiftReset;

END_FUNCTION_BLOCK

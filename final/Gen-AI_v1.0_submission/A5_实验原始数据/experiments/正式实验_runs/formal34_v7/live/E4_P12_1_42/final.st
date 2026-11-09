FUNCTION_BLOCK FB_P12
VAR_INPUT
    THICKNESS_FAULT : BOOL;
    THICKNESS_SIGNAL_VALID : BOOL;
    CUTTING_RUN : BOOL;
    FaultTimestamp : DINT;
    CycleTime : TIME;
END_VAR
VAR_OUTPUT
    THICKNESS_ALARM : BOOL;
    Slab_Fault_Counter : UINT;
    Slab_Runtime_Accumulator : LTIME;
    Slab_Fault_History : ARRAY[0..4] OF DINT;
END_VAR
VAR
    Initialized : BOOL := FALSE;
    PreviousValidFault : BOOL := FALSE;
    FaultRising : BOOL := FALSE;
    HoldRemaining : TIME := T#0ms;
    InternalAlarm : BOOL := FALSE;
    InternalCounter : UINT := UINT#0;
    InternalRuntime : LTIME := LTIME#0ns;
    InternalHistory : ARRAY[0..4] OF DINT;
    RuntimeIncrement : LTIME := LTIME#0ns;
    Index : INT;
END_VAR
VAR CONSTANT
    ScanInterval : TIME := T#20ms;
    MinimumHold : TIME := T#500ms;
    MaximumCounter : UINT := UINT#65535;
    MaximumRuntime : LTIME := LTIME#9223372036854775807ns;
END_VAR

(*
    待审语义冲突，不宣称规约已全部满足：
    1. 上电不报警 / C10 与上电输入已经有效且故障为 TRUE 时
       “立即报警”冲突。本实现首调用只初始化，后续调用执行监测。
       C10 的 G[0,1] 若包含两个执行后状态，则本实现不额外抑制第二扫描。
    2. 信号无效立即清报警优先于最少保持 500 ms。
       若无效期间原始 THICKNESS_FAULT 仍为 TRUE，C6 的无条件保持
       与 C2 的禁止报警冲突；本实现按有效信号限定故障保持。
    3. C6 本身不能推出最少保持 500 ms；本实现另设保持状态。
    4. C8 若禁止信号恢复后下一扫描立即报警，则与立即报警要求冲突；
       本实现信号无效时当扫描清除，恢复有效后重新检测故障上升沿。
    5. UINT 无法无限计数，LTIME 无法无限累计。本实现到上限饱和，
       上限之后严格“加 1 / 按 CycleTime 累加”不可由指定类型表达。
    6. VAR_OUTPUT 无法跨所有 IEC 平台声明为调用者不可写。
       私有历史为权威数据，每扫描覆盖输出镜像；调用者必须遵守只读约定。

    每调用为 20 ms，报警保持使用固定扫描间隔。
    正常运行累计使用正值 CycleTime；非正值不累计。
    LTIME、TIME_TO_LTIME 和长时间字面量需目标编译 profile 验证。
    源码未声称经过编译或逐周期功能验证。
*)

IF NOT Initialized THEN
    InternalAlarm := FALSE;
    InternalCounter := UINT#0;
    InternalRuntime := LTIME#0ns;
    HoldRemaining := T#0ms;
    PreviousValidFault := FALSE;
    FaultRising := FALSE;
    RuntimeIncrement := LTIME#0ns;

    FOR Index := 0 TO 4 DO
        InternalHistory[Index] := DINT#0;
    END_FOR;

    Initialized := TRUE;
ELSE
    FaultRising := FALSE;

    IF NOT THICKNESS_SIGNAL_VALID THEN
        InternalAlarm := FALSE;
        HoldRemaining := T#0ms;
        PreviousValidFault := FALSE;
    ELSE
        (* 已有保持状态对应前次扫描至本次扫描的经过时间。 *)
        IF HoldRemaining > ScanInterval THEN
            HoldRemaining := HoldRemaining - ScanInterval;
        ELSE
            HoldRemaining := T#0ms;
        END_IF;

        FaultRising := THICKNESS_FAULT AND NOT PreviousValidFault;

        IF FaultRising THEN
            IF InternalCounter < MaximumCounter THEN
                InternalCounter := InternalCounter + UINT#1;
            END_IF;

            FOR Index := 4 TO 1 BY -1 DO
                InternalHistory[Index] := InternalHistory[Index - 1];
            END_FOR;
            InternalHistory[0] := FaultTimestamp;

            (* 每个新故障均从当前扫描重新保证至少 500 ms。 *)
            HoldRemaining := MinimumHold;
        END_IF;

        InternalAlarm := THICKNESS_FAULT OR (HoldRemaining > T#0ms);
        PreviousValidFault := THICKNESS_FAULT;

        (* 报警保持期间若实际故障已消失，仍可累计正常运行时间。 *)
        IF CUTTING_RUN AND NOT THICKNESS_FAULT AND (CycleTime > T#0ms) THEN
            RuntimeIncrement := TIME_TO_LTIME(CycleTime);

            IF RuntimeIncrement > LTIME#0ns THEN
                IF InternalRuntime <= MaximumRuntime - RuntimeIncrement THEN
                    InternalRuntime := InternalRuntime + RuntimeIncrement;
                ELSE
                    InternalRuntime := MaximumRuntime;
                END_IF;
            END_IF;
        END_IF;
    END_IF;
END_IF;

(* 仅输出观测数据，不生成或修改切割设备运行许可。 *)
THICKNESS_ALARM := InternalAlarm;
Slab_Fault_Counter := InternalCounter;
Slab_Runtime_Accumulator := InternalRuntime;

FOR Index := 0 TO 4 DO
    Slab_Fault_History[Index] := InternalHistory[Index];
END_FOR;

END_FUNCTION_BLOCK

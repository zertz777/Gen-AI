FUNCTION_BLOCK FB_S14
VAR_INPUT
    Pressure : REAL;
    PumpEnable : BOOL;
    ResetBtn : BOOL;
END_VAR
VAR_OUTPUT
    LowPump : BOOL := FALSE;
    HighPump : BOOL := FALSE;
    ReliefValve : BOOL := FALSE;
    AlarmLamp : BOOL := FALSE;
    Status : WORD := WORD#16#0000;
END_VAR
VAR
    ResetBtnLast : BOOL := FALSE;
    HighPumpLatched : BOOL := FALSE;
    ResetRise : BOOL := FALSE;
    SensorFault : BOOL := FALSE;
    FaultLatched : BOOL := FALSE;
END_VAR

(*
    数据冲突报告（待审；尚未经过编译和逐周期验证）：
    1. C10 对上电输出的无条件要求与首周期过压保护 C1/K1、
       以及首周期低压加载 C2/K2 存在冲突。
       本实现保留声明初态，但扫描执行时优先立即保护，
       不以启动屏蔽延迟保护，也不保证 C10 的无条件时序要求。
    2. K2 未排除报警；故障时停泵与其无条件加载要求冲突。
       本实现以故障停泵优先。
    3. C7 未排除禁止加载、报警或卸荷保持状态，与这些状态下
       停泵及 C4 互斥要求可能冲突。
       本实现仅在允许正常加载时保持高压泵滞回；
       禁止加载、故障或卸荷均清除高压泵锁存。
    4. LTL 的 X 与文字“同一周期”时间标记不一致。
       本实现按当前调用输入更新当前调用输出，不额外延迟。
*)

(* 每次调用为一个 20 ms 扫描；任何状态下均更新复位边沿。 *)
ResetRise := ResetBtn AND NOT ResetBtnLast;
ResetBtnLast := ResetBtn;

SensorFault := (Pressure < REAL#0.5) OR (Pressure > REAL#250.0);

(* 当前传感器故障优先于复位，故障持续时不能复位。 *)
IF SensorFault THEN
    FaultLatched := TRUE;
ELSIF FaultLatched AND ResetRise THEN
    FaultLatched := FALSE;
END_IF;

AlarmLamp := FaultLatched;

IF SensorFault THEN
    Status := WORD#16#8D01;
ELSIF FaultLatched THEN
    Status := WORD#16#8D02;
ELSE
    Status := WORD#16#0000;
END_IF;

(* 卸荷独立于加载许可；150 和 160 的边界均保持原状态。
   包括 Pressure > 250 的故障情况在内，过压立即卸荷。 *)
IF Pressure > REAL#160.0 THEN
    ReliefValve := TRUE;
ELSIF Pressure < REAL#150.0 THEN
    ReliefValve := FALSE;
END_IF;

(* 先置安全输出，再在许可条件下加载，保证卸荷与泵互斥。 *)
LowPump := FALSE;
HighPump := FALSE;

IF AlarmLamp OR ReliefValve OR NOT PumpEnable THEN
    HighPumpLatched := FALSE;
ELSE
    LowPump := Pressure < REAL#120.0;

    IF Pressure >= REAL#140.0 THEN
        HighPumpLatched := TRUE;
    ELSIF Pressure < REAL#100.0 THEN
        HighPumpLatched := FALSE;
    END_IF;

    HighPump := HighPumpLatched;
END_IF;

END_FUNCTION_BLOCK

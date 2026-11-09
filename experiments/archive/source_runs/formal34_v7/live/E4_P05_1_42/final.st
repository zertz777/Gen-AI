FUNCTION_BLOCK FB_P05
VAR_INPUT
    Gap_Exceeded : BOOL;
    Weld_E_Stop_NC : BOOL;
    DebounceTime : TIME;
END_VAR
VAR_OUTPUT
    Operator_Alert : BOOL := FALSE;
    Weld_Soft_Start_Active : BOOL := TRUE;
END_VAR
VAR
    InitializationElapsed : TIME := T#0ms;
    DebounceElapsed : TIME := T#0ms;
END_VAR

(*
需求原文：
Control a weld-gap alarm with power-up monitoring inhibition,
input debouncing during normal monitoring and emergency-stop priority.

1. Gap_Exceeded indicates that the scanner has detected a weld gap
   exceeding the permitted 1.5 mm value.
2. Begin with a 5-second initialization inhibition period after power-up.
   During this period, Operator_Alert is FALSE,
   Weld_Soft_Start_Active is TRUE, and gap-signal debounce time
   does not accumulate.
3. Resume gap monitoring after initialization. Allow the alarm only after
   Gap_Exceeded has remained TRUE for DebounceTime. When the signal
   becomes FALSE, switch off the alarm and clear debounce timing.
4. When Weld_E_Stop_NC is FALSE, the emergency stop takes priority over
   initialization and normal monitoring. Operator_Alert must immediately
   become FALSE and any incomplete debounce timing must be cleared.
5. Weld_Soft_Start_Active indicates only the power-up inhibition period;
   it does not represent a continuous speed ramp.

形式化规约：
C1: G(!Weld_E_Stop_NC -> !Operator_Alert)
C2: G(Operator_Alert -> Weld_E_Stop_NC)
C6: G(Operator_Alert -> (Operator_Alert W !Gap_Exceeded))
C9: G(Operator_Alert -> G[0,25](Operator_Alert))
C10: G[0,1](!Operator_Alert && Weld_Soft_Start_Active)

待审语义冲突：
- C6 要求间隙未恢复时保持报警，与 K4/C1 要求急停立即撤销
  已有报警冲突。
- C9 要求报警至少保持 500 ms，与 K3 要求间隙恢复立即撤销、
  K4/C1 要求急停立即撤销冲突。
本实现采用题面明示的急停优先级及 K1 至 K4，不增加最小脉宽
保持逻辑；不能声称同时满足上述冲突规约。
源码未经过真实编译器及逐周期测试验证。

扫描约定：
每次调用代表一个 20 ms 区间，前 250 次调用处于初始化抑制期，
第 251 次调用开始监视。有效间隙扫描每次累计 20 ms。
初始化计时不因急停暂停或重新开始。
DebounceTime 必须为正；非正值不报警并清除去抖计时。
*)

Weld_Soft_Start_Active := InitializationElapsed < T#5s;

IF Weld_Soft_Start_Active THEN
    InitializationElapsed := InitializationElapsed + T#20ms;
END_IF;

(* 急停优先；抑制状态仍仅反映上电初始化时间。 *)
IF NOT Weld_E_Stop_NC THEN
    Operator_Alert := FALSE;
    DebounceElapsed := T#0ms;

ELSIF Weld_Soft_Start_Active THEN
    Operator_Alert := FALSE;
    DebounceElapsed := T#0ms;

ELSIF NOT Gap_Exceeded THEN
    Operator_Alert := FALSE;
    DebounceElapsed := T#0ms;

ELSIF DebounceTime <= T#0ms THEN
    Operator_Alert := FALSE;
    DebounceElapsed := T#0ms;

ELSE
    (* 饱和累计，避免在 TIME 上限附近加法溢出。 *)
    IF DebounceElapsed < DebounceTime THEN
        IF (DebounceTime - DebounceElapsed) <= T#20ms THEN
            DebounceElapsed := DebounceTime;
        ELSE
            DebounceElapsed := DebounceElapsed + T#20ms;
        END_IF;
    END_IF;

    Operator_Alert := DebounceElapsed >= DebounceTime;
END_IF;

END_FUNCTION_BLOCK

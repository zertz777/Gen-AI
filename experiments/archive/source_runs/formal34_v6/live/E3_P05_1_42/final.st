FUNCTION_BLOCK FB_P05
VAR_INPUT
    Gap_Exceeded : BOOL;
    Weld_E_Stop_NC : BOOL;
    DebounceTime : TIME;
END_VAR
VAR_OUTPUT
    Operator_Alert : BOOL;
    Weld_Soft_Start_Active : BOOL;
END_VAR
VAR
    InitTimer : TON;
    DebounceTimer : TON;
END_VAR

(*
    语义冲突保留报告：
    1) K3 要求 Gap_Exceeded 变 FALSE 时立即复位 Operator_Alert 并清去抖计时；
       C9 要求 Operator_Alert 一旦置位至少保持 500 ms（25 个扫描周期）。
       两者在报警置位后 Gap_Exceeded 于 500 ms 内变 FALSE 时冲突。
       本实现按任务卡 K3 执行：立即复位，不额外增加保持计时接口。
    2) C1 允许急停当周期清除 Operator_Alert；
       无条件 C6 要求 Operator_Alert 保持到 Gap_Exceeded 为 FALSE。
       若急停发生在 Gap_Exceeded 仍为 TRUE 时，C1 与 C6 冲突。
       本实现按任务卡 K4 执行：急停优先。
    编译通过不代表功能正确；功能正确性需由逐周期测试判定。
*)

(* 上电初始化抑制：固定 5 秒，仅上电后一次 *)
InitTimer(IN := TRUE, PT := T#5s);
Weld_Soft_Start_Active := NOT InitTimer.Q;

(* 间隙去抖计时：仅正常监视、无急停、间隙超限时累计 *)
DebounceTimer(
    IN := Weld_E_Stop_NC AND NOT Weld_Soft_Start_Active AND Gap_Exceeded,
    PT := DebounceTime
);

(* 报警优先级：急停 > 初始化抑制 > 正常监视去抖 *)
IF NOT Weld_E_Stop_NC THEN
    (* K4：急停有效，立即清报警，去抖通过 TON 的 IN=FALSE 清零 *)
    Operator_Alert := FALSE;
ELSIF Weld_Soft_Start_Active THEN
    (* K1：初始化抑制期内不报警，去抖不累计 *)
    Operator_Alert := FALSE;
ELSE
    (* K2/K3：初始化结束后正常监视 *)
    IF NOT Gap_Exceeded THEN
        (* K3：间隙恢复 FALSE，立即复位报警并清去抖计时 *)
        Operator_Alert := FALSE;
    ELSIF DebounceTimer.Q THEN
        (* K2：Gap_Exceeded 连续为 TRUE 达 DebounceTime 后置位报警 *)
        Operator_Alert := TRUE;
    END_IF;
END_IF;

END_FUNCTION_BLOCK

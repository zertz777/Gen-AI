FUNCTION_BLOCK FB_S12
VAR_INPUT
    EStop_NC : BOOL;
    ResetBtn : BOOL;
    StartBtn : BOOL;
    DoorClosed : BOOL;
END_VAR
VAR_OUTPUT
    MachineRun : BOOL := FALSE;
    ShiftCount : UINT := UINT#0;
    AlarmLamp : BOOL := FALSE;
    Status : WORD := WORD#16#0000;
END_VAR
VAR
    ResetConfirmed : BOOL := FALSE;
    ResetBtnLast : BOOL := FALSE;
    StartBtnLast : BOOL := FALSE;
    ResetRise : BOOL := FALSE;
    StartRise : BOOL := FALSE;
    RunScans : UINT := UINT#0;
END_VAR

(*
    待审语义冲突：
    C10 要求上电 [0,1] 周期 AlarmLamp = FALSE；
    需求第 1 条要求 EStop_NC = FALSE 时立即 AlarmLamp = TRUE。
    若上电时急停有效，两项不能同时满足。
    本实现保留此冲突说明，并执行急停安全优先级，
    不以初始化屏蔽急停报警。未声称已通过编译或逐周期验证。

    AlarmLamp 仅按明确要求指示急停；其他状态由 Status 指示。
    运行时间按每扫描 20 ms 累积，停机时保留不足一分钟的余量。
    ShiftCount 到达 UINT 上限后饱和，避免回绕清零。
*)

(* 所有扫描均更新按钮历史，急停期间的按键边沿不延后执行。 *)
ResetRise := ResetBtn AND NOT ResetBtnLast;
StartRise := StartBtn AND NOT StartBtnLast;
ResetBtnLast := ResetBtn;
StartBtnLast := StartBtn;

IF NOT EStop_NC THEN
    (* 急停优先于门、复位及启动。 *)
    MachineRun := FALSE;
    ResetConfirmed := FALSE;
    AlarmLamp := TRUE;
    Status := WORD#16#8B01;

ELSIF NOT DoorClosed THEN
    (* 开门立即停机，并撤销已经取得的复位许可。 *)
    MachineRun := FALSE;
    ResetConfirmed := FALSE;
    AlarmLamp := FALSE;
    Status := WORD#16#8B03;

ELSE
    AlarmLamp := FALSE;

    IF NOT ResetConfirmed THEN
        MachineRun := FALSE;
        Status := WORD#16#8B02;

        IF ResetRise THEN
            ResetConfirmed := TRUE;
            Status := WORD#16#0000;
        END_IF;
        (* 同一扫描的启动边沿不接受，必须在复位之后再出现。 *)

    ELSE
        Status := WORD#16#0000;

        IF StartRise THEN
            MachineRun := TRUE;
        END_IF;
    END_IF;
END_IF;

(* 仅实际运行扫描参与统计；急停和其他停机均冻结计数及余量。 *)
IF MachineRun THEN
    IF RunScans >= UINT#2999 THEN
        RunScans := UINT#0;

        IF ShiftCount < UINT#65535 THEN
            ShiftCount := ShiftCount + UINT#1;
        END_IF;
    ELSE
        RunScans := RunScans + UINT#1;
    END_IF;
END_IF;

END_FUNCTION_BLOCK

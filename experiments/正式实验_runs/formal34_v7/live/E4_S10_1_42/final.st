FUNCTION_BLOCK FB_S10
VAR_INPUT
    VFDFaultCode : WORD;
    VFDRun : BOOL;
    ResetBtn : BOOL;
END_VAR
VAR_OUTPUT
    AlarmLamp : BOOL := FALSE;
    TripOutput : BOOL := FALSE;
    Status : WORD := WORD#16#0000;
END_VAR
VAR
    ResetBtnLast : BOOL := FALSE;
    ResetRise : BOOL := FALSE;
    TripLatched : BOOL := FALSE;
    LatchedFaultCode : WORD := WORD#16#0000;
    HeavyFault : BOOL := FALSE;
END_VAR

(*
    扫描周期：20 ms。

    需求冲突，待审；本实现不声称满足全部原文及形式化规约：
    1. 原文第1条轻故障不跳闸，与第4条运行中任何非零故障跳闸冲突。
       本实现按安全优先：运行中轻故障也立即跳闸，且不写运行反馈。
    2. C1要求运行中故障当周期跳闸，C2却要求跳闸时VFDRun为FALSE。
       VFDRun为只读外部反馈，无法保证C2；也无法保证C7的下一周期反馈。
    3. C10要求上电初始扫描保持全部输出无故障，与当周期故障响应冲突。
       声明初值保持指定初态；首次调用即处理输入，不屏蔽故障。
    4. C6要求跳闸保持到复位，K3要求上升沿且当前无故障。
       本实现将所有跳闸保持至有效复位；仅0002、0003锁存故障码。
       Status优先显示锁存的重故障码，否则显示当前输入故障码。

    未经过编译或逐周期功能测试验证。
*)

ResetRise := ResetBtn AND NOT ResetBtnLast;
ResetBtnLast := ResetBtn;

HeavyFault :=
    (VFDFaultCode = WORD#16#0002) OR
    (VFDFaultCode = WORD#16#0003);

(* 有效复位仅允许在当前无故障时执行。 *)
IF ResetRise AND (VFDFaultCode = WORD#16#0000) THEN
    TripLatched := FALSE;
    LatchedFaultCode := WORD#16#0000;
END_IF;

(* 重故障不依赖运行反馈，同周期跳闸并锁存故障码。 *)
IF HeavyFault THEN
    TripLatched := TRUE;
    LatchedFaultCode := VFDFaultCode;
END_IF;

(* 按原文第4条的安全优先策略处理运行中任何非零故障。 *)
IF VFDRun AND (VFDFaultCode <> WORD#16#0000) THEN
    TripLatched := TRUE;
END_IF;

TripOutput := TripLatched;

IF LatchedFaultCode <> WORD#16#0000 THEN
    Status := LatchedFaultCode;
ELSE
    Status := VFDFaultCode;
END_IF;

AlarmLamp :=
    TripLatched OR
    (VFDFaultCode <> WORD#16#0000) OR
    (LatchedFaultCode <> WORD#16#0000);

END_FUNCTION_BLOCK

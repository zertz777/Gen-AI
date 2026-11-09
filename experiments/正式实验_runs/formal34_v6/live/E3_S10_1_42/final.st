FUNCTION_BLOCK FB_S10
VAR_INPUT
    VFDFaultCode : WORD;
    VFDRun : BOOL;
    ResetBtn : BOOL;
END_VAR
VAR_OUTPUT
    AlarmLamp : BOOL;
    TripOutput : BOOL;
    Status : WORD;
END_VAR
VAR
    ResetBtnLast : BOOL := FALSE;
    LatchedFaultCode : WORD := 16#0000;
    TripLatched : BOOL := FALSE;
    ResetEdge : BOOL;
    NoFault : BOOL;
    IsHeavyFault : BOOL;
END_VAR

(* Conflict/未验证报告:
   1) 需求4“运行中任何非零故障码跳闸”与需求1/C7“16#0001轻故障不跳闸”冲突。
      本实现按需求1/C1/C7将 16#0001 作为轻故障例外处理。
   2) C2: G(TripOutput -> !VFDRun) 涉及只读输入 VFDRun，FB 无法强制其状态；
      本实现仅置 TripOutput，C2 必须由外部联锁保证，未在 FB 内验证。
   3) C10 上电首周期不跳闸/不报警与 K1 重故障同周期跳闸在“首周期已有重故障”时冲突；
      本实现不增加首周期屏蔽，按故障优先，初值由声明初态保证。
*)

    (*  ResetBtn 上升沿检测  *)
    ResetEdge := ResetBtn AND NOT ResetBtnLast;
    ResetBtnLast := ResetBtn;

    (*  故障分级边界：16#0000 无故障，16#0001 轻故障，其余非零按重故障处理  *)
    NoFault := (VFDFaultCode = 16#0000);
    IsHeavyFault := (VFDFaultCode <> 16#0000) AND (VFDFaultCode <> 16#0001);

    (*  重故障优先，立即锁存跳闸并记录故障码  *)
    IF IsHeavyFault THEN
        TripLatched := TRUE;
        LatchedFaultCode := VFDFaultCode;
    END_IF;

    (*  仅 ResetBtn 上升沿且当前无故障时解除跳闸锁存  *)
    IF ResetEdge AND NoFault THEN
        TripLatched := FALSE;
        LatchedFaultCode := 16#0000;
    END_IF;

    (*  输出映射  *)
    TripOutput := TripLatched;
    AlarmLamp := (VFDFaultCode <> 16#0000) OR TripLatched;

    (*  Status 优先显示锁存重故障码；无锁存时显示当前故障码  *)
    IF LatchedFaultCode <> 16#0000 THEN
        Status := LatchedFaultCode;
    ELSE
        Status := VFDFaultCode;
    END_IF;

END_FUNCTION_BLOCK

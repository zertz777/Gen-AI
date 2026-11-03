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
    (* 内部状态：跳闸锁存与首个重故障码锁存 *)
    LatchedTrip : BOOL := FALSE;
    LatchedCode : WORD := 16#0000;
    (* 复位按钮上升沿检测 *)
    ResetBtnLast : BOOL := FALSE;
    ResetRising : BOOL := FALSE;
    (* 故障分级与跳闸触发中间量 *)
    IsHeavyFault : BOOL := FALSE;
    TripCondition : BOOL := FALSE;
END_VAR
(*
  规约映射与语义冲突报告（仅说明，不新增/修改接口）：
  - 冲突：需求1（16#0001 轻故障不跳闸）与需求4（运行中任何非零故障码均跳闸）冲突。
    规约 C1 已显式排除 16#0001，故采用：运行中 (VFDFaultCode <> 0 AND <> 16#0001) 才跳闸。
  - 冲突/假设：C2 G(TripOutput -> !VFDRun) 不能由本 FB 强制，因 VFDRun 为输入；
    跳闸后需由外部变频器反馈停机。FB 仅按其输入/输出逻辑实现，不声称已满足 C2。
  - C10 上电初态：由 VAR 初值保证（LatchedTrip=FALSE、LatchedCode=0）；
    首周期若输入即为故障仍按 K1/K2/K4 立即响应。
*)

(* 复位上升沿检测 *)
ResetRising := ResetBtn AND NOT ResetBtnLast;

(* 故障分级：16#0001 轻故障；16#0002/16#0003 重故障 *)
IsHeavyFault := (VFDFaultCode = 16#0002) OR (VFDFaultCode = 16#0003);

(* 跳闸触发条件：
   1) 重故障（2 或 3）—— 立即跳闸（需求2）
   2) 运行中且故障码非零且非轻故障（需求4 / C1） *)
TripCondition := IsHeavyFault OR
                (VFDRun AND (VFDFaultCode <> 16#0000) AND (VFDFaultCode <> 16#0001));

(* 重故障锁存：锁存首个重故障码，不随故障码消失自动复位（需求2/3，K2） *)
IF TripCondition AND NOT LatchedTrip THEN
    LatchedTrip := TRUE;
    LatchedCode := 16#0001;
END_IF;

(* 复位：仅 ResetBtn 上升沿且当前无故障时解除锁存（需求3，K3） *)
IF ResetRising AND (VFDFaultCode = 16#0000) THEN
    LatchedTrip := FALSE;
    LatchedCode := 16#0000;
END_IF;

(* 输出 *)
TripOutput := LatchedTrip;
AlarmLamp := (VFDFaultCode <> 16#0000) OR LatchedTrip;

(* Status = 当前生效故障码：锁存期间显示锁存码，否则显示当前码（需求5） *)
IF LatchedTrip THEN
    Status := LatchedCode;
ELSE
    Status := VFDFaultCode;
END_IF;

(* 更新边沿历史 *)
ResetBtnLast := ResetBtn;

END_FUNCTION_BLOCK

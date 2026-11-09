FUNCTION_BLOCK FB_S04
VAR_INPUT
    RawWeight : INT;
    ZeroBtn : BOOL;
    CalibWeight : REAL;
END_VAR
VAR_OUTPUT
    CompensatedWeight : REAL := 0.0;
    ZeroOffset : INT := 0;
    DriftAlarm : BOOL := FALSE;
    Status : WORD := 16#0000;
END_VAR
VAR
    ZeroBtnLast : BOOL := FALSE;
    delta : DINT;
    driftOut : BOOL;
    driftBack : BOOL;
END_VAR

(* ============================================================
 * 冲突报告（保留，不自行修改接口或类型）：
 *
 * 冲突1：C10 要求上电首周期 CompensatedWeight == 0.0，
 *        而 C4 要求每周期 CompensatedWeight == (RawWeight - ZeroOffset) * 0.01。
 *        当首个扫描周期 RawWeight != 0 时，两者在首周期结束时的值矛盾。
 *        本实现按 C4 每周期计算补偿重量；VAR_OUTPUT 初值仅保证调用前为 0.0。
 *
 * 冲突2：Status = 16#8402 要求检测 RawWeight 超出 -32768..32767 的可用段，
 *        但 RawWeight 的外部接口类型为 INT，其合法范围恰好就是 -32768..32767，
 *        因此该超量程条件在类型层面不可达。本实现保留检测分支，但该分支不会执行。
 *        不新增接口、不修改 RawWeight 类型。
 * ============================================================ *)

(* 边沿检测：ZeroBtn 上升沿更新零点并清漂移报警 *)
IF ZeroBtn AND NOT ZeroBtnLast THEN
    ZeroOffset := RawWeight;
    DriftAlarm := FALSE;
END_IF;
ZeroBtnLast := ZeroBtn;

(* 补偿重量：每周期按当前 RawWeight 和 ZeroOffset 计算，不使用上一周期结果 *)
CompensatedWeight := (INT_TO_REAL(RawWeight) - INT_TO_REAL(ZeroOffset)) * 0.01;

(* 计算偏差，使用 DINT 避免 INT 减法溢出 *)
delta := INT_TO_DINT(RawWeight) - INT_TO_DINT(ZeroOffset);

(* 滞回判据：|delta| >= 200 置位；|delta| <= 150 复位；中间保持 *)
driftOut := (delta >= 200) OR (delta <= -200);
driftBack := (delta <= 150) AND (delta >= -150);

IF driftOut THEN
    DriftAlarm := TRUE;
ELSIF driftBack THEN
    DriftAlarm := FALSE;
END_IF;

(* 状态码：超量程优先，其次漂移，最后正常。
   注意：RawWeight 为 INT，其范围恰为 -32768..32767，
   因此 16#8402 分支不可达，仅保留结构以符合规约声明。 *)
IF RawWeight < -32768 OR RawWeight > 32767 THEN
    Status := 16#8402;  (* 采样值超量程（类型层面不可达） *)
ELSIF DriftAlarm THEN
    Status := 16#8401;  (* 零点漂移 *)
ELSE
    Status := 16#0000;  (* 正常 *)
END_IF;

END_FUNCTION_BLOCK

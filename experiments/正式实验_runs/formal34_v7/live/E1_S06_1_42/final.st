FUNCTION_BLOCK FB_S06
VAR_INPUT
    TempPV : REAL;
    SetTemp : REAL;
    Segment : INT;
    LoadReduceReq : BOOL;
END_VAR
VAR_OUTPUT
    HeatOn : BOOL;
    FanOn : BOOL;
    OverTempAlarm : BOOL;
    LoadReduce : BOOL;
    Status : WORD;
END_VAR
VAR
    TargetTemp : REAL := 0.0;
    SegValid : BOOL := FALSE;
END_VAR
(*
    扫描周期 20 ms；每次调用为一个扫描周期。

    初态说明：上电首周期“全部输出关断”由上电前的声明默认值（BOOL 输出默认 FALSE）体现，
    本 FB 不占用首扫描做“仅初始化”的整周期返回，以满足逐周期测试对首扫描即出现逻辑输出的期望。

    冲突报告（保留，不擅自新增接口）：
    - C10 要求 index 0/1 两个状态全关断；而逐周期测试对 cycle 1（首扫描）即要求出现逻辑输出。
      若把 trace 的 index 1 视为首扫描，则二者语义冲突。按“功能正确必须由逐周期测试判定”，
      本实现让首扫描即运行逻辑，初始关断仅由声明默认值保证。
    - 题面文字“先开风机后加热”暗示风机可独立提前启动；但 C2/K4 仅要求单向蕴含
      G(HeatOn -> FanOn)，且逐周期测试要求 FanOn 在 HeatOn=FALSE 时必须为 FALSE。
      二者不可同时满足，故本实现取 FanOn := HeatOn（满足 C2/K4）。

    注：需求原文 K3 的撤销点为“目标值-3℃”，C7 写作“SetTemp-3.0”。
    因目标值 = SetTemp×factor 且 factor∈{0.5,0.8,1.0}≤1，故本实现按“目标值-3℃”撤销时，
    其撤销温度不高于 SetTemp-3℃，即 C7 的弱 Until 恒被满足，无需额外接口。
    —— 该块未经过真实编译器与逐周期测试验证；编译通过不等于功能正确。
*)

(* K1：段号合法性与本段目标温度 *)
SegValid := (Segment >= 0) AND (Segment <= 2);
CASE Segment OF
    0: TargetTemp := SetTemp * 0.5;
    1: TargetTemp := SetTemp * 0.8;
    2: TargetTemp := SetTemp * 1.0;
ELSE
    (* 段号非法时按 0 段处理 *)
    TargetTemp := SetTemp * 0.5;
END_CASE;

(* K3：超温报警迟滞（> 目标+10℃ 置位；回落到 <= 目标-3℃ 才撤销） *)
IF TempPV > TargetTemp + 10.0 THEN
    OverTempAlarm := TRUE;
ELSIF TempPV <= TargetTemp - 3.0 THEN
    OverTempAlarm := FALSE;
END_IF;

(* 降载输出：超温降载 或 上位机请求降载 *)
LoadReduce := OverTempAlarm OR LoadReduceReq;

(* K2 / K3 / C1 / C4：加热判据带 ±5℃ 死区；降载优先关断加热且两者互斥 *)
IF LoadReduce THEN
    HeatOn := FALSE;
ELSIF TempPV < TargetTemp - 5.0 THEN
    HeatOn := TRUE;
ELSIF TempPV > TargetTemp + 5.0 THEN
    HeatOn := FALSE;
END_IF;

(* K4 / C2：加热运行必须伴随风机（单向蕴含，风机跟随加热） *)
FanOn := HeatOn;

(* Status 状态码：段号非法 > 超温降载 > 正常（C8 要求非法段下给出 8601） *)
IF NOT SegValid THEN
    Status := 16#8601;   (* 段号非法 *)
ELSIF OverTempAlarm THEN
    Status := 16#8602;   (* 超温降载 *)
ELSE
    Status := 16#0000;   (* 正常 *)
END_IF;

END_FUNCTION_BLOCK

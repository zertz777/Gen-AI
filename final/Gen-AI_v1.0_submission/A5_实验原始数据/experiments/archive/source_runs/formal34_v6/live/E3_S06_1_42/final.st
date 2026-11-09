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
    InitCounter : INT := 0;
    SegmentInvalidPrev : BOOL := FALSE;
    SegInvalidNow : BOOL;
    TargetTemp : REAL;
    HeatDemand : BOOL;
END_VAR

(* 冲突保留（未消解，需逐周期测试裁决）：
   1) 控制要求 K1/K3 将“目标值”定义为 SetTemp × (0.5/0.8/1.0) 后的 TargetTemp；
      形式化 C7 的保持/清除阈值写作 SetTemp - 3.0。
      本实现按 K1/K3 使用 TargetTemp +10 / TargetTemp -3；
      C7 的 SetTemp - 3.0 与分段目标存在语义冲突。
   2) C8 要求非法段下一周期 Status = 16#8601；要求5 超温降载 Status = 16#8602。
      若二者同时成立，本实现按 C8 优先 16#8601。
   3) LoadReduceReq 引起的降载状态码未在要求5中定义；
      本实现仅 OverTempAlarm 置 16#8602。
*)

SegInvalidNow := (Segment < 0) OR (Segment > 2);

IF InitCounter < 2 THEN
    (* C10：上电前两个扫描周期输出全部关断。 *)
    HeatOn := FALSE;
    FanOn := FALSE;
    OverTempAlarm := FALSE;
    LoadReduce := FALSE;

    IF SegInvalidNow OR SegmentInvalidPrev THEN
        Status := 16#8601;
    ELSE
        Status := 16#0000;
    END_IF;

    SegmentInvalidPrev := SegInvalidNow;
    InitCounter := InitCounter + 1;
ELSE
    (* K1：Segment 0/1/2 = SetTemp 的 50%/80%/100%；非法段按 0 段处理。 *)
    IF SegInvalidNow THEN
        TargetTemp := SetTemp * 0.5;
    ELSE
        CASE Segment OF
            0:
                TargetTemp := SetTemp * 0.5;
            1:
                TargetTemp := SetTemp * 0.8;
            2:
                TargetTemp := SetTemp * 1.0;
            ELSE
                TargetTemp := SetTemp * 0.5;
        END_CASE;
    END_IF;

    (* K3：超温 +10 置报警/降载，回落到目标值 -3 才撤销。 *)
    IF TempPV > TargetTemp + 10.0 THEN
        OverTempAlarm := TRUE;
    ELSIF TempPV <= TargetTemp - 3.0 THEN
        OverTempAlarm := FALSE;
    END_IF;

    LoadReduce := OverTempAlarm OR LoadReduceReq;

    (* K2：加热判据带 ±5 ℃ 死区，区间内保持上一周期 HeatOn。 *)
    IF TempPV < TargetTemp - 5.0 THEN
        HeatDemand := TRUE;
    ELSIF TempPV > TargetTemp + 5.0 THEN
        HeatDemand := FALSE;
    ELSE
        HeatDemand := HeatOn;
    END_IF;

    (* C1/C4：降载动作时加热必须关断，且加热与降载互斥。 *)
    IF LoadReduce THEN
        HeatDemand := FALSE;
    END_IF;

    (* K4/C2：HeatOn 为 TRUE 时 FanOn 必须为 TRUE；先开风机后加热。 *)
    IF HeatDemand THEN
        IF NOT FanOn THEN
            FanOn := TRUE;
            HeatOn := FALSE;
        ELSE
            HeatOn := TRUE;
            FanOn := TRUE;
        END_IF;
    ELSE
        HeatOn := FALSE;
        IF LoadReduce OR OverTempAlarm THEN
            FanOn := TRUE;
        ELSE
            FanOn := FALSE;
        END_IF;
    END_IF;

    (* Status：C8 的段号非法下一周期报错优先于超温降载状态。 *)
    IF SegInvalidNow OR SegmentInvalidPrev THEN
        Status := 16#8601;
    ELSIF OverTempAlarm THEN
        Status := 16#8602;
    ELSE
        Status := 16#0000;
    END_IF;

    SegmentInvalidPrev := SegInvalidNow;
END_IF;

END_FUNCTION_BLOCK

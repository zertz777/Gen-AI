FUNCTION_BLOCK FB_S06
VAR_INPUT
    TempPV : REAL;
    SetTemp : REAL;
    Segment : INT;
    LoadReduceReq : BOOL;
END_VAR
VAR_OUTPUT
    HeatOn : BOOL := FALSE;
    FanOn : BOOL := FALSE;
    OverTempAlarm : BOOL := FALSE;
    LoadReduce : BOOL := FALSE;
    Status : WORD := WORD#16#0000;
END_VAR
VAR
    TargetTemp : REAL;
    InvalidSegment : BOOL;
    PreviousInvalidSegment : BOOL := FALSE;
    HeatDemand : BOOL := FALSE;
    ThermalReduce : BOOL := FALSE;
    StartupScans : INT := 0;
END_VAR

(*
    每次调用为一个20 ms扫描。

    待审语义冲突：
    1. 原文要求“超温时必须先降载而不是直接断电”，
       C1/C4却要求降载时HeatOn立即关断。
       本实现执行形式化保护互斥；现有BOOL接口不能表达
       “先降低功率、后决定是否断电”的分阶段功率控制。

    2. C10的G[0,1]要求前两个扫描输出全部关断，
       与温度判据立即产生输出存在冲突。
       本实现前两个扫描执行启动抑制。

    3. 原文非法段号立即报8601，C8还要求下一扫描报8601。
       本实现同时保留当前和上一扫描非法段号状态；
       因此段号恢复合法后的首扫描仍报8601。
       与同时发生的8602状态码不能同时编码；
       8601优先显示，但不屏蔽超温保护输出。

    4. K3撤销降载使用分段目标且要求严格低于目标-3；
       C7报警保持使用未分段SetTemp且允许等于SetTemp-3。
       本实现分别处理降载与报警，并仅在两个恢复条件
       均满足时撤销报警；两者可能不同步。

    风机赋值先于加热赋值，满足输出逻辑联锁。
    接口没有风机反馈，不能据此证明风机已实际运行。
    本源码未声明已通过编译或逐周期功能验证。
*)

InvalidSegment := (Segment < 0) OR (Segment > 2);

CASE Segment OF
    0:
        TargetTemp := SetTemp * REAL#0.5;
    1:
        TargetTemp := SetTemp * REAL#0.8;
    2:
        TargetTemp := SetTemp;
ELSE
    TargetTemp := SetTemp * REAL#0.5;
END_CASE;

IF StartupScans < 2 THEN
    HeatDemand := FALSE;
    ThermalReduce := FALSE;
    HeatOn := FALSE;
    FanOn := FALSE;
    OverTempAlarm := FALSE;
    LoadReduce := FALSE;
    StartupScans := StartupScans + 1;
ELSE
    (* 严格比较；等于死区边界时保持原加热需求。 *)
    IF TempPV < (TargetTemp - REAL#5.0) THEN
        HeatDemand := TRUE;
    ELSIF TempPV > (TargetTemp + REAL#5.0) THEN
        HeatDemand := FALSE;
    END_IF;

    (* 温度降载独立保持，上位机请求不会清除温度锁存。 *)
    IF TempPV > (TargetTemp + REAL#10.0) THEN
        ThermalReduce := TRUE;
        OverTempAlarm := TRUE;
    ELSE
        IF TempPV < (TargetTemp - REAL#3.0) THEN
            ThermalReduce := FALSE;
        END_IF;

        IF (TempPV < (TargetTemp - REAL#3.0))
            AND (TempPV <= (SetTemp - REAL#3.0)) THEN
            OverTempAlarm := FALSE;
        END_IF;
    END_IF;

    LoadReduce := ThermalReduce OR LoadReduceReq;

    (* 先更新风机，再使能加热；降载优先于死区保持。 *)
    FanOn := HeatDemand AND NOT LoadReduce;
    HeatOn := HeatDemand AND FanOn AND NOT LoadReduce;
END_IF;

IF InvalidSegment OR PreviousInvalidSegment THEN
    Status := WORD#16#8601;
ELSIF LoadReduce OR OverTempAlarm THEN
    Status := WORD#16#8602;
ELSE
    Status := WORD#16#0000;
END_IF;

PreviousInvalidSegment := InvalidSegment;

END_FUNCTION_BLOCK

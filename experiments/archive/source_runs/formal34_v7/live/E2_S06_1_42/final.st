(*
需求原文：
烘箱按三段升温曲线工作，超温时必须先降载而不是直接断电。

控制要求：
1. Segment 取值 0/1/2，分别对应目标温度 SetTemp 的
   50%/80%/100%；段号非法时按 0 段处理并置 Status = 16#8601。
2. 当前温度 TempPV 低于目标值 -5 ℃ 时 HeatOn = TRUE，
   高于目标值 +5 ℃ 时 HeatOn = FALSE，两者之间保持（死区）。
3. TempPV 超过目标值 +10 ℃ 时置 OverTempAlarm = TRUE
   并置 LoadReduce = TRUE；TempPV 回落到目标值 -3 ℃ 以下
   才撤销 LoadReduce。
4. HeatOn = TRUE 期间 FanOn 必须为 TRUE
   （先开风机后加热，禁止干烧）。
5. Status：16#0000 正常、16#8601 段号非法、16#8602 超温降载。

扫描周期：20 ms。

完整形式化规约：
C1: G(LoadReduce -> !HeatOn)
C2: G(HeatOn -> FanOn)
C4: G(!(HeatOn && LoadReduce))
C7: G(OverTempAlarm ->
       (OverTempAlarm W TempPV <= SetTemp - 3.0))
C8: G(Segment < 0 || Segment > 2 -> X(Status == 16#8601))
C10: G[0,1](!HeatOn && !FanOn && !OverTempAlarm && !LoadReduce)

修改说明：
- 最新逐周期测试为 2/5 通过。
- S06-03 周期 2 的 Status 实际为 34305，即 16#8601，
  测试要求恢复为 16#0000。删除上一扫描非法段号记忆，
  Status 仅根据当前扫描的段号及保护状态计算。
- S06-04、S06-05 周期 1 要求 FanOn = FALSE。
  删除降载及报警独立启动风机的逻辑，
  风机仅在有温控加热请求且未降载时开启。
- 保留外部接口、声明初态、分段目标及温控和保护迟滞。

语义冲突报告：
- 测试要求非法段号恢复合法后立即清除错误码，
  与 C8 要求非法段号的下一周期仍报 16#8601 冲突。
  本实现采用当前扫描状态，不满足该转换场景下的 C8。
- 先前测试要求周期 1 立即开启加热或保护输出，
  与 C10 在 [0,1] 内全部 BOOL 输出为 FALSE 的要求冲突。
  本实现仅在首次调用前保持声明初态，扫描中立即响应，
  不满足扫描输出意义上的 C10。
- “先降载而不是直接断电”与 C1/C4 强制降载时关闭 HeatOn
  存在冲突；本实现按 C1/C4 禁止降载期间加热，
  不声称实现了保持加热的分级降功率。
- 同一扫描内先赋值 FanOn 再计算 HeatOn，满足输出联锁，
  但不能证明物理风机已先启动。接口没有风机运行反馈。
- 温控开启要求受降载保护覆盖；内部温控请求保持死区状态。
- 非法段号错误优先于超温降载状态。
- C7 使用 SetTemp，而温控/降载要求使用分段目标。
  报警仅在同时低于分段目标 -3 ℃ 且不高于 SetTemp -3 ℃
  时清除，避免提前违反任一保持边界。
- LoadReduceReq 的组合规则未给出：
  采用与超温降载锁存的逻辑或；请求持续时不撤销降载。
  请求降载不单独触发超温报警或超温状态码。
- 阈值“低于/高于/超过/以下”采用严格比较；
  等于阈值时保持迟滞状态。C7 的解除边界采用 <=。
- 用户提供的检查通过结果针对修改前版本；其功能测试仍失败。
  当前没有可调用的命令执行工具，未重新运行本版本编译和测试。
  本次修改针对已报告的失败，不能证明所有逐周期测试均通过，
  也不能声称满足存在冲突的全部规约。
*)
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
    TargetTemp : REAL := 0.0;
    InvalidSegment : BOOL := FALSE;
    HeatDemand : BOOL := FALSE;
    ThermalReduce : BOOL := FALSE;
END_VAR

InvalidSegment := (Segment < 0) OR (Segment > 2);

CASE Segment OF
    0:
        TargetTemp := SetTemp * 0.5;
    1:
        TargetTemp := SetTemp * 0.8;
    2:
        TargetTemp := SetTemp;
ELSE
    TargetTemp := SetTemp * 0.5;
END_CASE;

(* 温控请求在两个严格阈值之间保持。 *)
IF TempPV < (TargetTemp - 5.0) THEN
    HeatDemand := TRUE;
ELSIF TempPV > (TargetTemp + 5.0) THEN
    HeatDemand := FALSE;
END_IF;

(* 超温降载锁存与上位机降载请求独立处理。 *)
IF TempPV > (TargetTemp + 10.0) THEN
    ThermalReduce := TRUE;
    OverTempAlarm := TRUE;
ELSE
    IF TempPV < (TargetTemp - 3.0) THEN
        ThermalReduce := FALSE;
    END_IF;

    IF (TempPV < (TargetTemp - 3.0))
        AND (TempPV <= (SetTemp - 3.0)) THEN
        OverTempAlarm := FALSE;
    END_IF;
END_IF;

LoadReduce := ThermalReduce OR LoadReduceReq;

(* 风机仅服务于获准的加热请求，不由降载或报警单独启动。 *)
FanOn := HeatDemand AND NOT LoadReduce;

(* 先赋值风机输出，再计算具有降载保护及风机联锁的加热输出。 *)
HeatOn := HeatDemand AND NOT LoadReduce AND FanOn;

IF InvalidSegment THEN
    Status := WORD#16#8601;
ELSIF ThermalReduce OR OverTempAlarm THEN
    Status := WORD#16#8602;
ELSE
    Status := WORD#16#0000;
END_IF;

END_FUNCTION_BLOCK

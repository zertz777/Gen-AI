(*
【必留：需求原文】
温度变送器输出 4—20 mA，需要识别断线并降级运行，避免因单点故障停机。

控制要求：
1. SensorCurrent 在 4—20 mA 内时 SensorValid = TRUE，ControlValue = (SensorCurrent - 4) / 16 × 100（℃）。
2. SensorCurrent < 3.6 或 > 21 时判为断线：SensorValid = FALSE，持续 2 s 后置 DegradedMode = TRUE，ControlValue 切换为 FallbackValue。
3. 断线恢复（重新进入 3.8—20.5 mA）后 SensorValid = TRUE，但必须持续 3 s 才允许退出 DegradedMode；确认期内允许 SensorValid 与 DegradedMode 同为 TRUE，ControlValue 继续使用 FallbackValue（防止接线抖动反复切换）。
4. DegradedMode = TRUE 期间 AlarmLamp = TRUE；SensorValid = FALSE 但尚未满 2 s 时 AlarmLamp 闪烁（1 Hz）。
5. Status：16#0000 正常、16#8A01 断线、16#8A02 降级运行、16#8A03 恢复确认中。

扫描周期：20 ms（全组统一，见 docs/tasks_note.md）

【必留：接口、初态、约束与数据告警】
{
  "task_id": "S11",
  "title": "传感器断线检测与降级运行",
  "io_table": [
    {
      "direction": "IN",
      "name": "SensorCurrent",
      "data_type": "REAL",
      "description": "变送器电流（mA）"
    },
    {
      "direction": "IN",
      "name": "FallbackValue",
      "data_type": "REAL",
      "description": "降级时的备用控制值（℃）"
    },
    {
      "direction": "OUT",
      "name": "SensorValid",
      "data_type": "BOOL",
      "description": "信号有效"
    },
    {
      "direction": "OUT",
      "name": "DegradedMode",
      "data_type": "BOOL",
      "description": "降级运行中"
    },
    {
      "direction": "OUT",
      "name": "ControlValue",
      "data_type": "REAL",
      "description": "参与控制的温度值（℃）"
    },
    {
      "direction": "OUT",
      "name": "AlarmLamp",
      "data_type": "BOOL",
      "description": "报警灯"
    },
    {
      "direction": "OUT",
      "name": "Status",
      "data_type": "WORD",
      "description": "状态码"
    }
  ],
  "initial_state": "SensorValid = FALSE；DegradedMode = FALSE；ControlValue = 0.0；AlarmLamp = FALSE；Status = 16#0000；断线与恢复计时器均清零。",
  "constraints": [
    "K1 断线判据用 3.6 mA 与 21 mA，恢复判据用 3.8 mA 与 20.5 mA（进出阈值不同，构成滞回）。",
    "K2 断线持续 2 s 才进入降级，避免瞬时干扰导致切换。",
    "K3 恢复持续 3 s 才退出降级，退出前 ControlValue 继续使用 FallbackValue。",
    "K4 DegradedMode = TRUE 期间 ControlValue 必须等于 FallbackValue。"
  ],
  "semantic_warnings": [],
  "warnings": [],
  "missing_fields": [],
  "dialect_requirements": [],
  "type_origins": {}
}

【必留：完整形式化规约；有界时序以扫描周期计】
# task: S11
# meta: hard / D 故障与安全
# spec: version 1.0, updated 2026-10-30, scan cycle 20 ms
# 条款号对齐任务书 3.4 的条款库 C1—C10；[a,b] 单位为扫描周期。

C1: G(!SensorValid -> !DegradedMode || ControlValue == FallbackValue)    -- 信号无效时要么未降级、要么输出已切到备用值（不得停留在失效测量值）（K4）
C2: G(DegradedMode -> ControlValue == FallbackValue)    -- 降级期间包括恢复确认期始终使用备用值（K3/K4）
C9: G((DegradedMode && !SensorValid && X(SensorValid)) -> X(G[0,149](DegradedMode)))    -- 从断线转为恢复确认后保持降级 3 s；逐拍边界由 S11-03 核对（K3）
C4: G((DegradedMode && SensorValid) -> Status == 16#8A03)    -- 恢复确认期两者可同时为 TRUE，状态码为恢复确认中（K3）
C10: G[0,0](!DegradedMode && !SensorValid && ControlValue == 0.0)    -- 上电当拍未降级、未标定（初态）

实现说明与语义冲突报告：
1. 本次修复初始化分支跳过首次扫描输入处理的问题。
   首次调用先初始化，然后立即执行扫描逻辑，不消耗额外初始化扫描。
   每次调用固定代表 20 ms，不依赖厂商定时器或扩展。
2. 要求 1 的无条件有效测量输出与要求 3、K4 在降级恢复期存在冲突。
   本实现按 K4 优先：降级期间始终使用当前 FallbackValue。
3. 用户提供的逐周期测试要求第 1 周期有效输入立即使 SensorValid 为 TRUE，
   且第 1 周期断线输入立即使 AlarmLamp 为 TRUE。
   若 C10 的时间 0 指首次调用后的输出，则与这些测试要求存在冲突。
   本实现将初态解释为首次调用前的状态，首次调用处理当前输入。
   保留 C10 原文，不声称此解释已经获得形式化验证。
4. 3.6—3.8 mA、20.5—21 mA 的滞回带保持上一拍 SensorValid；
   初始状态无效。3.8—20.5 mA 的恢复区间包含端点。
   非降级且有效时使用原始线性换算，不额外限幅；
   非降级且无效时保持上一控制值。
5. 断线计数仅在严格断线判据连续成立时累计；
   第 100 个连续断线扫描进入降级，其他输入使断线计数清零。
   首次调用也参与断线计数。
6. 恢复首拍计时为 0；恢复首拍及随后 149 拍保持降级，
   再下一拍且恢复区间持续成立时退出，遵循 C9。
   任一拍离开恢复区间，恢复计数和确认状态清零。
7. 无效但未降级时，报警灯按 25 拍亮、25 拍灭闪烁，
   首个无效扫描亮灯；降级时常亮，有效且未降级时熄灭。
8. 用户提供的旧版本检查输出第一部分为 pass，
   逐周期功能测试为 fail，5 个用例均在第 1 周期失败。
   本次修改尚未运行编译或逐周期测试；当前无可执行工具。
   编译通过仅证明编译，功能正确仍须由逐周期测试判定，
   尤其需要核对 S11-03 的恢复边界。
*)

FUNCTION_BLOCK FB_S11
VAR_INPUT
    SensorCurrent : REAL;
    FallbackValue : REAL;
END_VAR
VAR_OUTPUT
    SensorValid : BOOL := FALSE;
    DegradedMode : BOOL := FALSE;
    ControlValue : REAL := 0.0;
    AlarmLamp : BOOL := FALSE;
    Status : WORD := WORD#16#0000;
END_VAR
VAR
    Initialized : BOOL := FALSE;
    FaultNow : BOOL := FALSE;
    RecoveryNow : BOOL := FALSE;
    FaultScans : UINT := UINT#0;
    RecoveryScans : UINT := UINT#0;
    RecoveryTracking : BOOL := FALSE;
    BlinkPhase : UINT := UINT#0;
END_VAR

IF NOT Initialized THEN
    SensorValid := FALSE;
    DegradedMode := FALSE;
    ControlValue := 0.0;
    AlarmLamp := FALSE;
    Status := WORD#16#0000;

    FaultNow := FALSE;
    RecoveryNow := FALSE;
    FaultScans := UINT#0;
    RecoveryScans := UINT#0;
    RecoveryTracking := FALSE;
    BlinkPhase := UINT#0;
    Initialized := TRUE;
END_IF;

FaultNow := (SensorCurrent < 3.6) OR (SensorCurrent > 21.0);
RecoveryNow := (SensorCurrent >= 3.8) AND (SensorCurrent <= 20.5);

IF FaultNow THEN
    SensorValid := FALSE;
ELSIF RecoveryNow THEN
    SensorValid := TRUE;
END_IF;

IF FaultNow THEN
    IF FaultScans < UINT#100 THEN
        FaultScans := FaultScans + UINT#1;
    END_IF;
ELSE
    FaultScans := UINT#0;
END_IF;

IF NOT DegradedMode THEN
    RecoveryScans := UINT#0;
    RecoveryTracking := FALSE;

    IF FaultScans >= UINT#100 THEN
        DegradedMode := TRUE;
    END_IF;
ELSE
    IF RecoveryNow THEN
        IF NOT RecoveryTracking THEN
            RecoveryTracking := TRUE;
            RecoveryScans := UINT#0;
        ELSE
            IF RecoveryScans < UINT#150 THEN
                RecoveryScans := RecoveryScans + UINT#1;
            END_IF;

            IF RecoveryScans >= UINT#150 THEN
                DegradedMode := FALSE;
                RecoveryScans := UINT#0;
                RecoveryTracking := FALSE;
            END_IF;
        END_IF;
    ELSE
        RecoveryScans := UINT#0;
        RecoveryTracking := FALSE;
    END_IF;
END_IF;

IF DegradedMode THEN
    ControlValue := FallbackValue;
ELSIF SensorValid THEN
    ControlValue := ((SensorCurrent - 4.0) / 16.0) * 100.0;
END_IF;

IF DegradedMode THEN
    AlarmLamp := TRUE;
    BlinkPhase := UINT#0;

    IF SensorValid THEN
        Status := WORD#16#8A03;
    ELSE
        Status := WORD#16#8A02;
    END_IF;
ELSIF NOT SensorValid THEN
    AlarmLamp := BlinkPhase < UINT#25;
    Status := WORD#16#8A01;

    IF BlinkPhase >= UINT#49 THEN
        BlinkPhase := UINT#0;
    ELSE
        BlinkPhase := BlinkPhase + UINT#1;
    END_IF;
ELSE
    AlarmLamp := FALSE;
    BlinkPhase := UINT#0;
    Status := WORD#16#0000;
END_IF;

END_FUNCTION_BLOCK

(*
  语义冲突报告（保留并报告，不自行消解）：
  1. 条件1：SensorCurrent 在 4—20 mA 内时 SensorValid = TRUE，ControlValue = (SensorCurrent - 4) / 16 × 100。
  2. 条件3：断线恢复后重新进入 3.8—20.5 mA 时 SensorValid = TRUE。
  冲突：有效范围定义不一致，导致 3.8—4 和 20—20.5 区间 SensorValid 的含义冲突。
  本实现按滞回处理：明确断线判据 <3.6 或 >21 置 SensorValid=FALSE；恢复判据 3.8—20.5 置 SensorValid=TRUE；
  中间区（3.6—3.8 和 20.5—21）保持前一状态。因此 ControlValue 在 3.8—4 区间会得到负值，
  在 20—20.5 区间会大于 100，此为本保留冲突，未新增接口。
  编译通过仅证明语法正确；功能正确必须由逐周期测试判定。
*)

FUNCTION_BLOCK FB_S11
VAR_INPUT
    SensorCurrent : REAL;
    FallbackValue : REAL;
END_VAR
VAR_OUTPUT
    SensorValid : BOOL;
    DegradedMode : BOOL;
    ControlValue : REAL;
    AlarmLamp : BOOL;
    Status : WORD;
END_VAR
VAR
    State : INT;
    FaultTimer : INT;
    RecoverTimer : INT;
    BlinkTimer : INT;
    LastValidControlValue : REAL;
    FaultNow : BOOL;
    RecoverOK : BOOL;
    FirstScan : BOOL;
END_VAR

FaultNow := (SensorCurrent < 3.6) OR (SensorCurrent > 21.0);
RecoverOK := (SensorCurrent >= 3.8) AND (SensorCurrent <= 20.5);

IF NOT FirstScan THEN
    FirstScan := TRUE;
    State := 0;
    FaultTimer := 0;
    RecoverTimer := 0;
    BlinkTimer := 0;
    LastValidControlValue := 0.0;
END_IF;

CASE State OF
    0:
        IF FaultNow THEN
            State := 1;
            FaultTimer := 1;
            SensorValid := FALSE;
            BlinkTimer := 0;
        ELSE
            SensorValid := TRUE;
        END_IF;
    1:
        IF RecoverOK THEN
            State := 0;
            FaultTimer := 0;
            SensorValid := TRUE;
        ELSIF FaultNow THEN
            FaultTimer := FaultTimer + 1;
            SensorValid := FALSE;
            IF FaultTimer >= 100 THEN
                State := 2;
                FaultTimer := 0;
                RecoverTimer := 0;
            END_IF;
        ELSE
            SensorValid := FALSE;
        END_IF;
    2:
        IF RecoverOK THEN
            State := 3;
            RecoverTimer := 1;
            SensorValid := TRUE;
        ELSIF FaultNow THEN
            RecoverTimer := 0;
            SensorValid := FALSE;
        ELSE
            SensorValid := FALSE;
        END_IF;
    3:
        IF FaultNow THEN
            State := 2;
            RecoverTimer := 0;
            SensorValid := FALSE;
        ELSIF RecoverOK THEN
            RecoverTimer := RecoverTimer + 1;
            SensorValid := TRUE;
            IF RecoverTimer > 150 THEN
                State := 0;
                RecoverTimer := 0;
            END_IF;
        ELSE
            SensorValid := TRUE;
        END_IF;
END_CASE;

CASE State OF
    0:
        DegradedMode := FALSE;
        Status := 16#0000;
        AlarmLamp := FALSE;
        ControlValue := (SensorCurrent - 4.0) / 16.0 * 100.0;
        LastValidControlValue := ControlValue;
    1:
        DegradedMode := FALSE;
        Status := 16#8A01;
        ControlValue := LastValidControlValue;
        BlinkTimer := BlinkTimer + 1;
        IF BlinkTimer >= 50 THEN
            BlinkTimer := 0;
        END_IF;
        IF BlinkTimer < 25 THEN
            AlarmLamp := TRUE;
        ELSE
            AlarmLamp := FALSE;
        END_IF;
    2:
        DegradedMode := TRUE;
        Status := 16#8A02;
        ControlValue := FallbackValue;
        AlarmLamp := TRUE;
    3:
        DegradedMode := TRUE;
        Status := 16#8A03;
        ControlValue := FallbackValue;
        AlarmLamp := TRUE;
END_CASE;

END_FUNCTION_BLOCK

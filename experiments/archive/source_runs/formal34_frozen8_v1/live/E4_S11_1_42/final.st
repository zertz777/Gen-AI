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
    FaultDetected : BOOL := FALSE;
    RecoveryBand : BOOL := FALSE;
    FaultScans : UINT := UINT#0;
    RecoveryScans : UINT := UINT#0;
    BlinkPhase : UINT := UINT#0;
END_VAR

(*
    每次调用代表 20 ms，不依赖实际墙钟时间。

    待审语义冲突：
    若上电输入已在 4..20 mA，要求 1 的即时有效判定与
    C10 的上电当拍 SensorValid = FALSE 不能同时成立。
    本实现保留 C10 指定的首拍初态，从第二拍开始处理输入；
    该首拍例外仍需需求方确认，不能据此声称全部要求已验证。

    阈值间隙按 K1 的滞回处理：保持此前 SensorValid。
    非降级且信号无效时保持此前 ControlValue。
    有效信号采用线性换算；恢复区间超出 4..20 mA 的部分
    同样线性外推，不自行增加限幅要求。

    恢复首拍至第 150 拍均保持降级，第 151 拍才允许退出，
    以满足 C9 的 G[0,149] 保持窗口。
*)

IF NOT Initialized THEN
    SensorValid := FALSE;
    DegradedMode := FALSE;
    ControlValue := 0.0;
    AlarmLamp := FALSE;
    Status := WORD#16#0000;

    FaultDetected := FALSE;
    RecoveryBand := FALSE;
    FaultScans := UINT#0;
    RecoveryScans := UINT#0;
    BlinkPhase := UINT#0;
    Initialized := TRUE;
ELSE
    FaultDetected :=
        (SensorCurrent < 3.6) OR (SensorCurrent > 21.0);
    RecoveryBand :=
        (SensorCurrent >= 3.8) AND (SensorCurrent <= 20.5);

    (* 断线判据优先；中间区间保持有效性状态。 *)
    IF FaultDetected THEN
        SensorValid := FALSE;
    ELSIF RecoveryBand THEN
        SensorValid := TRUE;
    END_IF;

    IF DegradedMode THEN
        FaultScans := UINT#0;

        (* 必须连续处于恢复区间，才能完成恢复确认。 *)
        IF SensorValid AND RecoveryBand THEN
            IF RecoveryScans < UINT#150 THEN
                RecoveryScans := RecoveryScans + UINT#1;
            ELSE
                DegradedMode := FALSE;
                RecoveryScans := UINT#0;
            END_IF;
        ELSE
            RecoveryScans := UINT#0;
        END_IF;
    ELSE
        RecoveryScans := UINT#0;

        (* 滞回锁存的无效状态连续 100 个扫描后进入降级。 *)
        IF NOT SensorValid THEN
            IF FaultScans < UINT#100 THEN
                FaultScans := FaultScans + UINT#1;
            END_IF;

            IF FaultScans >= UINT#100 THEN
                DegradedMode := TRUE;
                RecoveryScans := UINT#0;
            END_IF;
        ELSE
            FaultScans := UINT#0;
        END_IF;
    END_IF;

    (* 降级优先，包含整个恢复确认期。 *)
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
        (* 25 拍亮、25 拍灭：周期 1 s，即 1 Hz。 *)
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
END_IF;

END_FUNCTION_BLOCK

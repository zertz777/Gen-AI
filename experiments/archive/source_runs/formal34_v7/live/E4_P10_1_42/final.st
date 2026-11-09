FUNCTION_BLOCK FB_P10
VAR_INPUT
    TemperatureSensorInput : REAL;
    SetTemperature : REAL;
END_VAR
VAR_OUTPUT
    CurrentTemperature : REAL;
    SetTempDisplay : REAL;
    HeaterStatus : BOOL := FALSE;
    OverheatProtection : BOOL := FALSE;
    HeaterOutput : BOOL := FALSE;
END_VAR
VAR
    StartupScans : UINT := 0;
    HeatingScans : UINT := 0;
    ProtectionScans : UINT := 0;
    SensorFault : BOOL := FALSE;
    PreviousSensorFault : BOOL := FALSE;
END_VAR

(*
    每次调用代表20 ms；计数记录上一输出实际保持的完整周期。
    本源码未经过真实编译或逐周期功能验证。

    规约冲突报告：
    C9 为 G(P -> G[0,150](P))。保护保持期间，每个周期均再次
    要求随后150周期保持保护，因此一旦触发，保护不能再解除。
    这与需求所述等待3 s后解除保护的意图不一致。
    本实现保留C9的字面安全约束，锁存保护，不擅自改写C9，
    不新增复位接口。3 s计时完成不会解除该锁存，解除行为待审。

    C10按形式化区间[0,1]实现：启动前两次调用关闭加热且无保护。
    温度等于设定值时需求未指定切换，保持此前加热状态；
    故障和过热保护始终优先。
    C7/C7b要求故障后的下一周期关闭，故保留上一周期故障状态；
    当前周期检测到故障也立即关闭。
*)

CurrentTemperature := TemperatureSensorInput;
SetTempDisplay := SetTemperature;

SensorFault := (TemperatureSensorInput < 0.0)
            OR (TemperatureSensorInput > 100.0);

IF StartupScans < 2 THEN
    StartupScans := StartupScans + 1;
    HeaterOutput := FALSE;
    OverheatProtection := FALSE;
    HeatingScans := 0;
    ProtectionScans := 0;
ELSE
    IF OverheatProtection THEN
        HeaterOutput := FALSE;
        HeatingScans := 0;

        IF ProtectionScans < 150 THEN
            ProtectionScans := ProtectionScans + 1;
        END_IF;

        (* C9要求继续锁存，即使已完成150个等待周期。 *)
    ELSE
        ProtectionScans := 0;

        (* 上次输出为TRUE，表示已经完成一个20 ms加热周期。 *)
        IF HeaterOutput THEN
            IF HeatingScans < 251 THEN
                HeatingScans := HeatingScans + 1;
            END_IF;
        ELSE
            HeatingScans := 0;
        END_IF;

        (* “超过5 s”采用严格大于：251个完整周期为5.02 s。 *)
        IF HeatingScans > 250 THEN
            OverheatProtection := TRUE;
            HeaterOutput := FALSE;
            HeatingScans := 0;
            ProtectionScans := 0;
        ELSIF SensorFault OR PreviousSensorFault THEN
            HeaterOutput := FALSE;
            HeatingScans := 0;
        ELSIF TemperatureSensorInput < SetTemperature THEN
            HeaterOutput := TRUE;
        ELSIF TemperatureSensorInput > SetTemperature THEN
            HeaterOutput := FALSE;
            HeatingScans := 0;
        END_IF;
    END_IF;
END_IF;

(* 最终安全仲裁及状态显示。 *)
IF OverheatProtection OR SensorFault OR PreviousSensorFault THEN
    HeaterOutput := FALSE;
    HeatingScans := 0;
END_IF;

HeaterStatus := HeaterOutput;
PreviousSensorFault := SensorFault;

END_FUNCTION_BLOCK

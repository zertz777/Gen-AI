FUNCTION_BLOCK FB_P10
VAR_INPUT
    TemperatureSensorInput : REAL;
    SetTemperature : REAL;
END_VAR
VAR_OUTPUT
    CurrentTemperature : REAL;
    SetTempDisplay : REAL;
    HeaterStatus : BOOL;
    OverheatProtection : BOOL;
    HeaterOutput : BOOL;
END_VAR
VAR
    FirstScan : BOOL := TRUE;
    SensorFaultNow : BOOL := FALSE;
    SensorFaultInhibit : BOOL := FALSE;
    HeaterRunTimer : UINT := 0;
    OverheatTimer : UINT := 0;
END_VAR
VAR CONSTANT
    OVERHEAT_TRIGGER_SCANS : UINT := 250; (* 5 s / 20 ms *)
    OVERHEAT_HOLD_SCANS : UINT := 150;    (* 3 s / 20 ms *)
END_VAR

(* 显示当前温度与设定温度 *)
CurrentTemperature := TemperatureSensorInput;
SetTempDisplay := SetTemperature;

(* 当前周期传感器越界判定：< 0 或 > 100 视为故障 *)
SensorFaultNow := (TemperatureSensorInput < 0.0) OR (TemperatureSensorInput > 100.0);

(* 上电首周期安全初态：不加热、无过热保护 *)
IF FirstScan THEN
    HeaterOutput := FALSE;
    HeaterStatus := FALSE;
    OverheatProtection := FALSE;
    HeaterRunTimer := 0;
    OverheatTimer := 0;
    FirstScan := FALSE;
ELSE
    (* 安全优先级 1：过热保护优先，保护期间强制关断加热 *)
    IF OverheatProtection THEN
        HeaterOutput := FALSE;
        HeaterRunTimer := 0;

        (* 过热保护至少保持 3 s 才能解除；解除周期仍不重新加热 *)
        IF OverheatTimer >= OVERHEAT_HOLD_SCANS THEN
            OverheatProtection := FALSE;
            OverheatTimer := 0;
        ELSE
            OverheatTimer := OverheatTimer + 1;
        END_IF;
    ELSE
        (* 安全优先级 2：传感器故障优先于温控。
           当前越界或上一周期越界，本周期均禁止加热。 *)
        IF SensorFaultNow OR SensorFaultInhibit THEN
            HeaterOutput := FALSE;
            HeaterRunTimer := 0;
        ELSE
            (* 温度控制：低于设定值加热；大于或等于设定值停止加热 *)
            IF TemperatureSensorInput < SetTemperature THEN
                HeaterOutput := TRUE;
            ELSE
                HeaterOutput := FALSE;
            END_IF;

            (* 连续加热计时；超过 5 s 触发过热保护并强制关断 *)
            IF HeaterOutput THEN
                IF HeaterRunTimer >= OVERHEAT_TRIGGER_SCANS THEN
                    OverheatProtection := TRUE;
                    HeaterOutput := FALSE;
                    HeaterRunTimer := 0;
                    OverheatTimer := 0;
                ELSE
                    HeaterRunTimer := HeaterRunTimer + 1;
                END_IF;
            ELSE
                HeaterRunTimer := 0;
            END_IF;
        END_IF;
    END_IF;
END_IF;

(* 本周期越界则下一周期仍禁止加热，满足 C7/C7b 的 X(!HeaterOutput) *)
SensorFaultInhibit := SensorFaultNow;

(* 加热器状态显示与实际输出一致 *)
HeaterStatus := HeaterOutput;

END_FUNCTION_BLOCK

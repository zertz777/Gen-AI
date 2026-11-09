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
    (* 连续加热扫描周期计数，5 s = 250 个扫描周期 *)
    HeatTimer : UINT := 0;
    (* 过热保护保持扫描周期计数，3 s = 150 个扫描周期 *)
    ProtectTimer : UINT := 0;
    (* 传感器故障标志（越界：< 0 或 > 100） *)
    SensorFault : BOOL := FALSE;
END_VAR

(* ------------------------------------------------------------ *)
(* 状态显示：当前温度 / 设定温度                                  *)
(* ------------------------------------------------------------ *)
CurrentTemperature := TemperatureSensorInput;
SetTempDisplay := SetTemperature;

(* ------------------------------------------------------------ *)
(* 传感器故障判断（K4）：< 0 ℃ 或 > 100 ℃                          *)
(* ------------------------------------------------------------ *)
SensorFault := (TemperatureSensorInput < 0.0)
               OR (TemperatureSensorInput > 100.0);

IF OverheatProtection THEN
    (* -------------------------------------------------------- *)
    (* 过热保护保持阶段（K3，C9）                                 *)
    (* 强制关断加热器（C1），并至少保持 3 s                       *)
    (* -------------------------------------------------------- *)
    HeaterOutput := FALSE;
    HeatTimer := 0;
    ProtectTimer := ProtectTimer + 1;
    (* 触发周期 + 后续 150 个周期 => 计数到 151 才解除            *)
    IF ProtectTimer >= 151 THEN
        OverheatProtection := FALSE;
        ProtectTimer := 0;
    END_IF;

ELSIF SensorFault THEN
    (* -------------------------------------------------------- *)
    (* 传感器故障（K4）：禁止加热                                 *)
    (* -------------------------------------------------------- *)
    HeaterOutput := FALSE;
    HeatTimer := 0;

ELSE
    (* -------------------------------------------------------- *)
    (* 正常温控逻辑（K1）                                        *)
    (* -------------------------------------------------------- *)
    IF TemperatureSensorInput < SetTemperature THEN
        IF HeatTimer >= 250 THEN
            (* 连续加热达到 5 s（K2）：触发过热保护                *)
            OverheatProtection := TRUE;
            ProtectTimer := 0;
            HeaterOutput := FALSE;
            HeatTimer := 0;
        ELSE
            HeaterOutput := TRUE;
            HeatTimer := HeatTimer + 1;
        END_IF;
    ELSE
        (* 高于或等于设定值：停止加热                             *)
        HeaterOutput := FALSE;
        HeatTimer := 0;
    END_IF;
END_IF;

(* 加热器状态显示 *)
HeaterStatus := HeaterOutput;

END_FUNCTION_BLOCK

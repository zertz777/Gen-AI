FUNCTION_BLOCK FB_P01
VAR_INPUT
    bottleSensor : BOOL;
    cleaningConfirmButton : BOOL;
    fillingConfirmButton : BOOL;
    cappingConfirmButton : BOOL;
    packingConfirmButton : BOOL;
    finishedButton : BOOL;
END_VAR
VAR_OUTPUT
    Pump_Motor : BOOL;
    Filling_Valve : BOOL;
    Capping_Machine : BOOL;
    Packing_Machine : BOOL;
    Completion_Light : BOOL;
END_VAR
VAR
    step : INT := 0;
    prevCleaningConfirmButton : BOOL := FALSE;
    prevFillingConfirmButton : BOOL := FALSE;
    prevCappingConfirmButton : BOOL := FALSE;
    prevPackingConfirmButton : BOOL := FALSE;
    cleaningConfirmEdge : BOOL;
    fillingConfirmEdge : BOOL;
    cappingConfirmEdge : BOOL;
    packingConfirmEdge : BOOL;
END_VAR

(* 按钮上升沿检测 *)
cleaningConfirmEdge := cleaningConfirmButton AND NOT prevCleaningConfirmButton;
fillingConfirmEdge := fillingConfirmButton AND NOT prevFillingConfirmButton;
cappingConfirmEdge := cappingConfirmButton AND NOT prevCappingConfirmButton;
packingConfirmEdge := packingConfirmButton AND NOT prevPackingConfirmButton;

prevCleaningConfirmButton := cleaningConfirmButton;
prevFillingConfirmButton := fillingConfirmButton;
prevCappingConfirmButton := cappingConfirmButton;
prevPackingConfirmButton := packingConfirmButton;

(* 安全优先级：finishedButton 为 TRUE 时，停止四路执行器、熄灭完成灯、回到等待瓶子 *)
IF finishedButton THEN
    step := 0;
    Pump_Motor := FALSE;
    Filling_Valve := FALSE;
    Capping_Machine := FALSE;
    Packing_Machine := FALSE;
    Completion_Light := FALSE;
ELSE
    CASE step OF
        0:  (* 等待瓶子 *)
            Pump_Motor := FALSE;
            Filling_Valve := FALSE;
            Capping_Machine := FALSE;
            Packing_Machine := FALSE;
            Completion_Light := FALSE;
            IF bottleSensor THEN
                step := 1;
                Pump_Motor := TRUE;
            END_IF;

        1:  (* 清洗：泵受 bottleSensor 控制，瓶子离开时停泵并保持本工步 *)
            Filling_Valve := FALSE;
            Capping_Machine := FALSE;
            Packing_Machine := FALSE;
            Completion_Light := FALSE;
            Pump_Motor := bottleSensor;
            IF cleaningConfirmEdge THEN
                step := 2;
                Pump_Motor := FALSE;
                Filling_Valve := TRUE;
            END_IF;

        2:  (* 灌装 *)
            Pump_Motor := FALSE;
            Capping_Machine := FALSE;
            Packing_Machine := FALSE;
            Completion_Light := FALSE;
            Filling_Valve := TRUE;
            IF fillingConfirmEdge THEN
                step := 3;
                Filling_Valve := FALSE;
                Capping_Machine := TRUE;
            END_IF;

        3:  (* 封盖 *)
            Pump_Motor := FALSE;
            Filling_Valve := FALSE;
            Packing_Machine := FALSE;
            Completion_Light := FALSE;
            Capping_Machine := TRUE;
            IF cappingConfirmEdge THEN
                step := 4;
                Capping_Machine := FALSE;
                Packing_Machine := TRUE;
            END_IF;

        4:  (* 包装 *)
            Pump_Motor := FALSE;
            Filling_Valve := FALSE;
            Capping_Machine := FALSE;
            Completion_Light := FALSE;
            Packing_Machine := TRUE;
            IF packingConfirmEdge THEN
                step := 5;
                Packing_Machine := FALSE;
                Completion_Light := TRUE;
            END_IF;

        5:  (* 包装完成，点亮指示灯，等待 finishedButton 复位 *)
            Pump_Motor := FALSE;
            Filling_Valve := FALSE;
            Capping_Machine := FALSE;
            Packing_Machine := FALSE;
            Completion_Light := TRUE;

        ELSE
            (* 异常状态复位 *)
            step := 0;
            Pump_Motor := FALSE;
            Filling_Valve := FALSE;
            Capping_Machine := FALSE;
            Packing_Machine := FALSE;
            Completion_Light := FALSE;
    END_CASE;
END_IF;

END_FUNCTION_BLOCK

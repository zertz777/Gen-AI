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
    Pump_Motor : BOOL := FALSE;
    Filling_Valve : BOOL := FALSE;
    Capping_Machine : BOOL := FALSE;
    Packing_Machine : BOOL := FALSE;
    Completion_Light : BOOL := FALSE;
END_VAR
VAR
    initialized : BOOL := FALSE;
    step : INT := 0;

    previousCleaning : BOOL := FALSE;
    previousFilling : BOOL := FALSE;
    previousCapping : BOOL := FALSE;
    previousPacking : BOOL := FALSE;

    cleaningEdge : BOOL;
    fillingEdge : BOOL;
    cappingEdge : BOOL;
    packingEdge : BOOL;
END_VAR

(* 每次调用为一个20 ms扫描。
   工步：0等待、1清洗、2灌装、3封盖、4包装、5完成。
   C3中的W公式本身不表达历史确认；顺序要求由工步转换落实。
   未提供真实编译或逐周期测试结果。 *)

cleaningEdge := cleaningConfirmButton AND NOT previousCleaning;
fillingEdge := fillingConfirmButton AND NOT previousFilling;
cappingEdge := cappingConfirmButton AND NOT previousCapping;
packingEdge := packingConfirmButton AND NOT previousPacking;

(* 每拍先关闭全部输出，再按唯一工步生成输出。 *)
Pump_Motor := FALSE;
Filling_Valve := FALSE;
Capping_Machine := FALSE;
Packing_Machine := FALSE;
Completion_Light := FALSE;

IF NOT initialized THEN
    (* C9：首次调用全部输出保持FALSE，不在上电当拍启动。 *)
    initialized := TRUE;
    step := 0;

ELSIF finishedButton THEN
    (* 最高优先级，电平有效；按住期间不启动下一瓶。 *)
    step := 0;

ELSE
    (* 每拍最多一次工步转换；非当前工步的确认不缓存。 *)
    CASE step OF
        0:
            IF bottleSensor THEN
                step := 1;
            END_IF;

        1:
            (* 瓶子离开时保持清洗工步，暂停期间不接受完成确认。 *)
            IF bottleSensor AND cleaningEdge THEN
                step := 2;
            END_IF;

        2:
            IF fillingEdge THEN
                step := 3;
            END_IF;

        3:
            IF cappingEdge THEN
                step := 4;
            END_IF;

        4:
            IF packingEdge THEN
                step := 5;
            END_IF;

        5:
            (* 完成状态保持，直至finishedButton有效。 *)

    ELSE
        (* 非法内部状态安全回到等待，当前拍不启动。 *)
        step := 0;
    END_CASE;

    CASE step OF
        1:
            Pump_Motor := bottleSensor;
        2:
            Filling_Valve := TRUE;
        3:
            Capping_Machine := TRUE;
        4:
            Packing_Machine := TRUE;
        5:
            Completion_Light := TRUE;
    END_CASE;
END_IF;

(* 首拍及复位期间同样更新历史，避免按住按钮导致重复推进。 *)
previousCleaning := cleaningConfirmButton;
previousFilling := fillingConfirmButton;
previousCapping := cappingConfirmButton;
previousPacking := packingConfirmButton;

END_FUNCTION_BLOCK

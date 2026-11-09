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
    (* 工步状态：0=等瓶子 1=清洗 2=灌装 3=封盖 4=包装 5=完成等取瓶 *)
    step : INT := 0;
    (* 各确认按钮的上一拍值，用于上升沿检测 *)
    prevCleaningConfirm : BOOL := FALSE;
    prevFillingConfirm  : BOOL := FALSE;
    prevCappingConfirm  : BOOL := FALSE;
    prevPackingConfirm  : BOOL := FALSE;
    (* 本拍上升沿标志 *)
    rTrigCleaning : BOOL := FALSE;
    rTrigFilling  : BOOL := FALSE;
    rTrigCapping  : BOOL := FALSE;
    rTrigPacking  : BOOL := FALSE;
END_VAR

(* ---------- 按钮上升沿检测（每个确认按钮只在按下瞬间触发一次推进） ---------- *)
rTrigCleaning := cleaningConfirmButton AND NOT prevCleaningConfirm;
rTrigFilling  := fillingConfirmButton  AND NOT prevFillingConfirm;
rTrigCapping  := cappingConfirmButton  AND NOT prevCappingConfirm;
rTrigPacking  := packingConfirmButton  AND NOT prevPackingConfirm;

prevCleaningConfirm := cleaningConfirmButton;
prevFillingConfirm  := fillingConfirmButton;
prevCappingConfirm  := cappingConfirmButton;
prevPackingConfirm  := packingConfirmButton;

(* ---------- 顺序状态机 ----------
   finishedButton 有效（电平）时无条件回工步 0（K4）。
   其余情况按 清洗→灌装→封盖→包装 顺序推进（K1）。
   清洗步不因 bottleSensor 变 FALSE 而丢弃步号，瓶子离开只是停泵（K3）。 *)
IF finishedButton THEN
    step := 0;
ELSIF step = 0 THEN
    IF bottleSensor THEN
        step := 1;
    END_IF;
ELSIF step = 1 THEN
    IF rTrigCleaning THEN
        step := 2;
    END_IF;
ELSIF step = 2 THEN
    IF rTrigFilling THEN
        step := 3;
    END_IF;
ELSIF step = 3 THEN
    IF rTrigCapping THEN
        step := 4;
    END_IF;
ELSIF step = 4 THEN
    IF rTrigPacking THEN
        step := 5;
    END_IF;
END_IF;

(* ---------- 输出（单一工步 → 天然互斥，满足 K2/C4） ---------- *)
(* 清洗泵仅在清洗工步且瓶子在位时运行（K3 / C2） *)
Pump_Motor      := ((step = 1) AND bottleSensor);
Filling_Valve   := (step = 2);
Capping_Machine := (step = 3);
Packing_Machine := (step = 4);
Completion_Light := (step = 5);

(* finishedButton 当拍强制四路执行器全停（K4 / C1），
   即使同拍 bottleSensor 又为真也不允许执行器输出。 *)
IF finishedButton THEN
    Pump_Motor      := FALSE;
    Filling_Valve   := FALSE;
    Capping_Machine := FALSE;
    Packing_Machine := FALSE;
END_IF;

END_FUNCTION_BLOCK

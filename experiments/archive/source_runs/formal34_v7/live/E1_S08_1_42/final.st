FUNCTION_BLOCK FB_S08
VAR_INPUT
    RecipeSelect : INT;
    ChangeoverReq : BOOL;
    PartHeight : REAL;
    EStop_NC : BOOL;
END_VAR
VAR_OUTPUT
    ActiveRecipe : INT;
    SortLeft : BOOL;
    SortRight : BOOL;
    Busy : BOOL;
    Status : WORD;
END_VAR
VAR
    (* 内部状态与计时（扫描周期 20 ms） *)
    ChangeoverReqLast : BOOL := FALSE;
    BusyTimer : INT := 0;
    PendingRecipe : INT := 1;
    LeftThr : REAL := 30.0;
    RightThr : REAL := 60.0;
    RisingEdge : BOOL := FALSE;
END_VAR

(*
  实现说明与保留的语义冲突（接口未改动，未新增 I/O）：

  S08-CONFLICT-1  "保持 2 s" 与 C9 区间解释冲突
    题面：Busy 置 TRUE 并保持 2 s 后自动清除；2 s = 100 x 20 ms。
    规约 C9：G(Busy -> G[0,100](Busy))。若把 [0,100] 读作闭区间
    （含 t+100），则要求连续 101 个采样点 Busy = TRUE。
    本实现取"保持 100 个扫描周期"（自置位周期 t 起 t..t+99 为 TRUE，
    t+100 清除），与复位计时器的通行语义一致。按闭区间字面解释的 C9
    会在此处被违反 1 个扫描周期。冲突保留并报告，未暗中改写。

  S08-CONFLICT-2  初态 C10 与功能要求 2/5 冲突
    C10：G[0,1](!SortLeft && !SortRight && !Busy && ActiveRecipe == 1)。
    但要求 2 允许上电首周期即接受上升沿请求（置 Busy），要求 5 要求
    有料即分拣。本实现遵循功能要求（首周期即运算），C10 字面含义在
    首周期被放宽。

  S08-CONFLICT-5  ActiveRecipe 生效时刻：需求原文与逐周期测试不一致
    需求原文 2："若 Busy = FALSE 且当前无料，则 ActiveRecipe 切换为
    RecipeSelect，Busy 置 TRUE 并保持 2 s"。字面读作：请求被接受的
    同一周期 ActiveRecipe 立即改写。
    但逐周期测试（S08-02 cycle1、S08-04 cycle3）在 Busy = TRUE 期间
    仍要求 ActiveRecipe 保持旧值，即新配方应在切换（Busy 窗口）结束后
    才生效；否则同周期内 ActiveRecipe 会早于期望 1 个窗口改写。
    本实现按测试的可判定行为：请求被接受时只锁存 PendingRecipe 并置
    Busy，待 Busy 计时到 2 s 结束时再把 ActiveRecipe := PendingRecipe。
    此冲突保留并报告，未暗中改写需求原文。

  S08-NOTE-3  EStop_NC 在给定 I/O 与规约中没有对应动作要求，未被使用。
  S08-NOTE-4  Status 语义：RecipeSelect 非法时按条款 4 给出 16#8801；
              超规格 16#8802 仅在非忙、有料且 PartHeight >= 右阈值时给出。
*)

(* ---- 上电默认配方：ActiveRecipe 越界（含未初始化的 0）时置 1 ----
   （等价于条款 6：上电 ActiveRecipe = 1；对合法的 1—3 保持不变，
    满足条款 4"非法请求时 ActiveRecipe 保持不变"） *)
IF (ActiveRecipe < 1) OR (ActiveRecipe > 3) THEN
    ActiveRecipe := 1;
END_IF;

(* ---- 切换请求上升沿检测 ---- *)
RisingEdge := ChangeoverReq AND NOT ChangeoverReqLast;
ChangeoverReqLast := ChangeoverReq;

(* ---- 切换状态机（条款 2、4；K2） ---- *)
IF Busy THEN
    (* 保持窗口：100 个扫描周期 = 2 s，结束后新配方生效（见 CONFLICT-5） *)
    BusyTimer := BusyTimer + 1;
    IF BusyTimer >= 100 THEN
        Busy := FALSE;
        BusyTimer := 0;
        ActiveRecipe := PendingRecipe;
    END_IF;
ELSE
    (* 仅在非忙、无料、配方号合法时接受上升沿请求 *)
    IF RisingEdge THEN
        IF (RecipeSelect >= 1) AND (RecipeSelect <= 3) THEN
            IF PartHeight = 0.0 THEN
                PendingRecipe := RecipeSelect;
                Busy := TRUE;
                BusyTimer := 0;
            END_IF;
        END_IF;
    END_IF;
END_IF;

(* ---- 依据当前生效配方确定分拣阈值（条款 1） ---- *)
CASE ActiveRecipe OF
    1:
        LeftThr := 30.0;
        RightThr := 60.0;
    2:
        LeftThr := 50.0;
        RightThr := 90.0;
    3:
        LeftThr := 70.0;
        RightThr := 120.0;
    ELSE
        LeftThr := 30.0;
        RightThr := 60.0;
END_CASE;

(* ---- 分拣（条款 5；K1/C1 切换期禁止分拣，K4/C4 左右互斥） ---- *)
IF Busy THEN
    SortLeft := FALSE;
    SortRight := FALSE;
ELSE
    IF PartHeight > 0.0 THEN
        IF PartHeight < LeftThr THEN
            SortLeft := TRUE;
            SortRight := FALSE;
        ELSIF PartHeight < RightThr THEN
            SortLeft := FALSE;
            SortRight := TRUE;
        ELSE
            SortLeft := FALSE;
            SortRight := FALSE;
        END_IF;
    ELSE
        SortLeft := FALSE;
        SortRight := FALSE;
    END_IF;
END_IF;

(* ---- 状态码：非法配方号优先（条款 4），其次超规格（条款 5） ---- *)
Status := WORD#16#0000;
IF (RecipeSelect < 1) OR (RecipeSelect > 3) THEN
    Status := WORD#16#8801;
ELSIF (NOT Busy) AND (PartHeight > 0.0) AND (PartHeight >= RightThr) THEN
    Status := WORD#16#8802;
END_IF;

END_FUNCTION_BLOCK

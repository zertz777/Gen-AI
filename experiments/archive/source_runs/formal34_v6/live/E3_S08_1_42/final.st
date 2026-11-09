FUNCTION_BLOCK FB_S08
VAR_INPUT
    RecipeSelect : INT;
    ChangeoverReq : BOOL;
    PartHeight : REAL;
    EStop_NC : BOOL;
END_VAR
VAR_OUTPUT
    ActiveRecipe : INT := 1;
    SortLeft : BOOL := FALSE;
    SortRight : BOOL := FALSE;
    Busy : BOOL := FALSE;
    Status : WORD := 16#0000;
END_VAR
VAR
    InitDone : BOOL := FALSE;
    ChangeoverReqLast : BOOL := FALSE;
    reqEdge : BOOL;
    LeftThr : REAL := 30.0;
    RightThr : REAL := 60.0;
    BusyCount : INT := 0;
    IllegalReq : BOOL;
END_VAR

(* 上电首周期初态：默认配方 1，不分拣，不忙 *)
IF NOT InitDone THEN
    ActiveRecipe := 1;
    SortLeft := FALSE;
    SortRight := FALSE;
    Busy := FALSE;
    Status := 16#0000;
    ChangeoverReqLast := ChangeoverReq;
    BusyCount := 0;
    InitDone := TRUE;
ELSE
    reqEdge := ChangeoverReq AND NOT ChangeoverReqLast;
    ChangeoverReqLast := ChangeoverReq;

    (* 安全优先级：急停常闭断开时禁止分拣和切换保持 *)
    IF NOT EStop_NC THEN
        SortLeft := FALSE;
        SortRight := FALSE;
        Busy := FALSE;
        BusyCount := 0;
        Status := 16#0000;
        (* ActiveRecipe 保持不变 *)
    ELSE
        SortLeft := FALSE;
        SortRight := FALSE;

        (* 按当前生效配方加载阈值 *)
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
            LeftThr := 0.0;
            RightThr := 0.0;
        END_CASE;

        Status := 16#0000;
        IllegalReq := FALSE;

        (* RecipeSelect 非法：拒绝切换，仅置错误码 *)
        IF (RecipeSelect < 1) OR (RecipeSelect > 3) THEN
            Status := 16#8801;
            IllegalReq := TRUE;
        END_IF;

        (* 切换请求上升沿；仅无料且非忙时允许切换 *)
        IF reqEdge THEN
            IF (RecipeSelect < 1) OR (RecipeSelect > 3) THEN
                Status := 16#8801;
                IllegalReq := TRUE;
            ELSIF (NOT Busy) AND (PartHeight = 0.0) THEN
                ActiveRecipe := RecipeSelect;
                Busy := TRUE;
                BusyCount := 0;
                Status := 16#0000;
            END_IF;
        END_IF;

        (* 正常分拣；Busy 期间强制禁止分拣 *)
        IF NOT Busy THEN
            IF PartHeight > 0.0 THEN
                IF PartHeight < LeftThr THEN
                    SortLeft := TRUE;
                ELSIF PartHeight < RightThr THEN
                    SortRight := TRUE;
                ELSE
                    IF NOT IllegalReq THEN
                        Status := 16#8802;
                    END_IF;
                END_IF;
            END_IF;
        END_IF;

        (* Busy 保持 2 s = 100 个扫描周期 *)
        IF Busy THEN
            BusyCount := BusyCount + 1;
            IF BusyCount > 100 THEN
                Busy := FALSE;
                BusyCount := 0;
            END_IF;
        END_IF;
    END_IF;
END_IF;
END_FUNCTION_BLOCK

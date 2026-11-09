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
    ChangeoverReqLast : BOOL := FALSE;
    RequestRise : BOOL;
    RecipeValid : BOOL;
    StartupScans : INT := 0;
    BusyScansRemaining : INT := 0;
    LeftThreshold : REAL;
    RightThreshold : REAL;
END_VAR

(*
    待审语义冲突：
    C9 对每一个 Busy 周期都要求后续 100 周期 Busy，因而一旦
    Busy 成立便不能有限时间清除，与原文“2 s 后自动清除”冲突。
    本实现采用原文有限保持：接受请求后经过 100 个 20 ms
    扫描间隔清除 Busy；不声称满足原式 C9。

    C10 的 [0,1] 按包含端点处理：前两个调用保持初态，
    此期间不接受切换，并采样请求历史，避免伪造上升沿。

    右阈值等值点未被原文两个分拣区间或“超过”覆盖：
    本实现严格保留边界，等于右阈值时不动作、不报超规格。

    K4 的“同一产品”未给产品标识或测量稳定性约束；
    本实现保证每周期互斥，不声称能识别跨周期的同一产品。

    急停仅禁止分拣和接受新切换，不改变已生效配方；
    已开始的固定保持计时继续。未新增急停状态码。
    本源码未提供编译或逐周期测试验证证据。
*)

RequestRise := ChangeoverReq AND NOT ChangeoverReqLast;
ChangeoverReqLast := ChangeoverReq;
RecipeValid := (RecipeSelect >= 1) AND (RecipeSelect <= 3);

SortLeft := FALSE;
SortRight := FALSE;
Status := 16#0000;

IF StartupScans < 2 THEN
    ActiveRecipe := 1;
    Busy := FALSE;
    BusyScansRemaining := 0;
    StartupScans := StartupScans + 1;

    IF NOT RecipeValid THEN
        Status := 16#8801;
    END_IF;
ELSE
    (* 先处理已有忙状态；到期扫描不接受重叠请求。 *)
    IF Busy THEN
        IF BusyScansRemaining > 0 THEN
            BusyScansRemaining := BusyScansRemaining - 1;
        END_IF;
        IF BusyScansRemaining = 0 THEN
            Busy := FALSE;
        END_IF;
    ELSE
        IF RequestRise AND RecipeValid AND EStop_NC
           AND (PartHeight = 0.0) THEN
            ActiveRecipe := RecipeSelect;
            Busy := TRUE;
            BusyScansRemaining := 100;
        END_IF;
    END_IF;

    CASE ActiveRecipe OF
        1:
            LeftThreshold := 30.0;
            RightThreshold := 60.0;
        2:
            LeftThreshold := 50.0;
            RightThreshold := 90.0;
        3:
            LeftThreshold := 70.0;
            RightThreshold := 120.0;
    ELSE
        (* 内部防御：无有效配方时禁止动作，不新增状态码。 *)
        LeftThreshold := 0.0;
        RightThreshold := 0.0;
    END_CASE;

    IF NOT RecipeValid THEN
        (* 非法请求优先报告；有效配方和正常分拣仍保留。 *)
        Status := 16#8801;
    END_IF;

    IF EStop_NC AND NOT Busy
       AND (ActiveRecipe >= 1) AND (ActiveRecipe <= 3)
       AND (PartHeight > 0.0) THEN
        IF PartHeight < LeftThreshold THEN
            SortLeft := TRUE;
        ELSIF PartHeight < RightThreshold THEN
            SortRight := TRUE;
        ELSIF PartHeight > RightThreshold THEN
            IF RecipeValid THEN
                Status := 16#8802;
            END_IF;
        END_IF;
    END_IF;
END_IF;

END_FUNCTION_BLOCK

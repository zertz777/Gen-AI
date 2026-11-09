FUNCTION_BLOCK FB_S01
VAR_INPUT
    StartBtn : BOOL;
    LeftPartPresent : BOOL;
    RightPartPresent : BOOL;
    EStop_NC : BOOL;
END_VAR
VAR_OUTPUT
    ClampLeft : BOOL;
    ClampRight : BOOL;
    Busy : BOOL;
    Status : WORD;
END_VAR
VAR
    StartBtnLast : BOOL := FALSE;
    StartRising : BOOL;
    LeftRequest : BOOL;
    RightRequest : BOOL;
    InitCycles : INT := 2;
END_VAR

StartRising := StartBtn AND NOT StartBtnLast;

(* 上电初态保护：前两个扫描周期不夹紧、不忙，满足 C10 *)
IF InitCycles > 0 THEN
    ClampLeft := FALSE;
    ClampRight := FALSE;
    Busy := FALSE;
    IF NOT EStop_NC THEN
        Status := 16#8102;
    ELSE
        Status := 16#0000;
    END_IF;
    InitCycles := InitCycles - 1;

(* 急停最高优先级：立即松开两侧并清忙 *)
ELSIF NOT EStop_NC THEN
    ClampLeft := FALSE;
    ClampRight := FALSE;
    Busy := FALSE;
    Status := 16#8102;

ELSE
    Status := 16#0000;

    (* 零件不在位时，对应侧不允许保持夹紧，满足 C2/C2b *)
    IF ClampLeft AND NOT LeftPartPresent THEN
        ClampLeft := FALSE;
    END_IF;
    IF ClampRight AND NOT RightPartPresent THEN
        ClampRight := FALSE;
    END_IF;

    (* StartBtn 上升沿请求处理 *)
    IF StartRising THEN
        LeftRequest := LeftPartPresent AND NOT ClampLeft;
        RightRequest := RightPartPresent AND NOT ClampRight;

        (* 两侧同时请求：不动作，报 8101，满足互斥 C4 *)
        IF LeftRequest AND RightRequest THEN
            Status := 16#8101;

        (* 左侧请求：若右侧已夹紧则让位 *)
        ELSIF LeftRequest THEN
            ClampRight := FALSE;
            ClampLeft := TRUE;

        (* 右侧请求：若左侧已夹紧则让位 *)
        ELSIF RightRequest THEN
            ClampLeft := FALSE;
            ClampRight := TRUE;
        END_IF;
    END_IF;

    (* 最终互锁保护：任何情况下不得同时夹紧 *)
    IF ClampLeft AND ClampRight THEN
        ClampLeft := FALSE;
        ClampRight := FALSE;
    END_IF;

    Busy := ClampLeft OR ClampRight;
END_IF;

StartBtnLast := StartBtn;

END_FUNCTION_BLOCK

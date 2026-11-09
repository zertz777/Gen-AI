FUNCTION_BLOCK FB_S01
VAR_INPUT
    StartBtn : BOOL;
    LeftPartPresent : BOOL;
    RightPartPresent : BOOL;
    EStop_NC : BOOL;
END_VAR
VAR_OUTPUT
    ClampLeft : BOOL := FALSE;
    ClampRight : BOOL := FALSE;
    Busy : BOOL := FALSE;
    Status : WORD := WORD#16#0000;
END_VAR
VAR
    StartBtnLast : BOOL := FALSE;
    StartRise : BOOL := FALSE;
    StartupScans : USINT := 0;
    PendingSide : USINT := 0; (* 0=无，1=左，2=右 *)
END_VAR

(*
待审语义：
1. C10 的 G[0,1] 要求前两个扫描均不夹紧；原文要求启动上升沿
   触发，未给出上电抑制例外。本实现按 C10 抑制前两个扫描，
   同时更新边沿寄存器，不缓存这两个扫描中的启动请求。
2. “右夹具未在夹紧才启动左侧”与“另一工位动作时自动让位”
   未明确释放与接替时序。本实现采用释放当扫描、接替下一扫描，
   待审期间不声称此时序已由原文唯一确定。
3. 两侧同时请求的处理及 Status 保持方式未明确：
   本实现空闲时拒绝同时请求；已有夹紧侧时允许另一侧排队让位。
   上升沿且两侧均到位时报告 8101，仅保持当扫描。
无真实编译或逐周期测试验证声明。
*)

StartRise := StartBtn AND NOT StartBtnLast;
StartBtnLast := StartBtn;
Status := WORD#16#0000;

IF StartupScans < 2 THEN
    StartupScans := StartupScans + 1;
    ClampLeft := FALSE;
    ClampRight := FALSE;
    Busy := FALSE;
    PendingSide := 0;

    IF NOT EStop_NC THEN
        Status := WORD#16#8102;
    END_IF;

ELSIF NOT EStop_NC THEN
    (* 急停优先；不保留待执行请求，不在急停解除时自动重启。 *)
    ClampLeft := FALSE;
    ClampRight := FALSE;
    Busy := FALSE;
    PendingSide := 0;
    Status := WORD#16#8102;

ELSE
    (* 到位信号消失立即解除对应夹紧。 *)
    IF NOT LeftPartPresent THEN
        ClampLeft := FALSE;
        IF PendingSide = 1 THEN
            PendingSide := 0;
        END_IF;
    END_IF;

    IF NOT RightPartPresent THEN
        ClampRight := FALSE;
        IF PendingSide = 2 THEN
            PendingSide := 0;
        END_IF;
    END_IF;

    IF StartRise AND LeftPartPresent AND RightPartPresent THEN
        Status := WORD#16#8101;
    END_IF;

    IF PendingSide <> 0 THEN
        (* 上一扫描已释放原夹具，本扫描执行一次接替。 *)
        ClampLeft := FALSE;
        ClampRight := FALSE;

        IF (PendingSide = 1) AND LeftPartPresent THEN
            ClampLeft := TRUE;
        ELSIF (PendingSide = 2) AND RightPartPresent THEN
            ClampRight := TRUE;
        END_IF;

        PendingSide := 0;

    ELSIF StartRise THEN
        IF ClampLeft THEN
            IF RightPartPresent THEN
                ClampLeft := FALSE;
                ClampRight := FALSE;
                PendingSide := 2;
            END_IF;

        ELSIF ClampRight THEN
            IF LeftPartPresent THEN
                ClampLeft := FALSE;
                ClampRight := FALSE;
                PendingSide := 1;
            END_IF;

        ELSE
            IF LeftPartPresent AND NOT RightPartPresent THEN
                ClampLeft := TRUE;
                ClampRight := FALSE;
            ELSIF RightPartPresent AND NOT LeftPartPresent THEN
                ClampLeft := FALSE;
                ClampRight := TRUE;
            ELSE
                (* 无零件或同时请求均不从空闲开始夹紧。 *)
                ClampLeft := FALSE;
                ClampRight := FALSE;
            END_IF;
        END_IF;
    END_IF;

    Busy := ClampLeft OR ClampRight OR (PendingSide <> 0);
END_IF;

END_FUNCTION_BLOCK

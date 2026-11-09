FUNCTION_BLOCK FB_S02
VAR_INPUT
    FwdBtn : BOOL;
    RevBtn : BOOL;
    MaintKey : BOOL;
    EStop_NC : BOOL;
END_VAR
VAR_OUTPUT
    MotorFwd : BOOL := FALSE;
    MotorRev : BOOL := FALSE;
    RunLamp : BOOL := FALSE;
    Status : WORD := WORD#16#0000;
END_VAR
VAR
    StartupScans : INT := 0;
    PreviousDirection : INT := 0;
    LastDirection : INT := 0;
    RequestedDirection : INT := 0;
    OffTicks : INT := 0;
    BlinkTicks : INT := 0;
END_VAR

(*
    每次调用为一个20 ms扫描周期。
    方向编码：0=停止，1=正转，2=反转。

    需求待审：
    原文第1条的无条件即时启动，与换向死区及C10启动禁止存在
    字面冲突。本实现保留启动禁止、安全锁定和换向死区优先。
    C10的闭区间[0,1]按前两个扫描周期禁止输出实现；其文字说明
    “上电首周期”与该闭区间范围不完全一致，待审。

    双按钮同时有效的仲裁未指定：运行中保持当前方向，
    停止时正转优先。正常态RunLamp按任一方向运行点亮。
    本源码不表示已通过编译或逐周期功能验证。
*)

(* 保存上一周期方向，用于判断首次断开的扫描时刻。 *)
PreviousDirection := 0;
IF MotorFwd THEN
    PreviousDirection := 1;
ELSIF MotorRev THEN
    PreviousDirection := 2;
END_IF;

(* 断开首周期计为0；随后十个扫描间隔构成200 ms。 *)
IF NOT EStop_NC THEN
    OffTicks := 0;
ELSIF PreviousDirection <> 0 THEN
    OffTicks := 0;
ELSIF OffTicks < 10 THEN
    OffTicks := OffTicks + 1;
END_IF;

(* 双按钮仲裁使用上一扫描输出，避免同周期赋值影响判定。 *)
RequestedDirection := 0;
IF FwdBtn AND RevBtn THEN
    IF PreviousDirection = 2 THEN
        RequestedDirection := 2;
    ELSE
        RequestedDirection := 1;
    END_IF;
ELSIF FwdBtn THEN
    RequestedDirection := 1;
ELSIF RevBtn THEN
    RequestedDirection := 2;
END_IF;

MotorFwd := FALSE;
MotorRev := FALSE;
Status := WORD#16#0000;

(* 急停优先于检修；保留最后运行方向，不以复位绕过换向保护。 *)
IF NOT EStop_NC THEN
    Status := WORD#16#8202;
ELSIF MaintKey THEN
    Status := WORD#16#8201;
ELSIF StartupScans < 2 THEN
    (* C10：初始闭区间[0,1]内禁止两个方向输出。 *)
ELSIF RequestedDirection <> 0 THEN
    IF (LastDirection <> 0)
       AND (RequestedDirection <> LastDirection)
       AND (OffTicks < 10) THEN
        Status := WORD#16#8203;
    ELSE
        IF RequestedDirection = 1 THEN
            MotorFwd := TRUE;
        ELSE
            MotorRev := TRUE;
        END_IF;
        LastDirection := RequestedDirection;
        OffTicks := 0;
    END_IF;
END_IF;

IF StartupScans < 2 THEN
    StartupScans := StartupScans + 1;
END_IF;

(* 检修灯独立于急停状态：亮500 ms、灭500 ms，周期1 s。 *)
IF MaintKey THEN
    RunLamp := BlinkTicks < 25;
    IF BlinkTicks < 49 THEN
        BlinkTicks := BlinkTicks + 1;
    ELSE
        BlinkTicks := 0;
    END_IF;
ELSE
    BlinkTicks := 0;
    RunLamp := MotorFwd OR MotorRev;
END_IF;

END_FUNCTION_BLOCK

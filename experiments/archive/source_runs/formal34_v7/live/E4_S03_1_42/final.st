FUNCTION_BLOCK FB_S03
VAR_INPUT
    DoorSwitch : BOOL;
    ZoneAOccupied : BOOL;
    ZoneBOccupied : BOOL;
    ResetBtn : BOOL;
    EStop_NC : BOOL;
END_VAR
VAR_OUTPUT
    DriveA_Run : BOOL := FALSE;
    DriveB_Run : BOOL := FALSE;
    AlarmLamp : BOOL := FALSE;
    Status : WORD := WORD#16#0000;
END_VAR
VAR
    ResetConfirmed : BOOL := TRUE;
    PreviousResetBtn : BOOL := FALSE;
    PreviousDoorSwitch : BOOL := FALSE;
    ResetRising : BOOL := FALSE;
    DoorRising : BOOL := FALSE;
    BStopPending : BOOL := FALSE;
    BElapsed : TIME := T#0ms;
END_VAR

(*
    待审事项：
    1. 需求提到启动按钮、B区动作完成，但接口没有对应输入。
       ZoneAOccupied、ZoneBOccupied仅表示有人，不能替代上述信号。
       因此不制造自动启动条件，也不制造动作完成条件。
       当前实现保留安全停机、复位和状态逻辑；没有将驱动置TRUE
       的启动路径，两区从指定初态保持停止，待补齐需求后实现启动。

    2. C10要求上电前两个采样点无报警，与上电门开或急停时
       AlarmLamp必须为TRUE存在冲突。本实现安全优先，立即报警，
       不声称满足这些输入条件下的C10。

    3. C1b允许[0,1]扫描内停机，而文字K1要求同周期停机；
       本实现采用更严格的同周期停止。

    4. 未经真实编译器和逐周期测试验证。
*)

ResetRising := ResetBtn AND NOT PreviousResetBtn;
DoorRising := DoorSwitch AND NOT PreviousDoorSwitch;

(* 计时以开门采样点为零点，之后每次调用累计20ms。
   门提前关闭不会取消停机计时；重复开门不延长已有期限。 *)
IF BStopPending THEN
    IF BElapsed < T#500ms THEN
        BElapsed := BElapsed + T#20ms;
    END_IF;

    IF BElapsed >= T#500ms THEN
        BElapsed := T#500ms;
        BStopPending := FALSE;
        DriveB_Run := FALSE;
    END_IF;
END_IF;

IF DoorRising THEN
    IF NOT BStopPending THEN
        BStopPending := TRUE;
        BElapsed := T#0ms;
    END_IF;
END_IF;

(* 急停优先于门开延时和复位。 *)
IF NOT EStop_NC THEN
    DriveA_Run := FALSE;
    DriveB_Run := FALSE;
    ResetConfirmed := FALSE;
    BStopPending := FALSE;
    BElapsed := T#0ms;

ELSIF DoorSwitch THEN
    DriveA_Run := FALSE;
    ResetConfirmed := FALSE;

    (* 仅保持开门前已有的B运行状态，不启动已停止的B。 *)
    IF NOT BStopPending THEN
        DriveB_Run := FALSE;
    END_IF;

ELSE
    (* 门关闭且急停释放时，才接受新的复位上升沿。
       复位只恢复许可，不直接启动驱动。 *)
    IF ResetRising THEN
        ResetConfirmed := TRUE;
    END_IF;

    IF NOT ResetConfirmed THEN
        DriveA_Run := FALSE;
        IF NOT BStopPending THEN
            DriveB_Run := FALSE;
        END_IF;
    END_IF;
END_IF;

(* 报警在门开或急停期间始终保持。 *)
AlarmLamp := DoorSwitch OR NOT EStop_NC;

IF NOT EStop_NC THEN
    Status := WORD#16#8303;
ELSIF DoorSwitch THEN
    Status := WORD#16#8302;
ELSIF NOT ResetConfirmed THEN
    Status := WORD#16#8301;
ELSE
    Status := WORD#16#0000;
END_IF;

PreviousResetBtn := ResetBtn;
PreviousDoorSwitch := DoorSwitch;

END_FUNCTION_BLOCK

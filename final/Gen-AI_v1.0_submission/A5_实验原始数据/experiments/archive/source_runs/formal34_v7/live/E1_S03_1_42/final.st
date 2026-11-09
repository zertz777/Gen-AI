FUNCTION_BLOCK FB_S03
VAR_INPUT
    DoorSwitch : BOOL;
    ZoneAOccupied : BOOL;
    ZoneBOccupied : BOOL;
    ResetBtn : BOOL;
    EStop_NC : BOOL;
END_VAR
VAR_OUTPUT
    DriveA_Run : BOOL;
    DriveB_Run : BOOL;
    AlarmLamp : BOOL;
    Status : WORD;
END_VAR
VAR
    NeedReset     : BOOL := FALSE;
    BStopping     : BOOL := FALSE;
    BStopped      : BOOL := FALSE;
    StopTimer     : INT  := 0;
    ResetBtn_Prev : BOOL := FALSE;
    ResetEdge     : BOOL := FALSE;
END_VAR

(* --- 复位按钮上升沿检测（每扫描周期计算一次） --- *)
ResetEdge := ResetBtn AND NOT ResetBtn_Prev;
ResetBtn_Prev := ResetBtn;

IF NOT EStop_NC THEN
    (* C1 / K4：急停优先，两区同周期立即停，忽略 500 ms 分级延时 *)
    DriveA_Run := FALSE;
    DriveB_Run := FALSE;
    BStopping := FALSE;
    BStopped := FALSE;
    StopTimer := 0;
    NeedReset := TRUE;
    AlarmLamp := TRUE;
    Status := 16#8303;

ELSIF DoorSwitch THEN
    (* C1b / K1：A 区（高等级侧）当周期立即停 *)
    (* C5  / K2：B 区（低等级侧）允许走完当前动作，最多 25 个扫描周期 = 500 ms *)
    DriveA_Run := FALSE;
    NeedReset := TRUE;
    AlarmLamp := TRUE;
    Status := 16#8302;
    IF NOT BStopping THEN
        BStopping := TRUE;
        BStopped := FALSE;
        StopTimer := 0;
    END_IF;
    IF BStopped THEN
        (* 本次门开期间 B 区已停，锁存不再恢复 *)
        DriveB_Run := FALSE;
    ELSIF StopTimer >= 25 THEN
        (* 500 ms 上限到：B 区停 *)
        DriveB_Run := FALSE;
        BStopped := TRUE;
    ELSIF ZoneBOccupied THEN
        (* B 区动作进行中：走完当前动作 *)
        DriveB_Run := TRUE;
        StopTimer := StopTimer + 1;
    ELSE
        (* B 区无进行中的动作：立即停 *)
        DriveB_Run := FALSE;
        BStopped := TRUE;
    END_IF;

ELSE
    (* 门关且急停正常 *)
    BStopping := FALSE;
    BStopped := FALSE;
    StopTimer := 0;
    IF NeedReset THEN
        (* 待复位：未复位的启动请求一律无效，Status 保持 16#8301 *)
        DriveA_Run := FALSE;
        DriveB_Run := FALSE;
        AlarmLamp := TRUE;      (* C6：报警锁存，门关后须待复位才撤销 *)
        Status := 16#8301;
        IF ResetEdge THEN
            NeedReset := FALSE;
            AlarmLamp := FALSE;
            Status := 16#0000;
        END_IF;
    ELSE
        (* C2：门关闭、无急停、已复位 —— 正常运行 *)
        DriveA_Run := TRUE;
        DriveB_Run := TRUE;
        AlarmLamp := FALSE;
        Status := 16#0000;
    END_IF;
END_IF;

END_FUNCTION_BLOCK

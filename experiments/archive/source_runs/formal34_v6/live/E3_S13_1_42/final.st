FUNCTION_BLOCK FB_S13
VAR_INPUT
    LineRun : BOOL;
    PartAtMerge : BOOL;
    PartOnMain : BOOL;
    JamSensor : BOOL;
    ResetBtn : BOOL;
    ModeAuto : BOOL;
END_VAR
VAR_OUTPUT
    MainMotor : BOOL;
    MergeMotor : BOOL;
    SpeedHigh : BOOL;
    JamAlarm : BOOL;
    Status : WORD;
END_VAR
VAR
    LineRunLast : BOOL := FALSE;
    ResetBtnLast : BOOL := FALSE;
    JamTimer : INT := 0;
    HighTimer : INT := 0;
    LowTimer : INT := 0;
    WaitForLineRunCycle : BOOL := FALSE;
    LineRunRising : BOOL;
    ResetRising : BOOL;
    FirstScan : BOOL := TRUE;
END_VAR

(* 冲突说明：
   1) 第1条“LineRun = FALSE -> Status = 16#0000”与第5条“报警锁存到复位并清Status”交叉时，
      本实现按安全/锁存优先：JamAlarm = TRUE 时 Status 保持 16#8C01 直到复位；
      无报警总停时 Status 置 16#0000。
   2) 形式化 C5 写作 JamSensor && LineRun，但 K3/第4条文本写作 JamSensor 连续 2 s 即报警；
      本实现采用文本 K3 的更强安全条件，即 JamSensor 连续 100 扫描周期即报警停机。
*)

IF FirstScan THEN
    MainMotor := FALSE;
    MergeMotor := FALSE;
    SpeedHigh := FALSE;
    JamAlarm := FALSE;
    Status := 16#0000;
    JamTimer := 0;
    HighTimer := 0;
    LowTimer := 0;
    WaitForLineRunCycle := FALSE;
    LineRunRising := FALSE;
    ResetRising := FALSE;
    LineRunLast := LineRun;
    ResetBtnLast := ResetBtn;
ELSE
    LineRunRising := LineRun AND NOT LineRunLast;
    ResetRising := ResetBtn AND NOT ResetBtnLast;
    LineRunLast := LineRun;
    ResetBtnLast := ResetBtn;
END_IF;

(* 堵料检测与报警锁存：连续 2 s = 100 扫描周期 *)
IF NOT FirstScan THEN
    IF JamSensor THEN
        IF JamTimer < 100 THEN
            JamTimer := JamTimer + 1;
        END_IF;
    ELSE
        JamTimer := 0;
    END_IF;

    IF JamTimer >= 100 THEN
        JamAlarm := TRUE;
        Status := 16#8C01;
        MainMotor := FALSE;
        MergeMotor := FALSE;
        SpeedHigh := FALSE;
    END_IF;
ELSE
    JamTimer := 0;
END_IF;

(* 复位：JamSensor = FALSE 且 ResetBtn 上升沿 *)
IF ResetRising AND NOT JamSensor THEN
    JamAlarm := FALSE;
    Status := 16#0000;
    JamTimer := 0;
    WaitForLineRunCycle := TRUE;
END_IF;

(* 总停：LineRun = FALSE 时两电机和高速档立即 FALSE *)
IF NOT LineRun THEN
    MainMotor := FALSE;
    MergeMotor := FALSE;
    SpeedHigh := FALSE;
    IF NOT JamAlarm THEN
        Status := 16#0000;
    END_IF;
    WaitForLineRunCycle := FALSE;
END_IF;

(* 自动启动：LineRun 上升沿且无报警、复位后未等待新上升沿 *)
IF ModeAuto AND LineRunRising AND NOT JamAlarm AND NOT WaitForLineRunCycle THEN
    MainMotor := TRUE;
END_IF;

(* 自动模式下汇流段允许送料：MainMotor = TRUE 且 PartAtMerge = FALSE *)
IF ModeAuto AND MainMotor AND NOT PartAtMerge AND NOT JamAlarm THEN
    MergeMotor := TRUE;
END_IF;

(* 速度档：有料 3 s = 150 周期切高速；无料 5 s = 250 周期回低速；中间保持 *)
IF ModeAuto AND MainMotor AND NOT JamAlarm THEN
    IF PartOnMain THEN
        IF HighTimer < 32767 THEN
            HighTimer := HighTimer + 1;
        END_IF;
        LowTimer := 0;
    ELSE
        HighTimer := 0;
        IF LowTimer < 32767 THEN
            LowTimer := LowTimer + 1;
        END_IF;
    END_IF;

    IF HighTimer >= 150 THEN
        SpeedHigh := TRUE;
    END_IF;

    IF LowTimer >= 250 THEN
        SpeedHigh := FALSE;
    END_IF;
ELSE
    HighTimer := 0;
    LowTimer := 0;
END_IF;

(* 安全强制：防撞互锁、报警停机、总停、主电机停止时禁止汇流段 *)
IF NOT MainMotor OR PartAtMerge OR JamAlarm THEN
    MergeMotor := FALSE;
END_IF;

IF NOT LineRun THEN
    MainMotor := FALSE;
    MergeMotor := FALSE;
    SpeedHigh := FALSE;
END_IF;

IF JamAlarm THEN
    MainMotor := FALSE;
    MergeMotor := FALSE;
    SpeedHigh := FALSE;
END_IF;

IF PartAtMerge THEN
    MergeMotor := FALSE;
END_IF;

FirstScan := FALSE;

END_FUNCTION_BLOCK

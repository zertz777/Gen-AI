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
    MainMotor : BOOL := FALSE;
    MergeMotor : BOOL := FALSE;
    SpeedHigh : BOOL := FALSE;
    JamAlarm : BOOL := FALSE;
    Status : WORD := WORD#16#0000;
END_VAR
VAR
    LineRunLast : BOOL := FALSE;
    ResetBtnLast : BOOL := FALSE;
    LineRunRise : BOOL := FALSE;
    ResetRise : BOOL := FALSE;
    ResetAccepted : BOOL := FALSE;
    JamCount : UINT := UINT#0;
    PresentCount : UINT := UINT#0;
    AbsentCount : UINT := UINT#0;
END_VAR

(*
    20 ms/调用；计数包含当前采样周期，计数器饱和。

    待审语义冲突，未声称形式化规约全部满足：
    1. C5 对单次 JamSensor TRUE 也提出最终报警义务，
       原文/K3 要求连续 TRUE 100 周期；本实现采用连续计数。
    2. C7 对单次有料采样也提出最终高速义务，未考虑随后
       缺料、停机；原文/K5 要求连续有料，本实现采用连续计数。
    3. C10 要求上电首周期输出全停，与初始 LineRunLast=FALSE
       且首扫描 LineRun=TRUE 时按上升沿启动存在冲突。
       本实现初始化输出，但不擅自增加首扫描启动屏蔽。
    4. LineRun=FALSE 要求 Status=0000，与堵料报警期间
       Status=8C01 的要求重叠；总停优先显示 0000，
       JamAlarm 仍锁存，LineRun 恢复后显示 8C01。
    5. C6 的当前周期复位条件与 X(JamAlarm) 的采样关系，
       以及未要求 ResetBtn 上升沿，与原文复位条件不完全一致；
       本实现按原文在有效复位扫描立即清除报警。
    手动点动未提供接口：手动模式保持电机状态，
    仅执行总停、堵料停机、防撞及复位，不制造点动命令。
*)

LineRunRise := LineRun AND NOT LineRunLast;
ResetRise := ResetBtn AND NOT ResetBtnLast;
ResetAccepted := ResetRise AND NOT JamSensor;

(* 堵料检测不因停线或手动模式暂停。 *)
IF JamSensor THEN
    IF JamCount < UINT#100 THEN
        JamCount := JamCount + UINT#1;
    END_IF;
ELSE
    JamCount := UINT#0;
END_IF;

IF ResetAccepted THEN
    JamAlarm := FALSE;
    MainMotor := FALSE;
    MergeMotor := FALSE;
END_IF;

IF JamCount >= UINT#100 THEN
    JamAlarm := TRUE;
END_IF;

(* 总停、报警、复位优先于自动启动。
   同一扫描有效复位与启动上升沿重合时，不允许启动。 *)
IF NOT LineRun THEN
    MainMotor := FALSE;
    MergeMotor := FALSE;
ELSIF JamAlarm THEN
    MainMotor := FALSE;
    MergeMotor := FALSE;
ELSIF ResetAccepted THEN
    MainMotor := FALSE;
    MergeMotor := FALSE;
ELSIF ModeAuto THEN
    IF LineRunRise THEN
        MainMotor := TRUE;
    END_IF;
    MergeMotor := MainMotor AND NOT PartAtMerge;
END_IF;

(* 所有模式均执行防撞和主电机许可联锁。 *)
IF PartAtMerge OR NOT MainMotor THEN
    MergeMotor := FALSE;
END_IF;

(* 连续有料必须同时满足主电机运行。 *)
IF MainMotor AND PartOnMain THEN
    IF PresentCount < UINT#150 THEN
        PresentCount := PresentCount + UINT#1;
    END_IF;
ELSE
    PresentCount := UINT#0;
END_IF;

(* 无料回低速按连续无料计数，不依赖主电机运行。 *)
IF NOT PartOnMain THEN
    IF AbsentCount < UINT#250 THEN
        AbsentCount := AbsentCount + UINT#1;
    END_IF;
ELSE
    AbsentCount := UINT#0;
END_IF;

IF NOT LineRun THEN
    SpeedHigh := FALSE;
    PresentCount := UINT#0;
    AbsentCount := UINT#0;
ELSIF AbsentCount >= UINT#250 THEN
    SpeedHigh := FALSE;
ELSIF PresentCount >= UINT#150 THEN
    SpeedHigh := TRUE;
END_IF;
(* 未达到切档时限时保持原档位。 *)

IF NOT LineRun THEN
    Status := WORD#16#0000;
ELSIF JamAlarm THEN
    Status := WORD#16#8C01;
ELSE
    Status := WORD#16#0000;
END_IF;

(* 所有模式、停机及报警期间均更新边沿记忆。 *)
LineRunLast := LineRun;
ResetBtnLast := ResetBtn;

END_FUNCTION_BLOCK

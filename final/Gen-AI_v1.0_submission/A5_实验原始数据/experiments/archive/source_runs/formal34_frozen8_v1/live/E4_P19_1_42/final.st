FUNCTION_BLOCK FB_P19
VAR_INPUT
    ManualMode : BOOL;
    SingleStepMode : BOOL;
    SingleCycleMode : BOOL;
    ContinuousMode : BOOL;
    EmergencyStop : BOOL;
    Start : BOOL;
    DownButton : BOOL;
    UpButton : BOOL;
    LeftButton : BOOL;
    RightButton : BOOL;
    GripButton : BOOL;
    ReleaseButton : BOOL;
    DownLimitSwitch : BOOL;
    UpLimitSwitch : BOOL;
    LeftLimitSwitch : BOOL;
    RightLimitSwitch : BOOL;
    GripLimitSwitch : BOOL;
    ReleaseLimitSwitch : BOOL;
END_VAR
VAR_OUTPUT
    MoveDown : BOOL := FALSE;
    MoveUp : BOOL := FALSE;
    MoveLeft : BOOL := FALSE;
    MoveRight : BOOL := FALSE;
    ActivateGrip : BOOL := FALSE;
    ActivateRelease : BOOL := FALSE;
END_VAR
VAR
    Initialized : BOOL := FALSE;
    PreviousStart : BOOL := FALSE;
    StartEdge : BOOL := FALSE;
    Mode : INT := 0;
    PreviousMode : INT := 0;
    ModeCount : INT := 0;
    Step : INT := 1;
    Active : BOOL := FALSE;
    Completed : BOOL := FALSE;
END_VAR

(*
    每次调用为20 ms扫描；不使用定时完成判据。
    步骤：1下、2抓、3上、4右、5下、6放、7上、8左。

    规约冲突报告（待审，未声称满足全部形式化条款）：
    1. C6无条件保持抓取，与手动松开即停、C1急停当拍停止、
       K5到位停以及模式切换停止存在冲突。
       本实现急停优先，手动按钮松开停止；自动抓取保持至反馈，
       但急停或模式退出会取消。
    2. 同时按下上下按钮且均未到位时，C2要求MoveDown，
       手动逐动作要求也会要求MoveUp，而C4禁止同时输出。
       本实现同轴相反按钮同时按下时两路均禁止，安全互锁优先。
    3. 首拍若满足C2前提，C2与C10首拍全停冲突。
       本实现首拍全停，首拍Start不作为自动启动请求。

    模式改变取消自动进度。非法模式组合禁止全部动作。
    急停清除进度并封锁已保持的Start；
    恢复后必须先采样到Start=FALSE，再出现上升沿。
    未经真实编译器或逐周期测试验证。
*)

MoveDown := FALSE;
MoveUp := FALSE;
MoveLeft := FALSE;
MoveRight := FALSE;
ActivateGrip := FALSE;
ActivateRelease := FALSE;
Completed := FALSE;

ModeCount := 0;
Mode := 0;
IF ManualMode THEN
    ModeCount := ModeCount + 1;
    Mode := 1;
END_IF;
IF SingleStepMode THEN
    ModeCount := ModeCount + 1;
    Mode := 2;
END_IF;
IF SingleCycleMode THEN
    ModeCount := ModeCount + 1;
    Mode := 3;
END_IF;
IF ContinuousMode THEN
    ModeCount := ModeCount + 1;
    Mode := 4;
END_IF;
IF ModeCount <> 1 THEN
    Mode := 0;
END_IF;

StartEdge := Start AND NOT PreviousStart;

IF NOT Initialized THEN
    Initialized := TRUE;
    Step := 1;
    Active := FALSE;
    PreviousMode := Mode;
    PreviousStart := Start;
    IF NOT EmergencyStop THEN
        PreviousStart := TRUE;
    END_IF;

ELSIF NOT EmergencyStop THEN
    Step := 1;
    Active := FALSE;
    PreviousMode := Mode;
    PreviousStart := TRUE;

ELSE
    PreviousStart := Start;

    IF Mode <> PreviousMode THEN
        Active := FALSE;
        Step := 1;
    END_IF;
    PreviousMode := Mode;

    IF Mode = 0 THEN
        Active := FALSE;
        Step := 1;
        (* 恢复有效模式后，不接受一直保持的Start。 *)
        PreviousStart := TRUE;

    ELSIF Mode = 1 THEN
        Active := FALSE;
        Step := 1;

        MoveDown := DownButton AND NOT UpButton
                    AND NOT DownLimitSwitch;
        MoveUp := UpButton AND NOT DownButton
                  AND NOT UpLimitSwitch;
        MoveLeft := LeftButton AND NOT RightButton
                    AND NOT LeftLimitSwitch;
        MoveRight := RightButton AND NOT LeftButton
                     AND NOT RightLimitSwitch;
        ActivateGrip := GripButton AND NOT ReleaseButton
                        AND NOT GripLimitSwitch;
        ActivateRelease := ReleaseButton AND NOT GripButton
                           AND NOT ReleaseLimitSwitch;

    ELSE
        IF NOT Active AND StartEdge THEN
            Active := TRUE;
        END_IF;

        IF Active THEN
            CASE Step OF
                1:
                    MoveDown := NOT DownLimitSwitch;
                    Completed := DownLimitSwitch;
                2:
                    ActivateGrip := NOT GripLimitSwitch;
                    Completed := GripLimitSwitch;
                3:
                    MoveUp := NOT UpLimitSwitch;
                    Completed := UpLimitSwitch;
                4:
                    MoveRight := NOT RightLimitSwitch;
                    Completed := RightLimitSwitch;
                5:
                    MoveDown := NOT DownLimitSwitch;
                    Completed := DownLimitSwitch;
                6:
                    ActivateRelease := NOT ReleaseLimitSwitch;
                    Completed := ReleaseLimitSwitch;
                7:
                    MoveUp := NOT UpLimitSwitch;
                    Completed := UpLimitSwitch;
                8:
                    MoveLeft := NOT LeftLimitSwitch;
                    Completed := LeftLimitSwitch;
            ELSE
                (* 内部步骤异常：停止并回到首步，须重新启动。 *)
                Active := FALSE;
                Step := 1;
            END_CASE;

            IF Completed THEN
                IF Step = 8 THEN
                    Step := 1;
                    (* 连续模式下一拍开始下一周期。 *)
                    IF Mode <> 4 THEN
                        Active := FALSE;
                    END_IF;
                ELSE
                    Step := Step + 1;
                    (* 单步完成后只接受后续扫描的新Start边沿。 *)
                    IF Mode = 2 THEN
                        Active := FALSE;
                    END_IF;
                END_IF;
            END_IF;
        END_IF;
    END_IF;
END_IF;

END_FUNCTION_BLOCK

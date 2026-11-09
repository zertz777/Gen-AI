FUNCTION_BLOCK FB_S07
VAR_INPUT
    BottleIn : BOOL;
    FillDone : BOOL;
    CapDone : BOOL;
    PackDone : BOOL;
    StartBtn : BOOL;
    EStop_NC : BOOL;
END_VAR
VAR_OUTPUT
    Conveyor : BOOL;
    FillValve : BOOL;
    CapMotor : BOOL;
    PackCyl : BOOL;
    CycleCount : UINT;
    Status : WORD;
END_VAR
(* 内部状态/计时器；初态对应 initial_state *)
VAR
    Step : INT := 0;              (* 当前工步 0..3 *)
    Run : BOOL := FALSE;          (* 整线运行标志 *)
    StepTimer : UINT := 0;        (* 当前步已运行扫描周期数 *)
    FillHold : UINT := 0;         (* 灌装阀已保持周期数（防抖） *)
    StartBtnLast : BOOL := FALSE; (* 启动按钮上一扫描值（边沿检测） *)
    StartRising : BOOL := FALSE;
    Advance : BOOL := FALSE;
    JustStarted : BOOL := FALSE;  (* 启动当周期不推进，避免同周期跳步 *)
END_VAR
VAR CONSTANT
    T_STEP_TIMEOUT : UINT := 250; (* 5 s / 20 ms 单步超时 *)
    FILL_MIN_HOLD : UINT := 5;    (* 100 ms / 20 ms 灌装最小保持 *)
    ST_OK : WORD := 16#0000;
    ST_TIMEOUT : WORD := 16#8701;
    ST_ESTOP : WORD := 16#8702;
END_VAR

(* 默认输出全停（初态 / 非运行态 / C10 首周期无动作） *)
Conveyor := FALSE;
FillValve := FALSE;
CapMotor := FALSE;
PackCyl := FALSE;

(* 启动按钮上升沿检测（EStop 期间也跟踪，避免误触发） *)
StartRising := StartBtn AND NOT StartBtnLast;
StartBtnLast := StartBtn;

(* K5 / C1：急停优先，立即全停并回到 Step 0，本扫描立即返回 *)
IF NOT EStop_NC THEN
    Run := FALSE;
    Step := 0;
    StepTimer := 0;
    FillHold := 0;
    Status := ST_ESTOP;
    RETURN;
END_IF;

(* 启动：上升沿且当前未运行（含超时停机后的重新启动） *)
JustStarted := FALSE;
IF StartRising AND NOT Run THEN
    Run := TRUE;
    Step := 0;
    StepTimer := 0;
    FillHold := 0;
    Status := ST_OK;
    JustStarted := TRUE;
END_IF;

IF Run THEN
    (* 工步输出：同一时刻仅一路动作（K4 / C4） *)
    CASE Step OF
        0: (* 进瓶工位 *)
            Conveyor := TRUE;
        1: (* 灌装：开阀前提瓶到位（C2） *)
            IF BottleIn THEN
                FillValve := TRUE;
            END_IF;
        2: (* 封盖 *)
            CapMotor := TRUE;
        3: (* 包装 *)
            PackCyl := TRUE;
    END_CASE;

    (* 启动当周期只给输出、不推进计时，保证初态稳定 *)
    IF NOT JustStarted THEN
        (* 灌装最小保持计数（C9：≥100 ms 防抖） *)
        IF (Step = 1) AND FillValve THEN
            IF FillHold < 65535 THEN
                FillHold := FillHold + 1;
            END_IF;
        ELSE
            FillHold := 0;
        END_IF;

        (* 完成判定（K2） *)
        Advance := FALSE;
        CASE Step OF
            0: Advance := BottleIn;
            1: Advance := FillDone AND (FillHold >= FILL_MIN_HOLD);
            2: Advance := CapDone;
            3: Advance := PackDone;
        END_CASE;

        IF Advance THEN
            (* 顺序推进 0→1→2→3→0（K1）；PackDone 回到 0 时计一瓶 *)
            CASE Step OF
                0: Step := 1;
                1: Step := 2;
                2: Step := 3;
                3: Step := 0;
                   CycleCount := CycleCount + 1;
            END_CASE;
            StepTimer := 0;
            FillHold := 0;
        ELSE
            (* 单步计时与超时（K3） *)
            IF StepTimer < 65535 THEN
                StepTimer := StepTimer + 1;
            END_IF;
            IF StepTimer >= T_STEP_TIMEOUT THEN
                Status := ST_TIMEOUT;
                Conveyor := FALSE;
                FillValve := FALSE;
                CapMotor := FALSE;
                PackCyl := FALSE;
                Run := FALSE;          (* 停机，等待人工处理；Step 保持不变 *)
                StepTimer := 0;
                FillHold := 0;
            END_IF;
        END_IF;
    END_IF;
END_IF;

END_FUNCTION_BLOCK

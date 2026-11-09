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
    Conveyor : BOOL := FALSE;
    FillValve : BOOL := FALSE;
    CapMotor : BOOL := FALSE;
    PackCyl : BOOL := FALSE;
    CycleCount : UINT := UINT#0;
    Status : WORD := WORD#16#0000;
END_VAR
VAR
    Step : USINT := USINT#0;
    StepElapsedMs : UINT := UINT#0;
    StartBtnLast : BOOL := FALSE;
    StartRise : BOOL := FALSE;
    Running : BOOL := FALSE;
    TimeoutLatched : BOOL := FALSE;
    DoneNow : BOOL := FALSE;
END_VAR

(*
需求原文：
灌装线由进瓶、灌装、封盖、包装四个工位组成，按固定节拍顺序推进。
1. StartBtn 上升沿启动整线，Conveyor = TRUE 进入进瓶工位；
   EStop_NC = FALSE 时立即停止全部输出并回到 Step 0。
2. 工步顺序：0 进瓶（等 BottleIn）→ 1 灌装（FillValve 开，等 FillDone）
   → 2 封盖（CapMotor 开，等 CapDone）→ 3 包装（PackCyl 开，等 PackDone）
   → 回到 0。
3. 每一步自进入起计时，超过 5 s 未收到完成信号则置 Status = 16#8701、
   保持当前步不动、关闭该步输出（等待人工处理）。
4. 每完成一瓶（PackDone 且回到 Step 0）CycleCount 加 1。
5. 同一时刻四个执行器输出中最多一个为 TRUE。
6. Status：16#0000 正常、16#8701 工步超时、16#8702 急停。
扫描周期：20 ms。

待审语义冲突，不声明全部形式化规约已满足：
- C6 无急停、超时例外；在 FillDone 未出现时，要求保持 FillValve，
  与 C1/K5 急停关闭和 K3 超时关闭冲突。
- 若灌装中 BottleIn 消失，C2 要求关闭 FillValve，
  而 C6 在 FillDone 未出现时要求保持，二者冲突。
- C9 按字面要求每个 FillValve 为 TRUE 的周期，其后 0..5 周期
  均为 TRUE。重复施加会使灌装阀一旦打开便不能关闭，
  并非仅要求进入灌装后保持 100 ms；与正常推进、急停及超时冲突。
- C10 的 [0,1] 要求前两个周期无动作，与首周期 StartBtn 上升沿
  立即启动的要求冲突。

本实现采用需求原文的工步推进、严格超过 5 s 超时、
急停最高优先级以及 C2 当前瓶位联锁。
不将 C9 暗中改写为一次性的最小保持时间，也不新增启动延迟。
超时锁存，不用 StartBtn 擅自清除；急停复位后必须重新出现启动沿。
无独立人工复位接口，其进一步处理方式仍待明确。
UINT 计数达到 65535 时采用饱和，避免回绕；超范围计数策略待审。
本源码未声称经过真实编译或逐周期功能验证。
*)

(* 每次调用均采样启动沿；急停期间的启动沿不会在释放后重放。 *)
StartRise := StartBtn AND NOT StartBtnLast;
StartBtnLast := StartBtn;

(* 每周期先关闭全部执行器，再根据唯一工步统一赋值。 *)
Conveyor := FALSE;
FillValve := FALSE;
CapMotor := FALSE;
PackCyl := FALSE;

(* 急停当周期复位工步、运行状态及计时，保留累计瓶数。 *)
IF NOT EStop_NC THEN
    Step := USINT#0;
    StepElapsedMs := UINT#0;
    Running := FALSE;
    TimeoutLatched := FALSE;
    DoneNow := FALSE;
    Status := WORD#16#8702;
    RETURN;
END_IF;

IF TimeoutLatched THEN
    Status := WORD#16#8701;
ELSE
    Status := WORD#16#0000;

    IF NOT Running THEN
        IF StartRise THEN
            Running := TRUE;
            Step := USINT#0;
            StepElapsedMs := UINT#0;
            (* 启动周期只进入进瓶；不在同周期继续跳步。 *)
        END_IF;
    ELSE
        (* 进入工步的周期计时为零，之后每周期累计 20 ms。 *)
        IF StepElapsedMs < UINT#5020 THEN
            StepElapsedMs := StepElapsedMs + UINT#20;
        END_IF;

        DoneNow := FALSE;
        CASE Step OF
            USINT#0:
                DoneNow := BottleIn;
            USINT#1:
                DoneNow := FillDone;
            USINT#2:
                DoneNow := CapDone;
            USINT#3:
                DoneNow := PackDone;
        END_CASE;

        (* 同周期已收到完成信号时，不满足“未收到”的超时条件。 *)
        IF DoneNow THEN
            CASE Step OF
                USINT#0:
                    Step := USINT#1;
                USINT#1:
                    Step := USINT#2;
                USINT#2:
                    Step := USINT#3;
                USINT#3:
                    Step := USINT#0;
                    IF CycleCount < UINT#65535 THEN
                        CycleCount := CycleCount + UINT#1;
                    END_IF;
            END_CASE;
            StepElapsedMs := UINT#0;
        ELSIF StepElapsedMs > UINT#5000 THEN
            TimeoutLatched := TRUE;
            Status := WORD#16#8701;
            (* 不修改 Step；锁存后禁止完成信号推动工步。 *)
        END_IF;
    END_IF;
END_IF;

IF Running AND NOT TimeoutLatched THEN
    CASE Step OF
        USINT#0:
            Conveyor := TRUE;
        USINT#1:
            (* C2：当前瓶位丢失时禁止灌装，工步计时仍继续。 *)
            FillValve := BottleIn;
        USINT#2:
            CapMotor := TRUE;
        USINT#3:
            PackCyl := TRUE;
    END_CASE;
END_IF;

END_FUNCTION_BLOCK

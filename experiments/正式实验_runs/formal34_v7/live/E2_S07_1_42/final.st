(*
修改说明：
1. 删除上电两次调用的动作屏蔽及暂存启动逻辑，
   StartBtn 上升沿当周期开启 Conveyor，修复已报告的周期 1 失败。
2. 将内部 Step 变量改名为 CurrentStep，避免与 IEC 61131-3
   的 SFC 保留字 STEP 冲突；外部接口不变。
   原先内部声明解析失败可能导致后续赋值和 CASE 的级联报错。
3. 保留固定 20 ms 扫描计时、急停复位、超时锁定、
   输出互斥和完成瓶数计数。

验证说明：
用户提供的旧版结果为 authoritative 编译通过、fast 编译失败，
逐周期测试 6 项中仅 1 项通过；其余均首先失败于周期 1 的 Conveyor。
本次修改未在当前对话中运行编译器或测试命令，
不声称新版已编译通过或功能验证通过。
需要使用相同 judge 命令重新运行，检查后续周期及计时边界。

需求原文：
灌装线由进瓶、灌装、封盖、包装四个工位组成，按固定节拍顺序推进。

控制要求：
1. StartBtn 上升沿启动整线，Conveyor = TRUE 进入进瓶工位；EStop_NC = FALSE 时立即停止全部输出并回到 Step 0。
2. 工步顺序：0 进瓶（等 BottleIn）→ 1 灌装（FillValve 开，等 FillDone）→ 2 封盖（CapMotor 开，等 CapDone）→ 3 包装（PackCyl 开，等 PackDone）→ 回到 0。
3. 每一步自进入起计时，超过 5 s 未收到完成信号则置 Status = 16#8701、保持当前步不动、关闭该步输出（等待人工处理）。
4. 每完成一瓶（PackDone 且回到 Step 0）CycleCount 加 1。
5. 同一时刻四个执行器输出中最多一个为 TRUE。
6. Status：16#0000 正常、16#8701 工步超时、16#8702 急停。

扫描周期：20 ms（全组统一，见 docs/tasks_note.md）

接口、初态、约束与数据告警：
task_id: S07
title: 灌装四工位节拍控制
接口声明见下方 VAR_INPUT 和 VAR_OUTPUT，名称、方向、类型保持不变。
initial_state:
四个执行器输出全 FALSE；CycleCount = 0；Step = 0；
Status = 16#0000；步计时器 = 0；StartBtnLast = FALSE。
内部 CurrentStep 对应需求中的 Step。
K1 工步只能按 0→1→2→3→0 推进，不得跳步或回退（除急停复位）。
K2 每一步必须在收到对应完成信号后才推进到下一步。
K3 单步超过 5 s 未完成时置 16#8701、关闭该步输出、保持步号不变。
K4 Conveyor/FillValve/CapMotor/PackCyl 同一时刻最多一个为 TRUE。
K5 EStop_NC = FALSE 时全部输出 FALSE、Step 归 0、立即返回。
semantic_warnings: []
warnings: []
missing_fields: []
dialect_requirements: []
type_origins: {}

完整形式化规约；有界时序以扫描周期计：
# task: S07
# meta: hard / C 状态机与节拍
# spec: version 1.0, updated 2026-10-30, scan cycle 20 ms
# 条款号对齐任务书 3.4 的条款库 C1—C10；[a,b] 单位为扫描周期。

C1: G(!EStop_NC -> (!Conveyor && !FillValve && !CapMotor && !PackCyl))
    -- 急停当周期四路执行器全停（K5）
C2: G(FillValve -> BottleIn)
    -- 开灌装阀的前提是瓶子到位（K2）
C4: G(!(Conveyor && FillValve) && !(Conveyor && CapMotor) &&
    !(Conveyor && PackCyl) && !(FillValve && CapMotor) &&
    !(FillValve && PackCyl) && !(CapMotor && PackCyl))
    -- 四路执行器两两互斥（单工步动作）（K4）
C6: G(FillValve -> (FillValve W FillDone))
    -- 灌装阀保持到灌装完成信号出现（K2）
C9: G(FillValve -> G[0,5](FillValve))
    -- 灌装动作至少保持 100 ms（防抖，避免单周期抖动误判完成）（K3）
C10: G[0,1](!Conveyor && !FillValve && !CapMotor && !PackCyl)
    -- 上电首周期无动作（初态）

语义冲突报告：
1. C9 对每个 FillValve 为 TRUE 的周期重复施加未来保持条件。
   按给定闭区间公式，一旦开阀便不能在有限周期内关阀，
   不等价于仅在进入灌装时保持 100 ms。
   该公式与完成后推进、超时关阀以及急停关阀存在冲突。
2. 未出现 FillDone 时，C6 要求持续开阀；
   与急停或超时强制关阀存在冲突。
3. 灌装期间 BottleIn 若变 FALSE，C2 要求立即关阀，
   而未出现 FillDone 时 C6 要求保持开阀，两者冲突。
4. C10 的闭区间 [0,1] 要求最初两次调用均无执行器动作；
   与这两次调用中启动沿立即开启 Conveyor 的要求存在冲突。
   已报告测试要求周期 1 的 Conveyor 为 TRUE。
   本次选择启动沿立即动作，保留 C10 原文并报告此冲突，
   不宣称满足 C10。

本实现的明确取舍：
急停优先于一切；超时优先于保持输出；BottleIn 实时联锁灌装阀。
初态执行器全 FALSE；正常输入下启动沿当周期进入进瓶并开启 Conveyor。
启动周期不同时处理 BottleIn，保证先进入进瓶工步。
完成信号按当前工步电平采样，每次调用最多推进一个工步。
不宣称满足冲突的 C6、C9 全局公式。
当前工步的进入周期计时为 0，此后每次调用累加 20 ms；
250 次为 5 s，251 次为超过 5 s。
同周期收到完成信号时优先完成；无完成信号才锁定超时。
超时锁定后不再接收完成信号或启动沿；
使用已有急停输入复位，释放急停后必须重新出现启动沿。
未启动期间不计步超时。急停保留 CycleCount。
UINT 计数到 65535 后，下一瓶回绕为 0。
*)

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
    CycleCount : UINT := 0;
    Status : WORD := WORD#16#0000;
END_VAR
VAR
    CurrentStep : USINT := 0;
    StepTicks : UINT := 0;
    StartBtnLast : BOOL := FALSE;
    StartRise : BOOL := FALSE;
    Running : BOOL := FALSE;
    TimeoutLatched : BOOL := FALSE;
    StepDone : BOOL := FALSE;
END_VAR

(* 默认关闭全部执行器，最后按当前工步唯一赋值。 *)
Conveyor := FALSE;
FillValve := FALSE;
CapMotor := FALSE;
PackCyl := FALSE;

(* 包括急停期间在内，每次调用都更新按钮历史。 *)
StartRise := StartBtn AND NOT StartBtnLast;
StartBtnLast := StartBtn;

(* 急停具有最高优先级，当周期复位并立即返回。 *)
IF NOT EStop_NC THEN
    Running := FALSE;
    TimeoutLatched := FALSE;
    CurrentStep := 0;
    StepTicks := 0;
    StepDone := FALSE;
    Status := WORD#16#8702;
    RETURN;
END_IF;

(* 超时后保持步号及计时值，关闭输出，等待急停复位。 *)
IF TimeoutLatched THEN
    Status := WORD#16#8701;
    RETURN;
END_IF;

Status := WORD#16#0000;

IF NOT Running THEN
    IF StartRise THEN
        Running := TRUE;
        CurrentStep := 0;
        StepTicks := 0;
        StepDone := FALSE;
    ELSE
        RETURN;
    END_IF;
ELSE
    (* 前一次调用进入工步，本次调用经过一个 20 ms 周期。 *)
    IF StepTicks < 251 THEN
        StepTicks := StepTicks + 1;
    END_IF;

    StepDone := FALSE;
    CASE CurrentStep OF
        0:
            StepDone := BottleIn;
        1:
            StepDone := FillDone;
        2:
            StepDone := CapDone;
        3:
            StepDone := PackDone;
    END_CASE;

    IF StepDone THEN
        CASE CurrentStep OF
            0:
                CurrentStep := 1;
            1:
                CurrentStep := 2;
            2:
                CurrentStep := 3;
            3:
                CurrentStep := 0;
                IF CycleCount = UINT#65535 THEN
                    CycleCount := 0;
                ELSE
                    CycleCount := CycleCount + 1;
                END_IF;
        END_CASE;
        StepTicks := 0;
    ELSIF StepTicks > 250 THEN
        TimeoutLatched := TRUE;
        Status := WORD#16#8701;
        RETURN;
    END_IF;
END_IF;

(* 仅当前工步对应输出允许开启；灌装附加实时瓶到位联锁。 *)
CASE CurrentStep OF
    0:
        Conveyor := TRUE;
    1:
        FillValve := BottleIn;
    2:
        CapMotor := TRUE;
    3:
        PackCyl := TRUE;
END_CASE;

END_FUNCTION_BLOCK

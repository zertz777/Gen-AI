(*
修改说明：
实现按钮上升沿切换、自动配料、急停优先停机、安全重启及
配料阀与出料阀互锁；保持外部接口不变。
内部步序变量使用 autoState，避免使用 ST/SFC 关键字 STEP。
输出声明初始为 FALSE；首次调用直接响应当前模式的启动边沿，
不再强制屏蔽首次扫描，也不将首次模式选择视为运行中模式切换。

需求原文：
Design a PLC program to control a material proportioning process that requires mixing three types of materials according to specific requirements and then delivering them to the next process through valve D. The system needs to support both manual and automatic operation modes and be able to safely stop all equipment when an emergency stop signal is triggered.
Control requirements:
Emergency Stop Logic: The estop(=FALSE) signal is used for emergency stopping of all equipment.
Manual Mode: opeMode=false, manually control the start/stop of valves A, B, C, D, and the mixing motor.
Automatic Mode: opeMode=true, equipment operates automatically according to the process flow.
Implement the emergency stop logic to ensure that all equipment stops immediately when the emergency stop signal is triggered.
In manual mode, manually control the start/stop of valves and the mixing motor.
For example, pressing the valve A start button valveAStart (triggering a rising edge) causes valve A to run (valveARun=TRUE); pressing the valve A start button valveAStart again (triggering a rising edge) stops valve A (valveARun=FALSE).
In automatic mode, implement the following control logic based on the process flow:
Press the autoStart button to start the automatic process, first opening valve A.
When the liquid level sensor levelSensor reaches 50cm, close valve A and open valve B.
When the liquid level sensor reaches 80cm, close valve B.
Based on processMode:
If processMode=false, start the mixing motor; after receiving the mixing complete signal, stop the mixing motor, open valve D, and the automatic process ends.
If processMode=true, open valve C; when the liquid level sensor reaches 100cm, close valve C, start the mixing motor; after receiving the mixing complete signal, stop the mixing motor, open valve D, and the automatic process ends.

中文摘要：物料配比控制：手动模式按按钮边沿切换各阀门与搅拌电机，
自动模式按工艺顺序配料，急停时立即停全部设备。
扫描周期：每次调用 20 ms。

初态与约束：
输出初始均为 FALSE；estop 正常态为 TRUE。
给定初态文字为：模式由 opeMode 决定，上电按手动处理。
本实现内部模式历史初始为手动，首次调用采纳当前 opeMode。
K1：estop=FALSE 时当周期停止全部设备，优先级最高。
K2：手动按钮按上升沿切换，不按持续电平翻转。
K3：自动按 A、B、可选 C、搅拌、D 的顺序执行。
K4：急停期间冻结自动步序；恢复时复位安全待机，不续跑。

完整形式化规约：
C1: G(!estop -> (!valveARun && !valveBRun && !valveCRun && !valveDRun && !mixMotorRun))
C2: G(mixMotorRun -> !estop)
C4: G(!(valveDRun && (valveARun || valveBRun || valveCRun)))
C6: G(mixMotorRun -> (mixMotorRun W mixMotorComplete))
C10: G[0,1](!valveARun && !valveBRun && !valveCRun && !valveDRun && !mixMotorRun)

语义冲突报告：
1. C2 的公式要求电机仅在急停触发时运行，与其“无急停”文字及
   C1、正常自动搅拌需求矛盾。本实现遵循 C1 和正常运行需求，
   不满足 C2 原公式；保留原公式，不声称规约全部满足。
2. C6 无模式、急停例外，与手动再次按键停机及急停强制停机冲突。
   本实现仅在未急停且未切换模式的自动搅拌步骤保持到完成信号。
3. C4 与手动各阀门完全独立切换可能冲突。本实现优先互锁：
   开 A/B/C 时关闭 D；开 D 时关闭 A/B/C；同扫描竞争时 D 优先。
4. C10 若严格按扫描编号 0、1 解释，要求前两次调用输出均关闭。
   提供的逐周期测试在 cycle=1 要求 valveARun=TRUE，但没有给出
   完整输入轨迹或编号定义，不能确定其与 C10 的精确对应关系。
   本次保留声明初态全关闭，取消首次调用的强制停机，
   允许首次扫描响应启动边沿，不声称满足 C10 严格区间公式。
5. “上电按手动处理”与首次即按 opeMode 自动启动存在解释差异。
   本实现将其解释为内部安全初态，不强制增加手动运行扫描。

边界实现：
首次调用使用当前 opeMode，不触发运行中模式切换保护。
首次调用按钮为 TRUE 时，相对于初始 FALSE 识别为上升沿。
后续模式切换当周期停机并复位自动流程，不接受该周期启动边沿。
急停期间仅冻结步号，输出立即关闭，持续更新按钮历史；
恢复当周期复位步号并关闭输出，需要之后新的启动上升沿。
液位采用 >= 阈值；每扫描最多推进一个自动步骤。
在 B 达标时读取 processMode；完成信号按电平判断。
D 在自动完成后保持开启，直至新一轮启动、模式切换或急停。
运行中 autoStart 边沿被忽略；完成态的新启动关闭 D 并开启 A。

验证状态：
用户提供的上一版结果为 fast 和 authoritative 编译均通过，
逐周期测试 0/7 通过，失败均报告 cycle=1 的 A 阀输出。
本次取消首次扫描强制停机及首次模式选择的停机屏蔽。
当前对话无可执行工具，未运行本地命令，未验证修改后的结果。
源码使用标准 BOOL、INT、VAR、IF 和 CASE，无厂商扩展。
编译通过不代表功能正确，仍需实际逐周期测试。
*)

FUNCTION_BLOCK FB_P15
VAR_INPUT
    estop : BOOL;
    opeMode : BOOL;
    valveAStart : BOOL;
    valveBStart : BOOL;
    valveCStart : BOOL;
    valveDStart : BOOL;
    mixMotorStart : BOOL;
    autoStart : BOOL;
    processMode : BOOL;
    levelSensor : INT;
    mixMotorComplete : BOOL;
END_VAR
VAR_OUTPUT
    valveARun : BOOL := FALSE;
    valveBRun : BOOL := FALSE;
    valveCRun : BOOL := FALSE;
    valveDRun : BOOL := FALSE;
    mixMotorRun : BOOL := FALSE;
END_VAR
VAR
    initialized : BOOL := FALSE;
    autoState : INT := 0;
    previousMode : BOOL := FALSE;
    emergencySeen : BOOL := FALSE;

    previousAStart : BOOL := FALSE;
    previousBStart : BOOL := FALSE;
    previousCStart : BOOL := FALSE;
    previousDStart : BOOL := FALSE;
    previousMotorStart : BOOL := FALSE;
    previousAutoStart : BOOL := FALSE;

    edgeA : BOOL := FALSE;
    edgeB : BOOL := FALSE;
    edgeC : BOOL := FALSE;
    edgeD : BOOL := FALSE;
    edgeMotor : BOOL := FALSE;
    edgeAuto : BOOL := FALSE;

    forceSafe : BOOL := FALSE;
END_VAR

edgeA := valveAStart AND NOT previousAStart;
edgeB := valveBStart AND NOT previousBStart;
edgeC := valveCStart AND NOT previousCStart;
edgeD := valveDStart AND NOT previousDStart;
edgeMotor := mixMotorStart AND NOT previousMotorStart;
edgeAuto := autoStart AND NOT previousAutoStart;

forceSafe := FALSE;

(* 首次采纳当前模式，不屏蔽首次启动边沿。 *)
IF NOT initialized THEN
    initialized := TRUE;
    previousMode := opeMode;
    autoState := 0;
END_IF;

(* 急停优先；运行中急停不改变自动步号。 *)
IF NOT estop THEN
    emergencySeen := TRUE;
    forceSafe := TRUE;
ELSIF emergencySeen THEN
    emergencySeen := FALSE;
    autoState := 0;
    forceSafe := TRUE;
ELSIF opeMode <> previousMode THEN
    autoState := 0;
    forceSafe := TRUE;
END_IF;

IF forceSafe THEN
    valveARun := FALSE;
    valveBRun := FALSE;
    valveCRun := FALSE;
    valveDRun := FALSE;
    mixMotorRun := FALSE;

ELSIF NOT opeMode THEN
    autoState := 0;

    IF edgeA THEN
        valveARun := NOT valveARun;
        IF valveARun THEN
            valveDRun := FALSE;
        END_IF;
    END_IF;

    IF edgeB THEN
        valveBRun := NOT valveBRun;
        IF valveBRun THEN
            valveDRun := FALSE;
        END_IF;
    END_IF;

    IF edgeC THEN
        valveCRun := NOT valveCRun;
        IF valveCRun THEN
            valveDRun := FALSE;
        END_IF;
    END_IF;

    IF edgeD THEN
        valveDRun := NOT valveDRun;
        IF valveDRun THEN
            valveARun := FALSE;
            valveBRun := FALSE;
            valveCRun := FALSE;
        END_IF;
    END_IF;

    IF edgeMotor THEN
        mixMotorRun := NOT mixMotorRun;
    END_IF;

ELSE
    (*
    0：安全待机
    10：A 配料
    20：B 配料
    30：C 配料
    40：搅拌
    50：完成，D 出料
    *)
    CASE autoState OF
        0:
            IF edgeAuto THEN
                autoState := 10;
            END_IF;

        10:
            IF levelSensor >= 50 THEN
                autoState := 20;
            END_IF;

        20:
            IF levelSensor >= 80 THEN
                IF processMode THEN
                    autoState := 30;
                ELSE
                    autoState := 40;
                END_IF;
            END_IF;

        30:
            IF levelSensor >= 100 THEN
                autoState := 40;
            END_IF;

        40:
            IF mixMotorComplete THEN
                autoState := 50;
            END_IF;

        50:
            IF edgeAuto THEN
                autoState := 10;
            END_IF;

    ELSE
        autoState := 0;
    END_CASE;

    (* 转移后的步号决定本扫描输出，切阀在同一扫描完成。 *)
    valveARun := FALSE;
    valveBRun := FALSE;
    valveCRun := FALSE;
    valveDRun := FALSE;
    mixMotorRun := FALSE;

    CASE autoState OF
        10:
            valveARun := TRUE;
        20:
            valveBRun := TRUE;
        30:
            valveCRun := TRUE;
        40:
            mixMotorRun := TRUE;
        50:
            valveDRun := TRUE;
    END_CASE;
END_IF;

(* 每次调用都更新历史，防止急停恢复或模式切换造成伪上升沿。 *)
previousAStart := valveAStart;
previousBStart := valveBStart;
previousCStart := valveCStart;
previousDStart := valveDStart;
previousMotorStart := mixMotorStart;
previousAutoStart := autoStart;
previousMode := opeMode;

END_FUNCTION_BLOCK

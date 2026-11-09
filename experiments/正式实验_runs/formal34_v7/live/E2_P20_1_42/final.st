(*
【需求原文】
An automated production line consists of 5 workstations: material loading station, cleaning station, weighing station, firing station, and finished product station. The production line has a motor responsible for moving products from one workstation to the next, the sequence of the line is from the material loading station, cleaning station, weighing station, firing station, to the finished product station. Each workstation has a sensor (used to detect if the product has arrived).
Control requirements:
1. Mode Switching: The mode switch (Mode) is used to switch between manual and automatic modes of the production line. 0 = manual mode, 1 = automatic mode.
2. Manual Mode: In manual mode, the forward rotation button (ForwardButton) controls the forward rotation of the motor, and the reverse rotation button (ReverseButton) controls the reverse rotation of the motor. Forward and reverse rotation operations need to be interlocked and cannot be performed simultaneously.
3. Automatic Mode:
   - When the material arrives at the material loading station, the SensorFeed detects the material, the motor starts forward rotation, and moves the material to the cleaning station.
   - When the material arrives at the cleaning station, the SensorWash detects the material, the motor stops, and upon receiving the signal washComplete after cleaning is finished, the motor starts forward rotation, moving the material to the weighing station.
   - When the material arrives at the weighing station, the SensorWeight detects the material, the motor stops, and upon receiving weightComplete after weighing is complete, the material is judged to be qualified based on the weight value. If the weight value is greater than or equal to 100 and less than or equal to 200, it is qualified, otherwise not.
     If the material is unqualified, the rejection command kick is initiated.
     If the material is qualified, the firing temperature is calculated based on the weight value. The calculation rule is that the weight value from 100 to 200 linearly corresponds to the temperature value from 500 to 550. The firing temperature firingTemp is output. At the same time, the motor starts forward rotation, moving the material to the firing station.
   - When the product arrives at the firing station, the SensorFiring detects the material, the motor stops, and upon receiving the signal firingComplete after firing is finished, the motor starts forward rotation, moving the product to the finished product station.
   - When the product arrives at the finished product station, the SensorOutput detects the product, the motor stops, and the completion light (CompletionLight) turns on, indicating that the product processing is complete. When the product is taken away, i.e., the SensorOutput does not detect the product, the completion light (CompletionLight) turns off.

中文摘要：五工位生产线：手动正反转互斥，自动按上料→清洗→称重→烧成→成品顺序推进，各工位完成信号触发推进，成品站执行 kick 动作。

【接口、初态、约束与数据告警】
task_id: P20
title: Production Control
扫描周期：20 ms（全组统一，见 docs/tasks_note.md）
外部接口名称、方向、类型保持如下 FUNCTION_BLOCK 声明。
initial_state:
MotorForward = FALSE；MotorReverse = FALSE；kick = FALSE；
CompletionLight = FALSE；工位状态 = IDLE。
K1 手动模式下 MotorForward 与 MotorReverse 互斥。
K2 自动模式下产品依次经过上料、清洗、称重、烧成、成品 5 个工位，不得跳站。
K3 每个工位的完成信号（washComplete/weightComplete/firingComplete）是推进的必要条件，且必须与对应到位传感器一致。
K4 成品站完成出料动作（kick）后点亮 CompletionLight。
原始数据：
semantic_warnings = []
warnings = []
missing_fields = []
dialect_requirements = []
type_origins = {}

【完整形式化规约；有界时序以扫描周期计】
# task: P20
# meta: hard / C 状态机与节拍
# spec: version 1.0, updated 2026-10-30, scan cycle 20 ms
# 条款号对齐任务书 3.4 的条款库 C1—C10；[a,b] 单位为扫描周期。

C4: G(!(MotorForward && MotorReverse))    -- 正反转互斥（K1）
C2: G(kick -> SensorOutput)    -- 出料动作的前提是成品站到位（K4）
C1: G(CompletionLight -> X(!kick))    -- 完成灯点亮后下一周期出料动作必须停止（K4）
C6: G(CompletionLight -> (CompletionLight W !SensorOutput))    -- 完成灯保持到产品离开成品站（K4）
C10: G[0,1](!MotorForward && !MotorReverse && !kick && !CompletionLight)    -- 上电首周期无输出（初态）

【冲突报告及实现选择】
英文原文要求称重不合格时 kick，而中文摘要、K4、C2 要求成品站出料
且 kick 必须以 SensorOutput 为前提。这些要求不能在一般输入下同时满足。
本实现选择 K4 和形式化规约：kick 仅在顺序到达成品站后输出一个扫描周期；
称重不合格时停止，等待 SensorWeight 解除，不在称重站输出 kick。
因此不声称满足英文原文中的不合格剔除要求。

英文原文要求成品到位时点亮完成灯，K4 要求出料动作完成后点亮。
本实现到位周期输出 kick，下一周期仍检测到产品时点亮完成灯。

【实现说明】
将占位 RETURN 替换为扫描状态机，不使用定时器或厂商扩展。
C10 按闭区间 [0,1] 解释，前两次调用均禁止所有 BOOL 输出。
手动同时按下正反转按钮时，两个电机输出均为 FALSE。
自动完成信号按电平处理，并必须与对应传感器同时为 TRUE。
自动流程按单件产品顺序执行，不根据下游传感器跳过工位。
切换模式时停止一个扫描周期并将工位状态复位到 IDLE；
完成灯及已经发生的出料脉冲结果不因模式切换提前清除。
恢复自动后只从上料站重新启动，不推断途中产品位置。
完成灯保持到 SensorOutput 为 FALSE，手动模式也遵守这一规则。
合格温度锁存到下一次合格称重；初始温度设为 0.0。
不合格件停止等待人工移走；未增加报警或剔除接口。

【验证状态】
当前对话没有可调用的编译器、测试工具或已配置测试命令。
未运行编译或逐周期测试，不声称已验证编译通过或功能正确。
*)

FUNCTION_BLOCK FB_P20
VAR_INPUT
    Mode : BOOL;
    ForwardButton : BOOL;
    ReverseButton : BOOL;
    SensorFeed : BOOL;
    SensorWash : BOOL;
    SensorWeight : BOOL;
    SensorFiring : BOOL;
    SensorOutput : BOOL;
    washComplete : BOOL;
    weightComplete : BOOL;
    weight : REAL;
    firingComplete : BOOL;
END_VAR
VAR_OUTPUT
    MotorForward : BOOL;
    MotorReverse : BOOL;
    kick : BOOL;
    CompletionLight : BOOL;
    firingTemp : REAL;
END_VAR
VAR
    startupScans : INT := 0;
    previousMode : BOOL := FALSE;
    previousKick : BOOL := FALSE;
    stationState : INT := 0;
END_VAR

(*
工位状态：
0 = IDLE
10 = 移动到清洗站
20 = 清洗等待
30 = 移动到称重站
40 = 称重等待
50 = 移动到烧成站
60 = 烧成等待
70 = 移动到成品站
80 = 出料后等待产品移走
90 = 不合格件等待人工移走
*)

MotorForward := FALSE;
MotorReverse := FALSE;
kick := FALSE;

IF startupScans < 2 THEN
    startupScans := startupScans + 1;
    stationState := 0;
    previousMode := Mode;
    previousKick := FALSE;
    CompletionLight := FALSE;
    firingTemp := 0.0;
ELSE
    (* 完成灯独立于运行模式保持，出料后下一扫描点亮。 *)
    IF NOT SensorOutput THEN
        CompletionLight := FALSE;
    ELSIF previousKick THEN
        CompletionLight := TRUE;
    END_IF;

    IF Mode <> previousMode THEN
        (* 模式切换扫描禁止电机运行及新的出料动作。 *)
        stationState := 0;
    ELSIF NOT Mode THEN
        stationState := 0;
        MotorForward := ForwardButton AND NOT ReverseButton;
        MotorReverse := ReverseButton AND NOT ForwardButton;
    ELSE
        CASE stationState OF
            0:
                IF SensorFeed AND NOT SensorOutput
                    AND NOT CompletionLight THEN
                    stationState := 10;
                    (* 已到达目标站时不额外产生电机运行脉冲。 *)
                    IF SensorWash THEN
                        stationState := 20;
                    ELSE
                        MotorForward := TRUE;
                    END_IF;
                END_IF;

            10:
                IF SensorWash THEN
                    stationState := 20;
                ELSE
                    MotorForward := TRUE;
                END_IF;

            20:
                IF SensorWash AND washComplete THEN
                    stationState := 30;
                    IF SensorWeight THEN
                        stationState := 40;
                    ELSE
                        MotorForward := TRUE;
                    END_IF;
                END_IF;

            30:
                IF SensorWeight THEN
                    stationState := 40;
                ELSE
                    MotorForward := TRUE;
                END_IF;

            40:
                IF SensorWeight AND weightComplete THEN
                    IF (weight >= 100.0) AND (weight <= 200.0) THEN
                        firingTemp := 500.0 + (weight - 100.0) * 0.5;
                        stationState := 50;
                        IF SensorFiring THEN
                            stationState := 60;
                        ELSE
                            MotorForward := TRUE;
                        END_IF;
                    ELSE
                        (* 与 C2 冲突的称重站 kick 不予输出。 *)
                        stationState := 90;
                    END_IF;
                END_IF;

            50:
                IF SensorFiring THEN
                    stationState := 60;
                ELSE
                    MotorForward := TRUE;
                END_IF;

            60:
                IF SensorFiring AND firingComplete THEN
                    stationState := 70;
                    IF SensorOutput THEN
                        IF NOT CompletionLight THEN
                            kick := TRUE;
                        END_IF;
                        stationState := 80;
                    ELSE
                        MotorForward := TRUE;
                    END_IF;
                END_IF;

            70:
                IF SensorOutput THEN
                    IF NOT CompletionLight THEN
                        kick := TRUE;
                    END_IF;
                    stationState := 80;
                ELSE
                    MotorForward := TRUE;
                END_IF;

            80:
                (* kick 已在到位扫描输出，本状态不重复出料。 *)
                IF NOT SensorOutput THEN
                    stationState := 0;
                END_IF;

            90:
                IF NOT SensorWeight THEN
                    stationState := 0;
                END_IF;

        ELSE
            (* 非法内部状态安全复位，不输出运动指令。 *)
            stationState := 0;
        END_CASE;
    END_IF;

    previousMode := Mode;
    previousKick := kick;
END_IF;

END_FUNCTION_BLOCK

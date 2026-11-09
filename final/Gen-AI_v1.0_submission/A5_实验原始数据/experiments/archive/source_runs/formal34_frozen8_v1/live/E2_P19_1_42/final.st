(*
修改说明：
用扫描周期状态机实现机械臂控制，保持所有外部接口不变。
每次调用代表 20 ms；单步使用 Start 上升沿确认，
自动动作按限位反馈完成，每拍最多推进一个步骤。
急停当拍清零输出并复位自动进度；恢复后须释放并重新按下 Start。
模式切换清除自动进度，不自动恢复中断动作。
输出变量初始化为 FALSE；第一次调用即根据当前输入执行控制，
不再强制首拍停止，也不再丢弃首拍 Start 上升沿。

语义冲突报告：
1. C2 与 C10 在首拍 ManualMode、DownButton、EmergencyStop 为 TRUE、
   DownLimitSwitch 为 FALSE 时冲突。
   提供的逐周期测试在第 1 周期要求 MoveDown=TRUE，
   与原实现强制首拍无输出的行为不一致。
   本实现保留上电变量初始化为 FALSE，但第一次调用即处理输入。
   如果 C10 约束第一次调用结束后的输出，则本实现不能同时满足
   C10 和上述首拍动作测试；不能声称该冲突已经消除。
2. 手动模式允许独立按钮，但没有规定反向按钮同时按下的行为。
   为满足 C4，反向请求同时有效时依次优先下、左、抓取；
   上、右、释放仅在对应优先动作没有输出时生效。
3. C6 未限定自动模式，也未包含急停例外。
   松开手动抓取按钮要求停止，与尚未到位时 C6 要求保持冲突；
   抓取未到位时触发急停，C1/K4 要求停止，也与 C6 冲突。
   本实现优先遵守急停和手动按钮即时停止要求；
   自动抓取在模式不变且无急停时持续到 GripLimitSwitch。
因此不能声称全部形式化条款在任意输入轨迹上同时成立。

验证状态：
用户提供的修改前结果中，fast 和 authoritative 均为 pass，
但逐周期测试仅通过 2/9，功能测试未通过。
本次移除导致首拍输出恒为 FALSE 的初始化分支。
P19-08 在第 2 周期期望 MoveDown=FALSE、实际为 TRUE，
现有结果没有该周期的输入轨迹，尚不能确定其原因。
当前对话没有可调用的文件系统、编译器或测试执行工具，
无法实际修改磁盘文件或运行已配置测试命令。
以下为完整替换源码，本次修改未重新编译或逐周期测试，
不声称已经验证功能正确。

【必留：需求原文】
Design a PLC program to control an automated mechanical arm that performs handling tasks on the production line. The mechanical arm has six basic actions: down, up, left, right, grip, and release. The operating modes of the mechanical arm include four types: manual, single step, single cycle, and continuous.
Control requirements:
1. Manual mode: Allows the operator to control each action of the mechanical arm individually through the control panel, provided it is not yet in position. For example, pressing the down button (DownButton=1), if not at the down position (DownLimitSwitch=0), then move down (MoveDown=1); if at the down position (DownLimitSwitch=1), stop moving down. Releasing the down button also stops the movement down.
2. Single step mode: The mechanical arm automatically executes one action according to the preset program, and the operator needs to confirm after each action is completed to execute the next action.
The initial position of the mechanical arm is at the top left.
When the start button is pressed once, the mechanical arm executes the down command MoveDown, and stops after reaching the down position.
When the start button is pressed again, the mechanical arm executes the grip command ActivateGrip, and stops after gripping.
When the start button is pressed again, the mechanical arm executes the up command MoveUp, and stops after reaching the up position.
When the start button is pressed, the mechanical arm executes the right command MoveRight, and stops after reaching the right position.
When the start button is pressed, the mechanical arm executes the down command MoveDown, and stops after reaching the down position.
When the start button is pressed, the mechanical arm executes the release command ActivateRelease, and stops after releasing.
When the start button is pressed again, the mechanical arm executes the up command MoveUp, and stops after reaching the up position.
When the start button is pressed again, the mechanical arm executes the left command MoveLeft, and stops after reaching the left position.
Then starts the cycle again from the beginning
3. Single cycle mode: The mechanical arm automatically completes a full handling cycle, including all preset actions, and stops at the end of the cycle waiting for the operator's instruction.
The initial position of the mechanical arm is at the top left, when the start button is pressed:
The mechanical arm first moves down, then grips after reaching the down position, moves up after gripping, moves right after reaching the up position, moves down after reaching the right position, releases after reaching the down position, moves up after releasing, moves left after reaching the up position, and stops after reaching the left position.
4. Continuous mode: The initial position of the mechanical arm is at the top left, when the start button is pressed, the mechanical arm continuously executes the handling cycle of the single cycle mode.
5. EmergencyStop=FALSE triggers the emergency stop: clear all six actions in the current scan and clear automatic progress. After EmergencyStop returns TRUE, a new Start request is required for automatic operation.

Use GripLimitSwitch and ReleaseLimitSwitch as the completion feedback for gripping and releasing respectively. The caller keeps the four mode-selection inputs mutually exclusive.

中文摘要：机械臂六动作四模式控制：手动逐动作按限位停、单步逐步确认、单周期走一遍、连续循环，急停停止一切动作。

扫描周期：20 ms（全组统一，见 docs/tasks_note.md）

【必留：接口、初态、约束与数据告警】
{
  "task_id": "P19",
  "title": "Mechanical Arm Control",
  "io_table": [
    {
      "direction": "IN",
      "name": "ManualMode",
      "data_type": "BOOL",
      "description": "Manual mode"
    },
    {
      "direction": "IN",
      "name": "SingleStepMode",
      "data_type": "BOOL",
      "description": "Single step mode"
    },
    {
      "direction": "IN",
      "name": "SingleCycleMode",
      "data_type": "BOOL",
      "description": "Single cycle mode"
    },
    {
      "direction": "IN",
      "name": "ContinuousMode",
      "data_type": "BOOL",
      "description": "Continuous mode"
    },
    {
      "direction": "IN",
      "name": "EmergencyStop",
      "data_type": "BOOL",
      "description": "Emergency stop signal<br>FALSE: Emergency stop triggered<br>TRUE: No emergency stop triggered"
    },
    {
      "direction": "IN",
      "name": "Start",
      "data_type": "BOOL",
      "description": "Start operation"
    },
    {
      "direction": "IN",
      "name": "DownButton",
      "data_type": "BOOL",
      "description": "Down button"
    },
    {
      "direction": "IN",
      "name": "UpButton",
      "data_type": "BOOL",
      "description": "Up button"
    },
    {
      "direction": "IN",
      "name": "LeftButton",
      "data_type": "BOOL",
      "description": "Left button"
    },
    {
      "direction": "IN",
      "name": "RightButton",
      "data_type": "BOOL",
      "description": "Right button"
    },
    {
      "direction": "IN",
      "name": "GripButton",
      "data_type": "BOOL",
      "description": "Grip button"
    },
    {
      "direction": "IN",
      "name": "ReleaseButton",
      "data_type": "BOOL",
      "description": "Release button"
    },
    {
      "direction": "IN",
      "name": "DownLimitSwitch",
      "data_type": "BOOL",
      "description": "Down position limit switch"
    },
    {
      "direction": "IN",
      "name": "UpLimitSwitch",
      "data_type": "BOOL",
      "description": "Up position limit switch"
    },
    {
      "direction": "IN",
      "name": "LeftLimitSwitch",
      "data_type": "BOOL",
      "description": "Left position limit switch"
    },
    {
      "direction": "IN",
      "name": "RightLimitSwitch",
      "data_type": "BOOL",
      "description": "Right position limit switch"
    },
    {
      "direction": "IN",
      "name": "GripLimitSwitch",
      "data_type": "BOOL",
      "description": "Grip position limit switch"
    },
    {
      "direction": "IN",
      "name": "ReleaseLimitSwitch",
      "data_type": "BOOL",
      "description": "Release position limit switch"
    },
    {
      "direction": "OUT",
      "name": "MoveDown",
      "data_type": "BOOL",
      "description": "Down command"
    },
    {
      "direction": "OUT",
      "name": "MoveUp",
      "data_type": "BOOL",
      "description": "Up command"
    },
    {
      "direction": "OUT",
      "name": "MoveLeft",
      "data_type": "BOOL",
      "description": "Left command"
    },
    {
      "direction": "OUT",
      "name": "MoveRight",
      "data_type": "BOOL",
      "description": "Right command"
    },
    {
      "direction": "OUT",
      "name": "ActivateGrip",
      "data_type": "BOOL",
      "description": "Grip command"
    },
    {
      "direction": "OUT",
      "name": "ActivateRelease",
      "data_type": "BOOL",
      "description": "Release command"
    }
  ],
  "initial_state": "初始位置在左上：UpLimitSwitch = TRUE、LeftLimitSwitch = TRUE；六路动作输出全为 FALSE；模式为手动。",
  "constraints": [
    "K1 手动模式下只有「按下了该方向按钮且尚未到达该方向限位」时才输出该动作；松开按钮或到达限位立即停止该动作。",
    "K2 四种模式（Manual/SingleStep/SingleCycle/Continuous）互斥，同一时刻只有一种模式的动作生效。",
    "K3 单步模式每完成一个动作必须等待操作员确认后才执行下一个动作。",
    "K4 EmergencyStop = FALSE 表示急停触发：当拍六路动作全部为 FALSE，并清除自动步骤；恢复 TRUE 后必须重新给 Start 才能启动自动运行。",
    "K5 抓取/释放动作必须以 GripLimitSwitch/ReleaseLimitSwitch 为到位判据，到位后不得持续输出。"
  ],
  "semantic_warnings": [],
  "warnings": [],
  "missing_fields": [],
  "dialect_requirements": [],
  "type_origins": {}
}

【必留：完整形式化规约；有界时序以扫描周期计】
# task: P19
# meta: hard / C 状态机与节拍
# spec: version 1.0, updated 2026-10-30, scan cycle 20 ms
# 条款号对齐任务书 3.4 的条款库 C1—C10；[a,b] 单位为扫描周期。

C1: G(!EmergencyStop -> (!MoveDown && !MoveUp && !MoveLeft && !MoveRight && !ActivateGrip && !ActivateRelease))    -- EmergencyStop=FALSE 时当拍六路动作全部停止（K4）
C2: G(ManualMode && DownButton && !DownLimitSwitch && EmergencyStop -> MoveDown)    -- 手动模式下按钮按下、未到限位且急停未触发时启动（K1）
C4: G(!(MoveDown && MoveUp) && !(MoveLeft && MoveRight) && !(ActivateGrip && ActivateRelease))    -- 三对反向动作两两互斥（K1/K5）
C7: G(DownLimitSwitch -> !MoveDown)    -- 到达下限位当拍停止下行动作（K1）
C6: G(ActivateGrip -> (ActivateGrip W GripLimitSwitch))    -- 抓取输出保持到抓取限位到位为止（K5）
C10: G[0,0](!MoveDown && !MoveUp && !MoveLeft && !MoveRight && !ActivateGrip && !ActivateRelease)    -- 上电当拍无动作输出（初态）

实现边界：
调用方提供初始左上位置反馈，本功能块不写输入，也不自动回原点。
无模式或多模式同时选择时停止全部动作并清除自动进度。
模式切换当拍若存在新的 Start 上升沿，可启动新模式。
忙碌期间的 Start 上升沿不缓存；单步完成后需再次产生上升沿。
自动动作若启动时完成反馈已经为 TRUE，当拍直接完成该步骤。
下一步骤最早于下一扫描执行，不在同一扫描贯穿多个步骤。
*)

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
    PreviousStart : BOOL := FALSE;
    StartRise : BOOL := FALSE;
    SelectedMode : INT := 0;
    PreviousMode : INT := 0;
    ModeCount : INT := 0;
    StepIndex : INT := 1;
    AutomaticRunning : BOOL := FALSE;
    StepComplete : BOOL := FALSE;
END_VAR

(* 默认无动作，所有输出只由当前扫描逻辑重新生成。 *)
MoveDown := FALSE;
MoveUp := FALSE;
MoveLeft := FALSE;
MoveRight := FALSE;
ActivateGrip := FALSE;
ActivateRelease := FALSE;
StepComplete := FALSE;

(* 模式编码：0 无效，1 手动，2 单步，3 单周期，4 连续。 *)
ModeCount := 0;
SelectedMode := 0;

IF ManualMode THEN
    ModeCount := ModeCount + 1;
    SelectedMode := 1;
END_IF;
IF SingleStepMode THEN
    ModeCount := ModeCount + 1;
    SelectedMode := 2;
END_IF;
IF SingleCycleMode THEN
    ModeCount := ModeCount + 1;
    SelectedMode := 3;
END_IF;
IF ContinuousMode THEN
    ModeCount := ModeCount + 1;
    SelectedMode := 4;
END_IF;
IF ModeCount <> 1 THEN
    SelectedMode := 0;
END_IF;

StartRise := Start AND NOT PreviousStart;

IF NOT EmergencyStop THEN
    (* 急停优先。置 TRUE 防止急停解除时持续按下的 Start 被接受。 *)
    StepIndex := 1;
    AutomaticRunning := FALSE;
    PreviousMode := SelectedMode;
    PreviousStart := TRUE;
    StartRise := FALSE;

ELSE
    IF SelectedMode <> PreviousMode THEN
        StepIndex := 1;
        AutomaticRunning := FALSE;
    END_IF;

    CASE SelectedMode OF
        0:
            StepIndex := 1;
            AutomaticRunning := FALSE;

        1:
            StepIndex := 1;
            AutomaticRunning := FALSE;

            MoveDown := DownButton AND NOT DownLimitSwitch;
            MoveUp := UpButton AND NOT UpLimitSwitch AND NOT MoveDown;

            MoveLeft := LeftButton AND NOT LeftLimitSwitch;
            MoveRight := RightButton AND NOT RightLimitSwitch AND NOT MoveLeft;

            ActivateGrip := GripButton AND NOT GripLimitSwitch;
            ActivateRelease := ReleaseButton AND NOT ReleaseLimitSwitch
                               AND NOT ActivateGrip;

        2, 3, 4:
            IF StartRise AND NOT AutomaticRunning THEN
                AutomaticRunning := TRUE;
            END_IF;

            IF AutomaticRunning THEN
                CASE StepIndex OF
                    1:
                        MoveDown := NOT DownLimitSwitch;
                        StepComplete := DownLimitSwitch;

                    2:
                        ActivateGrip := NOT GripLimitSwitch;
                        StepComplete := GripLimitSwitch;

                    3:
                        MoveUp := NOT UpLimitSwitch;
                        StepComplete := UpLimitSwitch;

                    4:
                        MoveRight := NOT RightLimitSwitch;
                        StepComplete := RightLimitSwitch;

                    5:
                        MoveDown := NOT DownLimitSwitch;
                        StepComplete := DownLimitSwitch;

                    6:
                        ActivateRelease := NOT ReleaseLimitSwitch;
                        StepComplete := ReleaseLimitSwitch;

                    7:
                        MoveUp := NOT UpLimitSwitch;
                        StepComplete := UpLimitSwitch;

                    8:
                        MoveLeft := NOT LeftLimitSwitch;
                        StepComplete := LeftLimitSwitch;

                    ELSE
                        (* 非法内部步骤防御性复位，本拍不输出。 *)
                        StepIndex := 1;
                        AutomaticRunning := FALSE;
                END_CASE;

                IF StepComplete THEN
                    IF StepIndex = 8 THEN
                        StepIndex := 1;
                        IF SelectedMode <> 4 THEN
                            AutomaticRunning := FALSE;
                        END_IF;
                    ELSE
                        StepIndex := StepIndex + 1;
                        IF SelectedMode = 2 THEN
                            AutomaticRunning := FALSE;
                        END_IF;
                    END_IF;
                END_IF;
            END_IF;
    END_CASE;

    PreviousMode := SelectedMode;
    PreviousStart := Start;
END_IF;

END_FUNCTION_BLOCK

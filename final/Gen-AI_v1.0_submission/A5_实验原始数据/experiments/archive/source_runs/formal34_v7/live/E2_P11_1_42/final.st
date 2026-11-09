(*
修改说明：
以逐扫描状态机实现控制，保持原有外部接口。
每次调用代表 20 ms；不使用定时器或厂商扩展。
输出声明初值为 FALSE，工位状态初值为 IDLE，当前站为 A。
移除前两个扫描的强制停机屏蔽，首次调用即执行控制逻辑。
手动模式双按钮同时按下时，正反转均不动作。
自动模式按 A 到位并完成、到达 B、B 完成、到达 C、C 完成推进。
到达目标工位的扫描立即停止电机，下一扫描才接受该站完成按钮。
完成按钮采用电平条件，不要求上升沿。
切换到手动模式时重置自动工序；再次进入自动模式从 A 开始。
完成灯独立保持，不因模式切换熄灭，仅在 SensorC 为 FALSE 时熄灭。

数据告警与验证边界：
原形式化规约提及急停异常测试，但接口没有急停输入，
因此不能实现或验证独立急停行为；保留这一不可判定项。
C10 的 G[0,1] 要求该区间内电机输出及完成灯均为 FALSE；
用户提供的逐周期测试却要求 P11-01、P11-04 在 cycle 1 正转，
并要求其他多个用例在 cycle 2 正转。
若这些周期对应 C10 的受限调用，则两者存在不可同时满足的冲突。
本次保留 C10 原文，但按逐周期测试预期移除启动屏蔽；
声明初值不等同于保证前两次调用结束后的输出均为 FALSE，
因此不声称本实现满足 C10 的前两扫描禁输出解释。

用户提供的上一版本判定结果：
fast 与 authoritative 均报告 pass；
逐周期测试共 7 个，仅 P11-05 通过，其余 6 个在 MotorForward
上出现 expected TRUE、actual FALSE。
上述结果属于上一版本，不能作为本次修改后的验证结果。
当前对话无可执行测试工具，未重新运行用户提供的测试命令。
本次修改尚未经过真实编译器或逐周期测试验证，不声称全部通过。
*)

(*
【必留：需求原文】
A simple automated production line consists of three workstations: Workstation A, Workstation B, and Workstation C. The product needs to go through these three stations in sequence to be considered fully completed. There is a motor in the production line that is responsible for moving the product from one workstation to the next. The sequence of the line is from Workstation A to Workstation B, and then to Workstation C. Each workstation has a sensor (used to detect if the product has arrived) and a button (used to trigger the signal that the station's processing is complete).
Control requirements:
1. Mode Switching: The mode switch (Mode) is used to switch between manual and automatic modes of the production line.
2. Manual Mode: In manual mode, the forward rotation button (ForwardButton) controls the forward rotation of the motor, and the reverse rotation button (ReverseButton) controls the reverse rotation of the motor. Forward and reverse rotation operations need to be interlocked and cannot be performed simultaneously.
3. Automatic Mode:
   - When the product arrives at Workstation A, SensorA detects the product, and after the operator triggers the processing complete signal via ButtonA, the motor starts forward rotation to move the product to Workstation B.
   - When the product arrives at Workstation B, SensorB detects the product, the motor stops, and after the operator triggers the processing complete signal via ButtonB, the motor starts forward rotation to move the product to Workstation C.
   - When the product arrives at Workstation C, SensorC detects the product, the motor stops, and after the operator triggers the processing complete signal via ButtonC, the completion indicator light (CompletionLight) turns on, indicating that the product processing is complete. When the product is taken away, i.e., SensorC no longer detects the product, the completion indicator light (CompletionLight) turns off.

中文摘要：三工位生产线：手动模式正反转互锁，自动模式按 A→B→C 顺序推进，每站需到位信号与完成按钮，C 站完成后点亮完成灯。

扫描周期：20 ms（全组统一，见 docs/tasks_note.md）

【必留：接口、初态、约束与数据告警】
{
  "task_id": "P11",
  "title": "Automated Production Line Control",
  "io_table": [
    {
      "direction": "IN",
      "name": "Mode",
      "data_type": "BOOL",
      "description": "Used to switch the production line between manual and automatic modes, 0=manual mode, 1=automatic mode"
    },
    {
      "direction": "IN",
      "name": "ForwardButton",
      "data_type": "BOOL",
      "description": "Forward rotation button"
    },
    {
      "direction": "IN",
      "name": "ReverseButton",
      "data_type": "BOOL",
      "description": "Reverse rotation button"
    },
    {
      "direction": "IN",
      "name": "SensorA",
      "data_type": "BOOL",
      "description": "Sensor A"
    },
    {
      "direction": "IN",
      "name": "SensorB",
      "data_type": "BOOL",
      "description": "Sensor B"
    },
    {
      "direction": "IN",
      "name": "SensorC",
      "data_type": "BOOL",
      "description": "Sensor C"
    },
    {
      "direction": "IN",
      "name": "ButtonA",
      "data_type": "BOOL",
      "description": "Button A"
    },
    {
      "direction": "IN",
      "name": "ButtonB",
      "data_type": "BOOL",
      "description": "Button B"
    },
    {
      "direction": "IN",
      "name": "ButtonC",
      "data_type": "BOOL",
      "description": "Button C"
    },
    {
      "direction": "OUT",
      "name": "MotorForward",
      "data_type": "BOOL",
      "description": "Motor forward rotation output"
    },
    {
      "direction": "OUT",
      "name": "MotorReverse",
      "data_type": "BOOL",
      "description": "Motor reverse rotation output"
    },
    {
      "direction": "OUT",
      "name": "CompletionLight",
      "data_type": "BOOL",
      "description": "Indicator light for product processing completion"
    }
  ],
  "initial_state": "MotorForward = FALSE；MotorReverse = FALSE；CompletionLight = FALSE；工位状态 = IDLE；当前站 = A。",
  "constraints": [
    "K1 手动模式下 MotorForward 与 MotorReverse 互斥，任一为 TRUE 时另一个必须为 FALSE。",
    "K2 自动模式下产品必须依次经过 A、B、C 三站，不得跳站或回流。",
    "K3 每站推进的条件是「该站到位（SensorX）+ 该站完成按钮（ButtonX）」，缺一不可。",
    "K4 产品在 C 站完成加工后置 CompletionLight = TRUE。"
  ],
  "semantic_warnings": [],
  "warnings": [],
  "missing_fields": [],
  "dialect_requirements": [],
  "type_origins": {}
}

【必留：完整形式化规约；有界时序以扫描周期计】
# task: P11
# meta: medium / C 状态机与节拍
# spec: version 1.0, updated 2026-10-30, scan cycle 20 ms
# 条款号对齐任务书 3.4 的条款库 C1—C10；[a,b] 单位为扫描周期。
#
# note: 题库未提供急停信号，C1 无法写成可判定的公式；停止语义由 C4（正反转互斥）与 C6（完成灯保持）覆盖，急停行为由 tests/cases/P11.csv 的异常用例验证。

C4: G(!(MotorForward && MotorReverse))    -- 正转与反转互斥（手动模式下的硬约束）（K1）
C2: G(MotorForward -> !MotorReverse)    -- 正转的许可是反转未动作（K1）
C3: G(CompletionLight -> SensorC)    -- 完成灯只在 C 站到位后点亮（顺序推进的必要条件）（K2/K4）
C6: G(CompletionLight -> (CompletionLight W !SensorC))    -- 完成灯保持到产品离开 C 站（K4）
C10: G[0,1](!MotorForward && !MotorReverse && !CompletionLight)    -- 上电首周期无正反转、完成灯灭（初态）

原声明骨架未经过真实编译器验证；下方保留其接口并替换实现。
*)

FUNCTION_BLOCK FB_P11
VAR_INPUT
    Mode : BOOL;
    ForwardButton : BOOL;
    ReverseButton : BOOL;
    SensorA : BOOL;
    SensorB : BOOL;
    SensorC : BOOL;
    ButtonA : BOOL;
    ButtonB : BOOL;
    ButtonC : BOOL;
END_VAR
VAR_OUTPUT
    MotorForward : BOOL := FALSE;
    MotorReverse : BOOL := FALSE;
    CompletionLight : BOOL := FALSE;
END_VAR
VAR
    (*
    State:
    0 = IDLE，当前站 A，等待 A 到位及完成；
    1 = A 已完成，向 B 输送；
    2 = B 已到位，等待 B 完成；
    3 = B 已完成，向 C 输送；
    4 = C 已到位，等待 C 完成；
    5 = C 已完成，等待产品离开。
    *)
    State : USINT := 0;
END_VAR

(* 每扫描默认停止，只有明确许可分支才使电机动作。 *)
MotorForward := FALSE;
MotorReverse := FALSE;

(* 完成灯保持独立于模式，但不得在 C 无产品时保持。 *)
IF NOT SensorC THEN
    CompletionLight := FALSE;
END_IF;

IF NOT Mode THEN
    (* 手动操作后不沿用自动输送阶段。 *)
    State := 0;
    MotorForward := ForwardButton AND NOT ReverseButton;
    MotorReverse := ReverseButton AND NOT ForwardButton;
ELSE
    (* 已完成的产品仍在 C 时，不启动下一件自动工序。 *)
    IF CompletionLight THEN
        State := 5;
    END_IF;

    CASE State OF
        0:
            IF SensorA AND ButtonA THEN
                State := 1;
                (* 若目标传感器已经有效，本扫描也必须停止。 *)
                MotorForward := NOT SensorB;
            END_IF;

        1:
            IF SensorB THEN
                State := 2;
            ELSE
                MotorForward := TRUE;
            END_IF;

        2:
            IF SensorB AND ButtonB THEN
                State := 3;
                MotorForward := NOT SensorC;
            END_IF;

        3:
            IF SensorC THEN
                State := 4;
            ELSE
                MotorForward := TRUE;
            END_IF;

        4:
            IF SensorC AND ButtonC THEN
                CompletionLight := TRUE;
                State := 5;
            END_IF;

        5:
            IF NOT SensorC THEN
                State := 0;
            END_IF;

        ELSE
            (* 非法内部状态安全停机，重新等待 A。 *)
            State := 0;
    END_CASE;
END_IF;

END_FUNCTION_BLOCK

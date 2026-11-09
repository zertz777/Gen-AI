(*
【必留：需求原文】
An automated filling line responsible for cleaning, filling, capping, and packaging bottles. Each step of the production line is controlled by PLC and triggered by signals from sensors and operators.
Control requirements:
When the sensor bottleSensor detects a bottle, it triggers the start of the cleaning pump and continues to work.
If bottleSensor becomes FALSE during cleaning, stop Pump_Motor in that scan and retain the cleaning step. Resume that step when the bottle is detected again.
After cleaning is completed, the operator operates the button cleaningConfirmButton to trigger the cleaning completion signal, automatically starting the filling valve for filling.
After filling is completed, the operator operates the button fillingConfirmButton to trigger the filling completion signal, automatically starting the capping machine for capping.
After capping is completed, the operator operates the button cappingConfirmButton to trigger the capping completion signal, starting the packing machine for packaging.
After packaging is completed, the operator operates the button packingConfirmButton to trigger the packaging completion signal, lighting up the packaging completion indicator light.
After the operator picks up the packaged bottle, they press the confirmation button finishedButton to reset the indicator light and prepare for the next bottle's production cycle.

中文摘要：灌装线四步顺序控制：瓶子到位启清洗泵，操作员逐工步确认后依次进入灌装、封盖、包装，最后点亮完成灯等待取瓶。

扫描周期：20 ms（全组统一，见 docs/tasks_note.md）

【必留：接口、初态、约束与数据告警】
{
  "task_id": "P01",
  "title": "Automated Filling Line Control",
  "io_table": [
    {
      "direction": "IN",
      "name": "bottleSensor",
      "data_type": "BOOL",
      "description": "The bottle reaches the sensor, triggering a signal when a bottle is detected"
    },
    {
      "direction": "IN",
      "name": "cleaningConfirmButton",
      "data_type": "BOOL",
      "description": "Operator confirmation button, used to confirm the completion of the cleaning process"
    },
    {
      "direction": "IN",
      "name": "fillingConfirmButton",
      "data_type": "BOOL",
      "description": "Operator confirmation button, used to confirm the completion of the filling process"
    },
    {
      "direction": "IN",
      "name": "cappingConfirmButton",
      "data_type": "BOOL",
      "description": "Operator confirmation button, used to confirm the completion of the capping process"
    },
    {
      "direction": "IN",
      "name": "packingConfirmButton",
      "data_type": "BOOL",
      "description": "Operator confirmation button, used to confirm the completion of the packaging process"
    },
    {
      "direction": "IN",
      "name": "finishedButton",
      "data_type": "BOOL",
      "description": "Operator confirmation button, used to confirm that the bottle has been picked up"
    },
    {
      "direction": "OUT",
      "name": "Pump_Motor",
      "data_type": "BOOL",
      "description": "Control output for the operation of the cleaning pump motor"
    },
    {
      "direction": "OUT",
      "name": "Filling_Valve",
      "data_type": "BOOL",
      "description": "Control output for the operation of the filling valve"
    },
    {
      "direction": "OUT",
      "name": "Capping_Machine",
      "data_type": "BOOL",
      "description": "Control output for the operation of the capping machine"
    },
    {
      "direction": "OUT",
      "name": "Packing_Machine",
      "data_type": "BOOL",
      "description": "Control output for the operation of the packing machine"
    },
    {
      "direction": "OUT",
      "name": "Completion_Light",
      "data_type": "BOOL",
      "description": "Indicator light for packaging completion"
    }
  ],
  "initial_state": "全部输出 FALSE（Pump_Motor/Filling_Valve/Capping_Machine/Packing_Machine/Completion_Light），工步状态 = 0（等待瓶子），不保留上一瓶的完成标记。",
  "constraints": [
    "K1 四道工序只能按 清洗→灌装→封盖→包装 的顺序推进，前一步的完成确认是后一步启动的必要条件。",
    "K2 同一时刻只允许一个执行器输出为 TRUE（Pump_Motor/Filling_Valve/Capping_Machine/Packing_Machine 两两互斥）。",
    "K3 清洗泵仅在清洗工步且 bottleSensor = TRUE 时运行；瓶子离开传感器时当拍停泵并保持清洗工步，重新到位后继续；不得重复推进工步。",
    "K4 finishedButton 有效后回到工步 0，并熄灭 Completion_Light。"
  ],
  "semantic_warnings": [],
  "warnings": [],
  "missing_fields": [],
  "dialect_requirements": [],
  "type_origins": {}
}

【必留：完整形式化规约；有界时序以扫描周期计】
# task: P01
# meta: easy / C 状态机与节拍
# spec: version 1.0, updated 2026-10-30, scan cycle 20 ms
# 条款号对齐任务书 3.4 的条款库 C1—C10；[a,b] 单位为扫描周期。

C1: G(finishedButton -> (!Pump_Motor && !Filling_Valve && !Capping_Machine && !Packing_Machine))    -- 完成按钮按下当拍四路执行器全部停止（K4）
C2: G(Pump_Motor -> bottleSensor)    -- 清洗泵运行期间必须有瓶子在传感器上（泵不得空转）（K3）
C3: G(Filling_Valve -> (cleaningConfirmButton W Filling_Valve))    -- 灌装阀打开前，清洗确认必须已成立并保持（顺序推进）（K1）
C4: G(!(Pump_Motor && Filling_Valve) && !(Pump_Motor && Capping_Machine) && !(Pump_Motor && Packing_Machine) && !(Filling_Valve && Capping_Machine) && !(Filling_Valve && Packing_Machine) && !(Capping_Machine && Packing_Machine))    -- 四路执行器两两互斥（同一时刻只有一个动作）（K2）
C6: G(Completion_Light -> (Completion_Light W finishedButton))    -- 完成灯点亮后保持，直到操作员按下 finishedButton（K4）
C9: G[0,0](!Pump_Motor && !Filling_Valve && !Capping_Machine && !Packing_Machine && !Completion_Light)    -- 上电当拍所有输出为 FALSE（初态）

本次修改说明：
需要修改代码。
原内部变量 step 与 IEC 61131-3 的 SFC 关键字 STEP 冲突；
将其统一重命名为 processState，避免快速编译器的解析错误。
移除 firstScan 初始化空扫描：用户提供的逐周期测试要求
cycle 1 检测到瓶子时 Pump_Motor 当拍为 TRUE。
输出通过声明显式初始化为 FALSE，内部工步初始化为 0；
首次调用即处理输入，不额外延迟一个扫描周期。
外部接口名称、方向及 BOOL 类型保持不变。

实现说明：
每次调用为一次 20 ms 扫描，无时间等待需求，不使用定时器。
工步：0 等待瓶子，1 清洗，2 灌装，3 封盖，4 包装，5 完成。
每扫描最多推进一个工步；确认按钮按当前工步的 TRUE 电平处理，
不缓存其他工步的确认，不要求未规定的上升沿。
清洗期间瓶子离开时保持工步 1，并忽略清洗确认。
finishedButton 在任何工步均优先复位；持续按下期间不启动新周期。
复位当拍全部输出为 FALSE；复位解除后若 bottleSensor 仍为 TRUE，
则按电平启动下一周期。

语义冲突及边界说明：
保留 C9 原文。若 C9 的时间 0 是首次调用前的初始化状态，
本实现以显式输出初始化满足该初态。
若 C9 的时间 0 是首次调用后的输出，则它与用户提供的
cycle 1 到瓶即启泵测试要求冲突，不能同时满足。
本次实现按已提供测试的首个执行扫描即启泵要求修改，
不声称满足将 C9 解释为首次调用后全部输出为 FALSE 的要求。

C3 的公式在 Filling_Valve 为 TRUE 时，其 W 的右操作数当拍已为 TRUE，
因此公式本身不能表达其注释所述的历史确认或确认信号保持要求。
保留原公式及注释；实现按 K1 和需求原文，通过工步记录已接受的确认，
不额外要求操作员在整个灌装期间持续按住 cleaningConfirmButton。

验证状态：
用户提供的旧版结果为 authoritative 编译 pass、fast 编译 fail，
逐周期测试仅通过 1/8；编译通过不代表功能正确。
当前对话没有可执行工具，无法在此运行用户提供的本地测试命令。
本次修改尚未重新编译或执行逐周期测试，不声称修复后全部通过。
*)

FUNCTION_BLOCK FB_P01
VAR_INPUT
    bottleSensor : BOOL;
    cleaningConfirmButton : BOOL;
    fillingConfirmButton : BOOL;
    cappingConfirmButton : BOOL;
    packingConfirmButton : BOOL;
    finishedButton : BOOL;
END_VAR
VAR_OUTPUT
    Pump_Motor : BOOL := FALSE;
    Filling_Valve : BOOL := FALSE;
    Capping_Machine : BOOL := FALSE;
    Packing_Machine : BOOL := FALSE;
    Completion_Light : BOOL := FALSE;
END_VAR
VAR
    processState : INT := 0;
END_VAR

(* 每扫描先清零输出，再依据更新后的唯一工步译码。 *)
Pump_Motor := FALSE;
Filling_Valve := FALSE;
Capping_Machine := FALSE;
Packing_Machine := FALSE;
Completion_Light := FALSE;

IF finishedButton THEN
    (* C1、K4：复位优先，禁止在同一扫描重新启动。 *)
    processState := 0;
ELSE
    CASE processState OF
        0:
            IF bottleSensor THEN
                processState := 1;
            END_IF;

        1:
            (* 瓶子不在位时停留在清洗工步，不接受完成确认。 *)
            IF bottleSensor AND cleaningConfirmButton THEN
                processState := 2;
            END_IF;

        2:
            IF fillingConfirmButton THEN
                processState := 3;
            END_IF;

        3:
            IF cappingConfirmButton THEN
                processState := 4;
            END_IF;

        4:
            IF packingConfirmButton THEN
                processState := 5;
            END_IF;

        5:
            (* 完成状态保持至 finishedButton 复位。 *)
            processState := 5;

    ELSE
        (* 内部状态异常时安全返回等待，不在当拍启动。 *)
        processState := 0;
    END_CASE;

    CASE processState OF
        1:
            Pump_Motor := bottleSensor;
        2:
            Filling_Valve := TRUE;
        3:
            Capping_Machine := TRUE;
        4:
            Packing_Machine := TRUE;
        5:
            Completion_Light := TRUE;
    END_CASE;
END_IF;

END_FUNCTION_BLOCK

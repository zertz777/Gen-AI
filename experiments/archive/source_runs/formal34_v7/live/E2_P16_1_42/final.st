(*
修改说明：
以显式状态机实现扫描控制，保持所有外部接口名称、方向和类型。
上电第一个扫描周期停止输送，第二个扫描周期开始允许启动。
每次左行后，后续十个扫描周期禁止右行。
启动时保存有效工艺序列；运行期间仍检查输入工艺是否合法。
错误状态锁存并停止输送，重新初始化功能块实例才能清除。
完成信号采用电平判定，且必须同时具有当前目标工位的到位信号。
一次启动按钮按下最多启动一件工件，释放按钮后允许再次启动。
相邻重复加工工位仍逐项等待完成条件，不删除或合并工步。
CASE 的各分支均包含有效语句，不使用仅含注释的空分支。
内部循环变量 checkIndex 使用 USINT，与 processLength 同类型，
避免快速编译器拒绝 INT 与 USINT 的直接比较。
循环范围为 1..8，循环结束递增后的值 9 也在 USINT 范围内。
无新增外部接口，无厂商扩展，无定时器库依赖。

边界解释与冲突报告：
C10 的公式 G[0,1] 按包含端点的零基扫描编号解释，
要求第 0、1 两个扫描周期停止输送。
但其文字说明为“上电首周期不输送”，且所提供测试结果在
cycle 1 期望 conveyorRight 为 TRUE。如果 cycle 1 对应第二次调用，
则该测试预期与 C10 的双周期字面解释存在冲突。
本实现保留原始公式，按文字说明及测试预期仅停止首次调用；
不声称满足 C10 的双周期字面解释。
C9 对每个左行扫描均适用，而不仅适用于左行上升沿。
换向等待优先于立即输送；等待期间保持工步和目标不变。
输入序列不合法时，包括违反末项为 5、前项为 2..4 的合同，
均进入内部错误状态。非活动数组元素不参与校验。
启动后有效序列使用启动时快照，避免输入变化造成工步乱序。

验证状态：
用户提供的上一版本结果：快速编译因比较类型不匹配而失败，
权威编译通过，逐周期测试 8 项通过 3 项。
本次仅修复已定位的比较类型错误，不改变状态机扫描行为。
失败日志未提供逐周期输入，无法确认功能失败的具体原因。
当前对话没有可执行工具，未运行本次修改后的编译或测试，
不声称本次修改已经编译通过或功能正确。
*)

(*
【必留：需求原文】
An automated production line consists of 5 workstations: numbered 1# to 5# from left to right. The 1# station is used for raw material loading, stations 2# to 4# are used for product processing, and the 5# station is used for finished product output and storage.
There is a motor in the production line, responsible for moving the product from one workstation to the next. Each workstation has a sensor (used to detect if the product has arrived).
Each product has a different sequence and number of processing steps, specified by the process sequence 'processSequence'. The processSequence is an array type, storing the sequence numbers of the workstations, and the system automatically sends the raw materials to the corresponding workstation for processing based on the station number.
Control requirements:
At the start of production, when the sensor at the 1# station (sensor1) detects the raw material, the start button at the 1# station (station1Start) is pressed. The system queries the first element of the process sequence 'processSequence', starts the conveyor to move the raw material to the corresponding workstation, and stops after delivery. Upon receiving the processing completion signal from the corresponding workstation (station2Complete to station4Complete), it continues to query the next element of the process sequence 'processSequence', determines the direction of the conveyor, and starts the conveyor (conveyorLeft, conveyorRight). This continues until the product is delivered to the 5# workstation.

processLength specifies the active sequence length, from 1 through 8, starting at processSequence[1]. The final active entry is output station 5; other active entries are processing stations 2 through 4. The caller supplies a sequence satisfying this contract.

中文摘要：柔性加工线：按工艺序列 processSequence 把工件依次送到指定工位加工，5 个工位、输送机左右互斥。

扫描周期：20 ms（全组统一，见 docs/tasks_note.md）
*)

(*
【必留：接口、初态、约束与数据告警】
{
  "task_id": "P16",
  "title": "Flexible Processing Control",
  "io_table": [
    {
      "direction": "IN",
      "name": "processLength",
      "data_type": "USINT",
      "description": "Active process-sequence length, 1..8; the final active entry must be station 5."
    },
    {
      "direction": "IN",
      "name": "sensor1",
      "data_type": "BOOL",
      "description": "Sensor at 1# station"
    },
    {
      "direction": "IN",
      "name": "sensor2",
      "data_type": "BOOL",
      "description": "Sensor at 2# station"
    },
    {
      "direction": "IN",
      "name": "sensor3",
      "data_type": "BOOL",
      "description": "Sensor at 3# station"
    },
    {
      "direction": "IN",
      "name": "sensor4",
      "data_type": "BOOL",
      "description": "Sensor at 4# station"
    },
    {
      "direction": "IN",
      "name": "sensor5",
      "data_type": "BOOL",
      "description": "Sensor at 5# station"
    },
    {
      "direction": "IN",
      "name": "station1Start",
      "data_type": "BOOL",
      "description": "Start button at 1# station"
    },
    {
      "direction": "IN",
      "name": "station2Complete",
      "data_type": "BOOL",
      "description": "Processing completion signal at 2# station"
    },
    {
      "direction": "IN",
      "name": "station3Complete",
      "data_type": "BOOL",
      "description": "Processing completion signal at 3# station"
    },
    {
      "direction": "IN",
      "name": "station4Complete",
      "data_type": "BOOL",
      "description": "Processing completion signal at 4# station"
    },
    {
      "direction": "IN",
      "name": "processSequence",
      "data_type": "ARRAY[1..8] OF USINT",
      "description": "Processing sequence"
    },
    {
      "direction": "OUT",
      "name": "conveyorLeft",
      "data_type": "BOOL",
      "description": "Conveyor turns left"
    },
    {
      "direction": "OUT",
      "name": "conveyorRight",
      "data_type": "BOOL",
      "description": "Conveyor turns right"
    }
  ],
  "initial_state": "conveyorLeft = FALSE；conveyorRight = FALSE；工步索引 = 0；各工位空闲。",
  "constraints": [
    "K1 每件工件的前 processLength 个工位号来自 processSequence，按数组顺序依次加工，不得跳过或乱序。",
    "K2 conveyorLeft 与 conveyorRight 互斥，任何时刻不得同时为 TRUE。",
    "K3 只有目标工位的到位传感器为 TRUE 且该工位加工完成信号有效时，才允许启动下一段输送。",
    "K4 processLength 超出数组范围或工位号不在 1—5 时置错误状态并停止输送。"
  ],
  "semantic_warnings": [],
  "warnings": [],
  "missing_fields": [],
  "dialect_requirements": [],
  "type_origins": {}
}
*)

(*
【必留：完整形式化规约；有界时序以扫描周期计】
# task: P16
# meta: hard / C 状态机与节拍
# spec: version 1.0, updated 2026-10-30, scan cycle 20 ms
# 条款号对齐任务书 3.4 的条款库 C1—C10；[a,b] 单位为扫描周期。

C4: G(!(conveyorLeft && conveyorRight))    -- 左右输送互斥（同一时刻只有一个方向）（K2）
C2: G(conveyorLeft -> !conveyorRight)    -- 左行的许可是右行未动作（K2）
C1: G(processLength == 0 -> X(!conveyorLeft && !conveyorRight))    -- 工艺长度为 0 时下一周期必须停止输送（空工艺不得启动）（K4）
C9: G(conveyorLeft -> G[0,10](!conveyorRight))    -- 左行开始后 200 ms 内不得切到右行（换向死区）（K2）
C10: G[0,1](!conveyorLeft && !conveyorRight)    -- 上电首周期不输送（初态）
*)

FUNCTION_BLOCK FB_P16
VAR_INPUT
    processLength : USINT;
    sensor1 : BOOL;
    sensor2 : BOOL;
    sensor3 : BOOL;
    sensor4 : BOOL;
    sensor5 : BOOL;
    station1Start : BOOL;
    station2Complete : BOOL;
    station3Complete : BOOL;
    station4Complete : BOOL;
    processSequence : ARRAY[1..8] OF USINT;
END_VAR
VAR_OUTPUT
    conveyorLeft : BOOL := FALSE;
    conveyorRight : BOOL := FALSE;
END_VAR
VAR
    (* 0：空闲；1：输送或等待换向；2：等待加工完成；3：错误。 *)
    controlState : USINT := 0;
    stepIndex : USINT := 0;
    activeLength : USINT := 0;
    activeSequence : ARRAY[1..8] OF USINT;

    currentStation : USINT := 1;
    targetStation : USINT := 0;

    startupScansRemaining : USINT := 1;
    rightInhibitScans : USINT := 0;

    startArmed : BOOL := TRUE;
    invalidInput : BOOL := FALSE;
    targetPresent : BOOL := FALSE;
    targetComplete : BOOL := FALSE;
    checkIndex : USINT := 0;
END_VAR

(* 每个扫描先关闭输出，随后仅在获准输送时置位一个方向。 *)
conveyorLeft := FALSE;
conveyorRight := FALSE;

(* 左行扫描将计数重置为 11。
   后续第 1..10 个扫描递减为 10..1，仍禁止右行；
   第 11 个扫描递减为 0，才允许右行。 *)
IF rightInhibitScans > 0 THEN
    rightInhibitScans := rightInhibitScans - 1;
END_IF;

IF NOT station1Start THEN
    startArmed := TRUE;
END_IF;

(* 不依赖短路求值保护数组下标。 *)
invalidInput := FALSE;

IF (processLength < 1) OR (processLength > 8) THEN
    invalidInput := TRUE;
ELSE
    FOR checkIndex := 1 TO 8 DO
        IF checkIndex <= processLength THEN
            IF (processSequence[checkIndex] < 1)
                OR (processSequence[checkIndex] > 5) THEN
                invalidInput := TRUE;
            END_IF;

            IF checkIndex < processLength THEN
                IF (processSequence[checkIndex] < 2)
                    OR (processSequence[checkIndex] > 4) THEN
                    invalidInput := TRUE;
                END_IF;
            ELSE
                IF processSequence[checkIndex] <> 5 THEN
                    invalidInput := TRUE;
                END_IF;
            END_IF;
        END_IF;
    END_FOR;
END_IF;

IF invalidInput THEN
    controlState := 3;
END_IF;

IF startupScansRemaining > 0 THEN
    (* 首次调用停止输送；之后允许响应启动条件。 *)
    startupScansRemaining := startupScansRemaining - 1;
ELSE
    CASE controlState OF
        0:
            IF startArmed AND station1Start AND sensor1 THEN
                activeLength := processLength;

                FOR checkIndex := 1 TO 8 DO
                    activeSequence[checkIndex] := processSequence[checkIndex];
                END_FOR;

                stepIndex := 1;
                currentStation := 1;
                targetStation := activeSequence[1];
                startArmed := FALSE;
                controlState := 1;
            END_IF;

        1:
            (* 输送与到位判断在下方统一执行。
               显式赋值避免编译器拒绝空 CASE 分支。 *)
            conveyorLeft := FALSE;
            conveyorRight := FALSE;

        2:
            targetPresent := FALSE;
            targetComplete := FALSE;

            CASE targetStation OF
                2:
                    targetPresent := sensor2;
                    targetComplete := station2Complete;
                3:
                    targetPresent := sensor3;
                    targetComplete := station3Complete;
                4:
                    targetPresent := sensor4;
                    targetComplete := station4Complete;
            ELSE
                controlState := 3;
            END_CASE;

            IF controlState = 2 THEN
                IF targetPresent AND targetComplete THEN
                    (* 当前工步完成后只推进一个数组位置。 *)
                    IF (stepIndex >= 1)
                        AND (stepIndex < activeLength)
                        AND (stepIndex < 8) THEN
                        currentStation := targetStation;
                        stepIndex := stepIndex + 1;
                        targetStation := activeSequence[stepIndex];
                        controlState := 1;
                    ELSE
                        controlState := 3;
                    END_IF;
                END_IF;
            END_IF;

        3:
            (* 错误锁存，输出保持关闭。 *)
            conveyorLeft := FALSE;
            conveyorRight := FALSE;

    ELSE
        controlState := 3;
    END_CASE;

    IF controlState = 1 THEN
        targetPresent := FALSE;

        CASE targetStation OF
            2:
                targetPresent := sensor2;
            3:
                targetPresent := sensor3;
            4:
                targetPresent := sensor4;
            5:
                targetPresent := sensor5;
        ELSE
            controlState := 3;
        END_CASE;

        IF controlState = 1 THEN
            IF targetPresent THEN
                (* 到位扫描立即停止，不受换向计数影响。 *)
                currentStation := targetStation;

                IF targetStation = 5 THEN
                    IF stepIndex = activeLength THEN
                        controlState := 0;
                        stepIndex := 0;
                        activeLength := 0;
                        targetStation := 0;
                    ELSE
                        controlState := 3;
                    END_IF;
                ELSE
                    controlState := 2;
                END_IF;
            ELSE
                IF targetStation < currentStation THEN
                    conveyorLeft := TRUE;
                    rightInhibitScans := 11;
                ELSIF targetStation > currentStation THEN
                    IF rightInhibitScans = 0 THEN
                        conveyorRight := TRUE;
                    END_IF;
                ELSE
                    (* 同工位的重复工步无需输送，但必须有到位信号。
                       信号缺失时停机等待，不猜测产品位置。 *)
                    conveyorLeft := FALSE;
                    conveyorRight := FALSE;
                END_IF;
            END_IF;
        END_IF;
    END_IF;
END_IF;

(* 防御性收尾：错误时强制关闭两个方向。 *)
IF controlState = 3 THEN
    conveyorLeft := FALSE;
    conveyorRight := FALSE;
END_IF;

END_FUNCTION_BLOCK

(*
【修改说明】
本次日志显示编译检查通过，但四个逐周期测试均在 cycle 1 失败：
DriveA_Run 期望 TRUE，实际 FALSE。
原因是此前增加了两个扫描周期的启动禁止逻辑。
本次删除 StartupScans 和 StartupInhibit，保留输出变量的初始值；
首次执行时，已复位、门关闭且无急停即允许两个区运行。
保持外部接口、复位沿检测、复位锁存、B 区延时和急停优先逻辑。
门打开的检测周期为延时起点；其后第 25 个扫描周期停止 B 区。
门开期间不能启动原本停止的 B 区；门关闭也不能绕过复位锁存。

【语义冲突与实现边界】
1. C10 要求最初两个采样周期驱动停止且无报警，但所提供测试
   要求 cycle 1 的 DriveA_Run 为 TRUE；若使用相同的输出采样
   时点，两者冲突。本实现按照所提供测试取消启动禁止逻辑，
   仅在功能块初始化时保持两区停止、无报警，不声称满足 C10。
   需求 4 要求门开或急停当周期报警，也与 C10 在初始危险输入
   下冲突。本实现优先危险报警，完整保留原始规约。
2. 接口没有启动按钮，也没有 B 区动作完成信号。
   ZoneAOccupied、ZoneBOccupied 的定义是区域内有人，不能暗中
   将其解释为启动按钮或动作完成信号。
   本实现不使用这两个输入推断动作完成，也不新增占用联锁；
   B 区采用 500 ms 上限停止，不实现缺少信号的提前完成检测。
   启动采用自动运行许可：已复位、门关闭且无急停时运行。
   故无法实现或验证独立的启动按钮行为。
3. 门关闭会立即停止尚在延时运行的 B 区，并等待有效复位沿；
   门开期间不接受复位，急停期间也不接受复位。
   若门关闭与复位上升沿在同一扫描被采样，则接受该复位。
4. 急停同样清除已复位标志，解除后需要新的有效复位沿。
5. C1b 的 F[0,1] 比文字的当周期停止宽松；
   本实现采用更严格的当周期停止。
   形式化条款旁的 K 编号与约束列表存在对应差异，原文保留。
6. 用户提供的日志证明此前版本通过编译检查，但逐周期测试失败。
   当前会话无可调用的执行工具，无法运行所提供的测试命令。
   本次修改尚未重新编译或测试，不声称新版本功能已验证，
   也不能从首个失败点推断其余周期均正确。

【必留：需求原文】
设备分 A、B 两个危险区，安全门打开时需要分级停机：A 区（靠近门）立即停，B 区（远端）允许走完当前动作再停。

控制要求：
1. DoorSwitch = TRUE（门打开）时，DriveA_Run 立即变为 FALSE；DriveB_Run 继续保持，直到 500 ms 延时到或 B 区动作完成。
2. 门关闭（DoorSwitch = FALSE）后，必须由 ResetBtn 的上升沿确认，才允许重新启动两个区。
3. EStop_NC = FALSE 时 A、B 两区同时立即停止，不受 500 ms 延时影响。
4. 门打开或急停期间 AlarmLamp = TRUE。
5. 未复位前按启动按钮无效（Status 保持 16#8301 待复位）。
6. Status：16#0000 正常、16#8301 待复位、16#8302 门开、16#8303 急停。

扫描周期：20 ms（全组统一，见 docs/tasks_note.md）

【必留：接口、初态、约束与数据告警】
{
  "task_id": "S03",
  "title": "安全门分级停机",
  "io_table": [
    {
      "direction": "IN",
      "name": "DoorSwitch",
      "data_type": "BOOL",
      "description": "安全门，TRUE = 门开"
    },
    {
      "direction": "IN",
      "name": "ZoneAOccupied",
      "data_type": "BOOL",
      "description": "A 区内有人"
    },
    {
      "direction": "IN",
      "name": "ZoneBOccupied",
      "data_type": "BOOL",
      "description": "B 区内有人"
    },
    {
      "direction": "IN",
      "name": "ResetBtn",
      "data_type": "BOOL",
      "description": "复位按钮（上升沿有效）"
    },
    {
      "direction": "IN",
      "name": "EStop_NC",
      "data_type": "BOOL",
      "description": "急停常闭触点，TRUE = 正常"
    },
    {
      "direction": "OUT",
      "name": "DriveA_Run",
      "data_type": "BOOL",
      "description": "A 区驱动运行"
    },
    {
      "direction": "OUT",
      "name": "DriveB_Run",
      "data_type": "BOOL",
      "description": "B 区驱动运行"
    },
    {
      "direction": "OUT",
      "name": "AlarmLamp",
      "data_type": "BOOL",
      "description": "报警灯"
    },
    {
      "direction": "OUT",
      "name": "Status",
      "data_type": "WORD",
      "description": "状态码"
    }
  ],
  "initial_state": "DriveA_Run = FALSE；DriveB_Run = FALSE；AlarmLamp = FALSE；Status = 16#0000；延时计时器 = 0；已复位标志 = TRUE。",
  "constraints": [
    "K1 DoorSwitch 由 FALSE 变 TRUE 时，DriveA_Run 必须在同一周期内变为 FALSE。",
    "K2 DriveB_Run 在门开后最多再保持 500 ms（或提前因动作完成而停）。",
    "K3 门关闭后必须经过 ResetBtn 上升沿，两个区才允许重新启动。",
    "K4 EStop_NC = FALSE 时两个区都立即停止，且优先于 500 ms 延时。"
  ],
  "semantic_warnings": [],
  "warnings": [],
  "missing_fields": [],
  "dialect_requirements": [],
  "type_origins": {}
}

【必留：完整形式化规约；有界时序以扫描周期计】
# task: S03
# meta: medium / A 开关量联锁
# spec: version 1.0, updated 2026-10-30, scan cycle 20 ms
# 条款号对齐任务书 3.4 的条款库 C1—C10；[a,b] 单位为扫描周期。

C1: G(!EStop_NC -> (!DriveA_Run && !DriveB_Run))    -- 急停当周期两区都停（优先于分级延时）（K3）
C1b: G(DoorSwitch -> F[0,1](!DriveA_Run))    -- 门打开后 A 区当周期必须停（分级停机的高等级侧）（K1）
C5: G(DoorSwitch -> F[0,25](!DriveB_Run))    -- 门打开后 B 区 500 ms 内必须停（低等级侧允许走完当前动作）（K2）
C2: G(DriveA_Run -> (!DoorSwitch && EStop_NC))    -- A 区运行的许可：门关闭且无急停（K3）
C6: G(AlarmLamp -> (AlarmLamp W !DoorSwitch))    -- 门关闭后报警才允许撤销（不得随门抖动闪烁）（K4）
C10: G[0,1](!DriveA_Run && !DriveB_Run && !AlarmLamp)    -- 上电首周期两区都不运行、无报警（初态）
*)

FUNCTION_BLOCK FB_S03
VAR_INPUT
    DoorSwitch : BOOL;
    ZoneAOccupied : BOOL;
    ZoneBOccupied : BOOL;
    ResetBtn : BOOL;
    EStop_NC : BOOL;
END_VAR
VAR_OUTPUT
    DriveA_Run : BOOL := FALSE;
    DriveB_Run : BOOL := FALSE;
    AlarmLamp : BOOL := FALSE;
    Status : WORD := WORD#16#0000;
END_VAR
VAR
    ResetConfirmed : BOOL := TRUE;
    PreviousResetBtn : BOOL := FALSE;
    PreviousDoorSwitch : BOOL := FALSE;
    ResetRisingEdge : BOOL := FALSE;
    DoorRisingEdge : BOOL := FALSE;
    BStopPending : BOOL := FALSE;
    BDelayScans : UINT := UINT#0;
END_VAR

(* 先采样边沿；包括危险期间的按钮变化，避免解除危险后产生假边沿。 *)
ResetRisingEdge := ResetBtn AND NOT PreviousResetBtn;
DoorRisingEdge := DoorSwitch AND NOT PreviousDoorSwitch;

(* 急停、门开均锁存待复位；有效复位必须发生在安全条件下。 *)
IF NOT EStop_NC THEN
    ResetConfirmed := FALSE;
ELSIF DoorSwitch THEN
    ResetConfirmed := FALSE;
ELSIF ResetRisingEdge THEN
    ResetConfirmed := TRUE;
END_IF;

(* 急停拥有最高优先级，不能保留或恢复此前的 B 区延时。 *)
IF NOT EStop_NC THEN
    DriveA_Run := FALSE;
    DriveB_Run := FALSE;
    BStopPending := FALSE;
    BDelayScans := UINT#0;

ELSIF DoorSwitch THEN
    DriveA_Run := FALSE;

    IF DoorRisingEdge THEN
        (* 仅允许门打开之前已在运行的 B 区继续当前动作。 *)
        BStopPending := DriveB_Run;
        BDelayScans := UINT#0;
    ELSIF BStopPending THEN
        IF BDelayScans < UINT#25 THEN
            BDelayScans := BDelayScans + UINT#1;
        END_IF;
    END_IF;

    IF BDelayScans >= UINT#25 THEN
        BStopPending := FALSE;
    END_IF;

    DriveB_Run := BStopPending;

ELSE
    (* 门关闭取消延时，但不能自动清除待复位状态。 *)
    BStopPending := FALSE;
    BDelayScans := UINT#0;
    DriveA_Run := ResetConfirmed;
    DriveB_Run := ResetConfirmed;
END_IF;

(* 危险报警优先于存在冲突的上电无报警条款。 *)
AlarmLamp := DoorSwitch OR NOT EStop_NC;

(* 状态优先级：急停 > 门开 > 待复位 > 正常。 *)
IF NOT EStop_NC THEN
    Status := WORD#16#8303;
ELSIF DoorSwitch THEN
    Status := WORD#16#8302;
ELSIF NOT ResetConfirmed THEN
    Status := WORD#16#8301;
ELSE
    Status := WORD#16#0000;
END_IF;

PreviousResetBtn := ResetBtn;
PreviousDoorSwitch := DoorSwitch;

END_FUNCTION_BLOCK

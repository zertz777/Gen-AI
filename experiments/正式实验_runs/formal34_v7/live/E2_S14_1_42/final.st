(*
【必留：需求原文】
液压站按系统压力自动投切泵组与卸荷阀，要求不频繁启停、越界立即保护。

控制要求：
1. PumpEnable = TRUE 且 AlarmLamp = FALSE 时按压力分级加载：
   Pressure < 120.0 bar → LowPump = TRUE。
2. 高压泵投入：Pressure >= 140.0 bar → HighPump = TRUE。
3. 滞回：HighPump 投入后，只有 Pressure < 100.0 bar 才断开；
   100.0 <= Pressure < 140.0 区间保持原状态，不得反复启停。
4. 卸荷：Pressure > 160.0 bar → ReliefValve = TRUE 且
   LowPump、HighPump 同时 FALSE；
   Pressure < 150.0 bar 后 ReliefValve = FALSE。
5. 卸荷阀与泵互斥：ReliefValve 与 LowPump/HighPump 不得同时为 TRUE。
6. 传感器越界：Pressure < 0.5 bar 或 Pressure > 250.0 bar
   视为断线/短路 → 两泵 FALSE、AlarmLamp = TRUE、Status = 16#8D01；
   故障消失后需 ResetBtn 上升沿复位（复位前 Status = 16#8D02）。
7. Status：16#0000 正常、16#8D01 传感器故障、16#8D02 待复位。

扫描周期：20 ms（全组统一，见 docs/tasks_note.md）

【必留：接口、初态、约束与数据告警】
{
  "task_id": "S14",
  "title": "液压站压力分级加载与卸荷",
  "io_table": [
    {
      "direction": "IN",
      "name": "Pressure",
      "data_type": "REAL",
      "description": "系统压力，单位 bar"
    },
    {
      "direction": "IN",
      "name": "PumpEnable",
      "data_type": "BOOL",
      "description": "允许加载"
    },
    {
      "direction": "IN",
      "name": "ResetBtn",
      "data_type": "BOOL",
      "description": "复位按钮，上升沿有效"
    },
    {
      "direction": "OUT",
      "name": "LowPump",
      "data_type": "BOOL",
      "description": "低压泵"
    },
    {
      "direction": "OUT",
      "name": "HighPump",
      "data_type": "BOOL",
      "description": "高压泵"
    },
    {
      "direction": "OUT",
      "name": "ReliefValve",
      "data_type": "BOOL",
      "description": "卸荷阀"
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
  "initial_state": "LowPump = HighPump = ReliefValve = AlarmLamp = FALSE；Status = 16#0000；ResetBtnLast = FALSE；HighPumpLatched = FALSE。",
  "constraints": [
    "K1 Pressure > 160.0 bar 时必须在同一周期卸荷并停泵。",
    "K2 Pressure < 120.0 bar 且 PumpEnable 时必须加载低压泵（允许一个扫描周期延迟）。",
    "K3 高压泵在 100.0—140.0 bar 之间保持原状态，构成 40 bar 滞回带。",
    "K4 传感器越界（< 0.5 或 > 250.0 bar）必须在 200 ms 内停机报警，Status = 16#8D01。",
    "K5 卸荷阀与任一台泵不得同时为 TRUE。"
  ],
  "semantic_warnings": [],
  "warnings": [],
  "missing_fields": [],
  "dialect_requirements": [],
  "type_origins": {}
}

【必留：完整形式化规约；有界时序以扫描周期计】
# task: S14
# meta: medium / B 模拟量处理
# spec: version 1.0, updated 2026-10-30, scan cycle 20 ms
# 条款号对齐任务书 3.4 的条款库 C1—C10；[a,b] 单位为扫描周期。

C1: G(Pressure > 160.0 -> X(!LowPump && !HighPump && ReliefValve))    -- 过压当周期卸荷并停泵（K1）
C2: G(Pressure < 120.0 && PumpEnable && !AlarmLamp -> X(LowPump))    -- 低压加载条件成立时一周期内投泵（K2）
C4: G(!(ReliefValve && LowPump) && !(ReliefValve && HighPump))    -- 卸荷阀与泵不得同时为 TRUE（K5）
C6: G((Pressure < 0.5 || Pressure > 250.0) -> F[0,10] AlarmLamp)    -- 传感器越界 200 ms 内报警（10 周期）（K4）
C7: G(HighPump && Pressure >= 100.0 && Pressure < 140.0 -> X(HighPump))    -- 滞回带内保持高压泵状态，不抖动（K3）
C10: G[0,1](!LowPump && !HighPump && !ReliefValve && !AlarmLamp && Status == 16#0000)    -- 上电首周期不加载、无报警（初态）

【修改说明与语义冲突报告】
以显式初值、故障锁存、复位边沿和高压泵滞回替换占位实现。
每次调用直接计算本次扫描输出，不使用定时器或厂商扩展。

原文与形式化规约存在以下冲突，原条款保留，不宣称全部满足：
1. C10 要求初始扫描输出保持关闭且不报警；若初始压力大于
   160.0，则与 K1 同周期卸荷冲突；若初始压力小于 120.0 且允许
   加载，则 C10 的 [0,1] 与 C2 下一状态加载也存在冲突。
   本实现仅在调用前提供所列初态，首次调用立即响应输入，
   不强制维持 C10 的整个区间。
2. K2 未排除故障与待复位状态；C2 未排除本次新检测到的故障。
   例如 Pressure = 0.0、PumpEnable = TRUE 时，加载要求与停泵
   保护冲突。本实现优先停泵报警。
3. “高压泵只有 Pressure < 100.0 才断开”与过压卸荷、故障停泵
   冲突；C7 也未排除 PumpEnable 撤销或报警保护。
   本实现在允许加载且无保护时保持滞回；禁止加载、报警或卸荷
   均强制停泵并清除高压泵锁存。
4. C1、C2、C7 使用 X 描述下一状态，K1 却明确要求同周期动作。
   本实现采用本次输入到本次扫描结束输出的执行语义；
   不额外延迟保护，不能未经时序采样定义确认而声称满足全部 LTL。

【边界选择】
Pressure = 0.5 或 250.0 不构成传感器越界。
Pressure = 160.0 不新触发卸荷；已卸荷时保持至 Pressure < 150.0。
Pressure = 150.0 保持卸荷阀原状态。
Pressure = 120.0 不加载低压泵。
Pressure = 140.0 在允许加载且无保护时投入高压泵。
Pressure = 100.0 保持高压泵锁存。
复位只在传感器恢复正常且检测到新的上升沿时有效；
故障期间的复位边沿不缓存。
复位成功的同一扫描允许按压力重新加载。
卸荷阀按压力独立运行，不受 PumpEnable 或报警锁存禁止，
因此 Pressure > 250.0 时仍卸荷，同时停泵并报警。

【验证状态】
当前对话未提供可执行工具、编译 profile 或已配置测试命令，
未运行编译与逐周期测试，不声称编译或功能已经验证。
*)

FUNCTION_BLOCK FB_S14
VAR_INPUT
    Pressure : REAL;
    PumpEnable : BOOL;
    ResetBtn : BOOL;
END_VAR
VAR_OUTPUT
    LowPump : BOOL := FALSE;
    HighPump : BOOL := FALSE;
    ReliefValve : BOOL := FALSE;
    AlarmLamp : BOOL := FALSE;
    Status : WORD := WORD#16#0000;
END_VAR
VAR
    ResetBtnLast : BOOL := FALSE;
    ResetRising : BOOL := FALSE;
    HighPumpLatched : BOOL := FALSE;
    ReliefValveLatched : BOOL := FALSE;
    FaultLatched : BOOL := FALSE;
    SensorFault : BOOL := FALSE;
END_VAR

(* 每扫描采集边沿；故障期间的边沿不会延后用于复位。 *)
ResetRising := ResetBtn AND NOT ResetBtnLast;
ResetBtnLast := ResetBtn;

SensorFault := (Pressure < 0.5) OR (Pressure > 250.0);

(* 当前故障优先于复位请求。 *)
IF SensorFault THEN
    FaultLatched := TRUE;
ELSIF FaultLatched AND ResetRising THEN
    FaultLatched := FALSE;
END_IF;

AlarmLamp := FaultLatched;

IF SensorFault THEN
    Status := WORD#16#8D01;
ELSIF FaultLatched THEN
    Status := WORD#16#8D02;
ELSE
    Status := WORD#16#0000;
END_IF;

(* 卸荷阀具有 160/150 bar 滞回，过压立即动作。 *)
IF Pressure > 160.0 THEN
    ReliefValveLatched := TRUE;
ELSIF Pressure < 150.0 THEN
    ReliefValveLatched := FALSE;
END_IF;

ReliefValve := ReliefValveLatched;

(* 默认停泵；仅在所有加载许可成立时计算分级加载。 *)
LowPump := FALSE;
HighPump := FALSE;

IF (NOT PumpEnable) OR AlarmLamp OR ReliefValve THEN
    HighPumpLatched := FALSE;
ELSE
    LowPump := Pressure < 120.0;

    IF Pressure >= 140.0 THEN
        HighPumpLatched := TRUE;
    ELSIF Pressure < 100.0 THEN
        HighPumpLatched := FALSE;
    END_IF;

    HighPump := HighPumpLatched;
END_IF;

END_FUNCTION_BLOCK

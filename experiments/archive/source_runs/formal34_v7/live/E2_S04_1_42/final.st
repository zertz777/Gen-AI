(*
【需求原文】
称重传感器长时间运行会出现零点漂移，需要在空秤时重新标定零点。

控制要求：
1. ZeroBtn 的上升沿把当前 RawWeight 采样为零点 ZeroOffset，同时清 DriftAlarm。
2. CompensatedWeight = (RawWeight - ZeroOffset) * 0.01（单位 kg，0.01 为标定系数），每个扫描周期更新。
3. 当 (RawWeight - ZeroOffset) 的绝对值超过 200（即 2 kg）时置 DriftAlarm = TRUE；回到 ±150 以内才复位（滞回）。
4. 上电时 ZeroOffset = 0，DriftAlarm = FALSE。
5. Status：16#0000 正常、16#8401 零点漂移、16#8402 采样值超量程（RawWeight 超出 -32768..32767 的可用段）。

扫描周期：20 ms（全组统一，见 docs/tasks_note.md）

【接口、初态、约束与数据告警】
{
  "task_id": "S04",
  "title": "称重零点漂移补偿",
  "io_table": [
    {
      "direction": "IN",
      "name": "RawWeight",
      "data_type": "INT",
      "description": "称重传感器原始值"
    },
    {
      "direction": "IN",
      "name": "ZeroBtn",
      "data_type": "BOOL",
      "description": "零点标定按钮（上升沿有效）"
    },
    {
      "direction": "IN",
      "name": "CalibWeight",
      "data_type": "REAL",
      "description": "标准砝码重量（kg），仅作显示"
    },
    {
      "direction": "OUT",
      "name": "CompensatedWeight",
      "data_type": "REAL",
      "description": "补偿后的重量（kg）"
    },
    {
      "direction": "OUT",
      "name": "ZeroOffset",
      "data_type": "INT",
      "description": "当前零点原始值"
    },
    {
      "direction": "OUT",
      "name": "DriftAlarm",
      "data_type": "BOOL",
      "description": "零点漂移报警"
    },
    {
      "direction": "OUT",
      "name": "Status",
      "data_type": "WORD",
      "description": "状态码"
    }
  ],
  "initial_state": "ZeroOffset = 0；CompensatedWeight = 0.0；DriftAlarm = FALSE；Status = 16#0000；ZeroBtnLast = FALSE。",
  "constraints": [
    "K1 ZeroOffset 只在 ZeroBtn 上升沿更新，按住或松开时保持不变。",
    "K2 CompensatedWeight 每周期按 (RawWeight - ZeroOffset) * 0.01 计算，不使用上一周期的结果。",
    "K3 漂移判据带 50 单位滞回：超过 ±200 置位，回到 ±150 内复位。",
    "K4 上电后未标定前 ZeroOffset 必须为 0，不得沿用断电前的值。"
  ],
  "semantic_warnings": [],
  "warnings": [],
  "missing_fields": [],
  "dialect_requirements": [],
  "type_origins": {}
}

【完整形式化规约；有界时序以扫描周期计】
# task: S04
# meta: medium / B 模拟量与数据处理
# spec: version 1.0, updated 2026-10-30, scan cycle 20 ms
# 条款号对齐任务书 3.4 的条款库 C1—C10；[a,b] 单位为扫描周期。
#
# 命题映射（I/O 名 -> 派生命题）：
# alias: zeroDelta := RawWeight - ZeroOffset
# alias: driftOut := RawWeight - ZeroOffset >= 200 || ZeroOffset - RawWeight >= 200
# alias: driftBack := RawWeight - ZeroOffset <= 150 && ZeroOffset - RawWeight <= 150
#
# note: 称重补偿属模拟量处理，题目未设急停；信号断线/失效的降级由 tests/cases/S04.csv 覆盖，规约层只约束换算与滞回。

C4: G(CompensatedWeight == (RawWeight - ZeroOffset) * 0.01)    -- 输出必须等于换算式（不得沿用上一周期的结果）（K2）
C2: G(DriftAlarm -> driftOut)    -- 报警的前提是偏差确实超限（不得空报）（K3）
C6: G(DriftAlarm -> (DriftAlarm W driftBack))    -- 偏差回落到 ±150 以内才允许撤警（滞回保持）（K3）
C7: G(DriftAlarm && driftBack -> X(!DriftAlarm))    -- 偏差回到 ±150 死区内就必须下一周期撤报（不得滞留）（K3）
C10: G[0,1](ZeroOffset == 0 && !DriftAlarm && CompensatedWeight == 0.0)    -- 上电首周期零点为 0、无报警（K4）

【本次编译修复】
需要修改声明：提供的权威编译结果表明，当前编译 profile
不接受 VAR_OUTPUT NON_RETAIN 和 VAR NON_RETAIN 的写法，
导致各声明块的首个变量未被正确解析，进而产生未声明变量、
无效赋值目标和 BOOL 表达式等连带错误。
本次改为骨架使用的 VAR_OUTPUT 和 VAR，保留显式初值，
不修改接口名称、方向、类型或扫描逻辑，不引入厂商扩展。

普通变量声明不单独保证运行时的断电重初始化行为。
部署时必须确认 FB 实例不处于 RETAIN/PERSISTENT 存储中，
并确认上电时执行声明初值初始化，以满足 K4。
不能通过每扫描重置 ZeroOffset 代替启动初始化，否则违反 K1。

已收到测试命令及旧版失败日志，但当前对话没有可执行工具，
无法在此运行该 Windows 命令。修改版尚未经过真实编译器和
逐周期测试验证；fast pass 不代表权威编译或功能正确。

【未消除的语义冲突】
CalibWeight 仅作显示，不参与标定系数计算。

1. 原文要求绝对偏差严格超过 200 才置位；driftOut 使用大于等于
   200，边界不一致。本实现采用原文的严格大于 200。
2. C2 禁止在绝对偏差小于 200 时报警，但 C6 和 K3 要求已经置位
   的报警在 150 到 200 之间保持。两者不能对所有输入序列同时成立。
   本实现保留 K3 的滞回：绝对偏差小于等于 150 当周期复位，
   大于 150 且小于等于 200 保持上一周期报警。
3. C10 若约束调用后的首两个扫描输出，则与非零输入下的 C4、
   超限报警以及首扫描 ZeroBtn 上升沿采样存在冲突。
   本实现将给定初态用于首次调用之前，首扫描立即执行采样、
   换算和报警逻辑，不跳过扫描。
4. RawWeight 的 INT 接口不能表示超出 -32768 到 32767 的输入。
   保留 16#8402 的范围判断及其状态优先级，但该分支对合法 INT
   输入不可达；接口外发生的截断或转换错误无法由本块检测。
*)

FUNCTION_BLOCK FB_S04
VAR_INPUT
    RawWeight : INT;
    ZeroBtn : BOOL;
    CalibWeight : REAL;
END_VAR
VAR_OUTPUT
    CompensatedWeight : REAL := REAL#0.0;
    ZeroOffset : INT := INT#0;
    DriftAlarm : BOOL := FALSE;
    Status : WORD := WORD#16#0000;
END_VAR
VAR
    ZeroBtnLast : BOOL := FALSE;
    RawValue : DINT := DINT#0;
    ZeroDelta : DINT := DINT#0;
END_VAR

(* 首扫描输入为 TRUE 时，也按上升沿执行零点采样。 *)
IF ZeroBtn AND NOT ZeroBtnLast THEN
    ZeroOffset := RawWeight;
    DriftAlarm := FALSE;
END_IF;
ZeroBtnLast := ZeroBtn;

(* 先提升至 DINT 再相减，避免两个 INT 极值相减溢出。 *)
RawValue := INT_TO_DINT(RawWeight);
ZeroDelta := RawValue - INT_TO_DINT(ZeroOffset);

(* 使用本扫描采样后的零点计算重量。 *)
CompensatedWeight := DINT_TO_REAL(ZeroDelta) * REAL#0.01;

(* 严格超过 200 置位；回到闭区间 [-150, 150] 复位。 *)
IF (ZeroDelta > DINT#200) OR (ZeroDelta < DINT#-200) THEN
    DriftAlarm := TRUE;
ELSIF (ZeroDelta >= DINT#-150) AND (ZeroDelta <= DINT#150) THEN
    DriftAlarm := FALSE;
END_IF;

(* 超量程状态优先；合法 INT 输入不会进入该分支。 *)
IF (RawValue < DINT#-32768) OR (RawValue > DINT#32767) THEN
    Status := WORD#16#8402;
ELSIF DriftAlarm THEN
    Status := WORD#16#8401;
ELSE
    Status := WORD#16#0000;
END_IF;

END_FUNCTION_BLOCK

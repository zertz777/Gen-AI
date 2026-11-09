(*
【必留：需求原文】
泵站出口装有脉冲流量计，每个脉冲代表 0.5 L。需要同时维护累计总量与当班流量。

控制要求：
1. FlowPulse 的每个上升沿使 PulseCount 加 1，TotalVolume 与 ShiftVolume 各加 0.5 L。
2. ShiftReset 的上升沿把 ShiftVolume 清 0、PulseCount 清 0，但 TotalVolume 必须保持不变。
3. TotalVolume 达到 1000000.0 L 时不再增加，置 OverflowFlag = TRUE；清零只能由维护流程完成（本题不提供入口，仅置位）。
4. FlowPulse 为高频脉冲，同一扫描周期内最多计一个脉冲（20 ms 周期内不允许丢脉冲的假设不成立时，以 Status 报 16#8501）。
5. 上电时 PulseCount = 0、TotalVolume = 0.0、ShiftVolume = 0.0、OverflowFlag = FALSE。
6. Status：16#0000 正常、16#8501 脉冲过快、16#8502 总量溢出。

扫描周期：20 ms（全组统一，见 docs/tasks_note.md）

【必留：接口、初态、约束与数据告警】
{
  "task_id": "S05",
  "title": "泵站流量累计与班次清零",
  "io_table": [
    {
      "direction": "IN",
      "name": "FlowPulse",
      "data_type": "BOOL",
      "description": "流量计脉冲"
    },
    {
      "direction": "IN",
      "name": "ShiftReset",
      "data_type": "BOOL",
      "description": "班次清零（上升沿有效）"
    },
    {
      "direction": "IN",
      "name": "CycleTime",
      "data_type": "TIME",
      "description": "扫描周期，用于判断脉冲频率"
    },
    {
      "direction": "OUT",
      "name": "TotalVolume",
      "data_type": "LREAL",
      "description": "累计总量（L）"
    },
    {
      "direction": "OUT",
      "name": "ShiftVolume",
      "data_type": "LREAL",
      "description": "当班流量（L）"
    },
    {
      "direction": "OUT",
      "name": "PulseCount",
      "data_type": "UDINT",
      "description": "当班脉冲数"
    },
    {
      "direction": "OUT",
      "name": "OverflowFlag",
      "data_type": "BOOL",
      "description": "总量溢出标志"
    },
    {
      "direction": "OUT",
      "name": "Status",
      "data_type": "WORD",
      "description": "状态码"
    }
  ],
  "initial_state": "PulseCount = 0；TotalVolume = 0.0；ShiftVolume = 0.0；OverflowFlag = FALSE；Status = 16#0000；FlowPulseLast = FALSE；ShiftResetLast = FALSE。",
  "constraints": [
    "K1 只在 FlowPulse 的上升沿累加，不得按电平累加。",
    "K2 ShiftReset 上升沿清 ShiftVolume 与 PulseCount，TotalVolume 严格不减。",
    "K3 TotalVolume 达到 1000000.0 后保持不再增长，并置 OverflowFlag。",
    "K4 单个扫描周期内检测到两次以上脉冲上升沿时置 Status = 16#8501，本周期只计 1 个。"
  ],
  "semantic_warnings": [],
  "warnings": [],
  "missing_fields": [],
  "dialect_requirements": [],
  "type_origins": {}
}

【必留：完整形式化规约；有界时序以扫描周期计】
# task: S05
# meta: hard / B 模拟量与数据处理
# spec: version 1.0, updated 2026-10-30, scan cycle 20 ms
# 条款号对齐任务书 3.4 的条款库 C1—C10；[a,b] 单位为扫描周期。

C1: G(OverflowFlag -> TotalVolume <= 1000000.0)    -- 溢出标志置位后总量不得继续增长（也不得回绕）（K3）
C2: G(TotalVolume >= 0.0 && ShiftVolume >= 0.0)    -- 两个累计量都不得为负（单向累计）（K1）
C8: G(TotalVolume >= 1000000.0 -> X(OverflowFlag))    -- 达到上限后下一周期必须置溢出标志（K3）
C8b: G(OverflowFlag -> X(OverflowFlag))    -- 溢出标志一旦置位就永久保持（不自动清除）（K3）
C6: G(ShiftVolume <= TotalVolume)    -- 当班流量不得超过累计总量（班次清零不影响总量）（K2）
C10: G[0,1](TotalVolume == 0.0 && ShiftVolume == 0.0 && !OverflowFlag)    -- 上电首周期两个累计量为 0、无溢出（初态）
*)

(*
修改说明：
以显式初值、扫描间保存的输入电平和上升沿逻辑替换占位 RETURN。
总量限幅，溢出标志锁存；班次清零不修改总量。
同一扫描同时出现两个上升沿时，总量仍计入该脉冲，
班次清零最后执行，班次输出为零；这属于边界优先级选择。

保留并报告的冲突与不可实现条件：
1. 每次调用只能观察 FlowPulse 的一个 BOOL 样本。
   扫描间发生零次、两次或更多次上升沿可能得到完全相同的样本。
   CycleTime 仅提供扫描周期，不能提供扫描内脉冲次数。
   因此现有接口无法实现 K4 的真实多脉冲检测及可靠的 16#8501。
   本实现不伪造检测结果，不把 CycleTime 偏离 20 ms 等同于脉冲过快；
   CycleTime 保留原接口，但不参与无法成立的频率判断。
   窄脉冲和扫描间多脉冲仍可能丢失，不能宣称满足要求 4。

2. 总量封顶后继续按要求 1 增加 ShiftVolume，最终可能违反 C6。
   若同时停止当班流量累计，则会违反要求 1。
   本实现保留要求 1 对当班流量的累计行为，并报告 C6 不能普遍成立，
   不通过暗中限幅 ShiftVolume 掩盖该冲突。

3. 若 C10 的 [0,1] 指前两个调用结束后的输出均为零，
   则它与这两个调用中任意上升沿立即累计的要求冲突。
   本实现保证调用前的声明初值，并从第一次调用开始正常计数；
   不通过忽略启动脉冲宣称满足上述 C10 解读。

4. UDINT 无法无限表示每个上升沿都加 1 的当班脉冲数。
   达到 UDINT 最大值后采用饱和，避免算术溢出及隐式回绕。
   此边界不满足无限累计的字面要求；题面没有提供对应状态码。
   LREAL 的有限精度也不支持无限次严格增加 0.5 L。

验证说明：
当前对话没有可执行工具、编译 profile 或已配置测试命令的访问入口，
未运行编译或逐周期测试，不声称已验证编译或功能正确。
上述冲突意味着无法在给定接口下完整满足全部需求与形式化规约。
*)

FUNCTION_BLOCK FB_S05
VAR_INPUT
    FlowPulse : BOOL;
    ShiftReset : BOOL;
    CycleTime : TIME;
END_VAR
VAR_OUTPUT
    TotalVolume : LREAL := LREAL#0.0;
    ShiftVolume : LREAL := LREAL#0.0;
    PulseCount : UDINT := UDINT#0;
    OverflowFlag : BOOL := FALSE;
    Status : WORD := WORD#16#0000;
END_VAR
VAR
    FlowPulseLast : BOOL := FALSE;
    ShiftResetLast : BOOL := FALSE;
    FlowPulseRise : BOOL := FALSE;
    ShiftResetRise : BOOL := FALSE;
END_VAR

(* 每次调用仅对本次输入样本进行一次上升沿检测。 *)
FlowPulseRise := FlowPulse AND NOT FlowPulseLast;
ShiftResetRise := ShiftReset AND NOT ShiftResetLast;

IF FlowPulseRise THEN
    (* 避免 UDINT 达到表示上限后回绕。 *)
    IF PulseCount < UDINT#4294967295 THEN
        PulseCount := PulseCount + UDINT#1;
    END_IF;

    (* 总量达到上限后仍按需求累计当班流量，相关 C6 冲突见上。 *)
    ShiftVolume := ShiftVolume + LREAL#0.5;

    IF NOT OverflowFlag THEN
        IF TotalVolume < LREAL#1000000.0 THEN
            TotalVolume := TotalVolume + LREAL#0.5;
        END_IF;
    END_IF;
END_IF;

(* 达到上限的同一次调用即置位；本接口没有解除锁存的入口。 *)
IF TotalVolume >= LREAL#1000000.0 THEN
    TotalVolume := LREAL#1000000.0;
    OverflowFlag := TRUE;
END_IF;

(* 班次清零优先于同一扫描的班次累计，但不撤销总量累计。 *)
IF ShiftResetRise THEN
    ShiftVolume := LREAL#0.0;
    PulseCount := UDINT#0;
END_IF;

(* 16#0000 仅表示没有可报告的总量溢出，不证明物理脉冲未丢失。 *)
IF OverflowFlag THEN
    Status := WORD#16#8502;
ELSE
    Status := WORD#16#0000;
END_IF;

(* 每次调用均更新历史电平，包括清零与溢出期间。 *)
FlowPulseLast := FlowPulse;
ShiftResetLast := ShiftReset;

END_FUNCTION_BLOCK

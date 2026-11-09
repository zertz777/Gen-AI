(*
【必留：需求原文】
Control a wastewater-treatment aeration blower with a low-dissolved-oxygen demand, a 5-second start delay, emergency-stop priority and start-cycle counting.

1. Start delay timing when both DO_LOW and AERATION_E_STOP_NC are TRUE. Allow BLOWER_RUN to become TRUE only after these conditions have remained satisfied for 5 seconds.
2. If DO_LOW becomes FALSE or an emergency stop occurs, immediately disable BLOWER_RUN and reset the start timer, whether timing is incomplete or complete. A new demand must wait the full 5 seconds again.
3. Increment AERATION_BLOWER_CYCLE_COUNT once on each FALSE-to-TRUE transition of BLOWER_RUN. Do not count repeatedly during continuous operation.
4. At power-up, initialize the blower to OFF and the start count to zero. The start delay gates a BOOL enable; no continuous speed ramp is required.

中文摘要：曝气风机延时启动：溶解氧偏低且无急停持续 5 秒才启动，
条件消失立即停机并复位计时，按启动次数计数。

扫描周期：20 ms（全组统一，见 docs/tasks_note.md）

【必留：接口、初态、约束与数据告警】
{
  "task_id": "P06",
  "title": "Aeration Blower Delayed Start",
  "io_table": [
    {
      "direction": "IN",
      "name": "DO_LOW",
      "data_type": "BOOL",
      "description": "Dissolved oxygen is below its threshold and aeration is needed."
    },
    {
      "direction": "IN",
      "name": "AERATION_E_STOP_NC",
      "data_type": "BOOL",
      "description": "TRUE means the emergency stop is inactive; FALSE means it is active."
    },
    {
      "direction": "OUT",
      "name": "BLOWER_RUN",
      "data_type": "BOOL",
      "description": "Blower motor-contactor run command."
    },
    {
      "direction": "OUT",
      "name": "AERATION_BLOWER_CYCLE_COUNT",
      "data_type": "UINT",
      "description": "Count of actual blower starts."
    }
  ],
  "initial_state": "BLOWER_RUN = FALSE；AERATION_BLOWER_CYCLE_COUNT = 0；启动延时计时器清零。",
  "constraints": [
    "K1 延时计时只在 DO_LOW = TRUE 且 AERATION_E_STOP_NC = TRUE 时进行。",
    "K2 上述两个条件同时满足并持续满 5 s 后才允许 BLOWER_RUN = TRUE。",
    "K3 DO_LOW 变 FALSE 或急停发生时，BLOWER_RUN 立即 FALSE、启动计时复位；下次需求须重新计满 5 s。",
    "K4 AERATION_BLOWER_CYCLE_COUNT 只在 BLOWER_RUN 的 FALSE→TRUE 沿加 1，连续运行期间不得重复计数。"
  ],
  "semantic_warnings": [],
  "warnings": [],
  "missing_fields": [],
  "dialect_requirements": [],
  "type_origins": {}
}

【必留：完整形式化规约；有界时序以扫描周期计】
# task: P06
# meta: easy / A 开关量联锁
# spec: version 1.0, updated 2026-10-30, scan cycle 20 ms
# 条款号对齐任务书 3.4 的条款库 C1—C10；[a,b] 单位为扫描周期。

C1: G(!AERATION_E_STOP_NC -> !BLOWER_RUN)    -- 急停当周期风机必须停（K1/K3）
C2: G(BLOWER_RUN -> (DO_LOW && AERATION_E_STOP_NC))    -- 风机运行的双许可：溶解氧偏低且无急停（K2）
C3: G(!DO_LOW -> X(!BLOWER_RUN))    -- 溶解氧恢复后下一周期必须停机并复位启动计时（K3）
C6: G(BLOWER_RUN -> (BLOWER_RUN W !DO_LOW))    -- 需求持续期间风机保持运行，不因单周期抖动反复启停（K2/K3）
C10: G[0,1](!BLOWER_RUN)    -- 上电首周期风机不运行（需先计满 5 s）（K1）

实现说明与冲突报告：
替换占位 RETURN，增加非保持的扫描计时状态和输出沿检测状态。
每次调用代表完整的 20 ms 扫描；第 250 个连续双许可扫描结束时启动。
任一许可失效，当次调用立即停机并清零计时。

C6 与急停优先存在冲突：运行后 DO_LOW 始终为 TRUE 时，
C6 要求一直运行，但急停时 C1、K3 要求立即停机。
本实现保留原规约，按题面明确要求优先执行急停，不声称满足原始 C6。
C3 的下一周期停机要求由当周期立即停机和重新等待 250 扫描实现。

UINT 无法表示无限启动次数；未规定溢出策略。
本实现显式采用模 65536 计数，65535 后的下一次启动变为 0，
避免依赖运行时整数溢出行为。

未提供可访问的编译器、测试执行工具或测试命令，
因此未运行编译或逐周期测试，未验证功能正确性。
*)
FUNCTION_BLOCK FB_P06
VAR_INPUT
    DO_LOW : BOOL;
    AERATION_E_STOP_NC : BOOL;
END_VAR
VAR_OUTPUT
    BLOWER_RUN : BOOL := FALSE;
    AERATION_BLOWER_CYCLE_COUNT : UINT := UINT#0;
END_VAR
VAR
    StartDelayScans : UINT := UINT#0;
    PreviousBlowerRun : BOOL := FALSE;
END_VAR

IF NOT AERATION_E_STOP_NC OR NOT DO_LOW THEN
    StartDelayScans := UINT#0;
    BLOWER_RUN := FALSE;
ELSE
    IF StartDelayScans < UINT#250 THEN
        StartDelayScans := StartDelayScans + UINT#1;
    END_IF;
    BLOWER_RUN := StartDelayScans >= UINT#250;
END_IF;

IF BLOWER_RUN AND NOT PreviousBlowerRun THEN
    IF AERATION_BLOWER_CYCLE_COUNT = UINT#65535 THEN
        AERATION_BLOWER_CYCLE_COUNT := UINT#0;
    ELSE
        AERATION_BLOWER_CYCLE_COUNT :=
            AERATION_BLOWER_CYCLE_COUNT + UINT#1;
    END_IF;
END_IF;

PreviousBlowerRun := BLOWER_RUN;

END_FUNCTION_BLOCK

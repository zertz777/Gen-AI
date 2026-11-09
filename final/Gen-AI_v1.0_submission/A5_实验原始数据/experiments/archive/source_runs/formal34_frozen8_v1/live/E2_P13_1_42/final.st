(*
【需求原文】
Control an office-building supply fan and generate a temperature-setpoint adjustment from occupancy, operating mode and the energy-saving selection.

1. Valid HVAC_MODE_SELECTOR values are 0 (Auto), 1 (Comfort), 2 (Economy) and 3 (Night).
2. Start a 30-second delay only when occupancy is detected and Night mode is not selected. SUPPLY_FAN_RUN becomes TRUE only after these conditions remain satisfied for 30 seconds. Immediately stop the fan and reset timing if occupancy is lost or Night mode is selected. Wait the full 30 seconds again when the conditions recover.
3. Auto mode: use a 0°C adjustment when occupied. When unoccupied, use +3°C in energy-saving mode or +2°C in standard mode.
4. Comfort mode: use 0°C when occupied or +1°C when unoccupied. Economy mode: use 0°C when occupied or +4°C when unoccupied.
5. Night mode: use +4°C regardless of occupancy. The energy-saving selection affects only Auto mode.
6. Keep TEMP_SETPOINT_ADJUST within ±4°C. Initialize outputs to OFF and zero at power-up; update them from current inputs when normal calculation begins.
7. The start delay controls only the BOOL fan enable; no continuous speed ramp is required.

中文摘要：办公楼 HVAC 节能控制：按占用与模式（自动/舒适/经济/夜间）
决定送风机启停与温度设定值修正，风机启动需 30 秒延时。
扫描周期：20 ms（全组统一，见 docs/tasks_note.md）

【接口、初态、约束与数据告警】
{
  "task_id": "P13",
  "title": "Office HVAC Multi-mode Energy-Saving Control",
  "io_table": [
    {
      "direction": "IN",
      "name": "OCCUPANCY_DETECTED",
      "data_type": "BOOL",
      "description": "Occupancy-detection result derived from the CO₂ sensor."
    },
    {
      "direction": "IN",
      "name": "ENERGY_SAVING_MODE",
      "data_type": "BOOL",
      "description": "TRUE selects energy saving; FALSE selects standard operation; affects Auto mode only."
    },
    {
      "direction": "IN",
      "name": "HVAC_MODE_SELECTOR",
      "data_type": "INT",
      "description": "0 Auto, 1 Comfort, 2 Economy, 3 Night; callers supply a valid value."
    },
    {
      "direction": "OUT",
      "name": "SUPPLY_FAN_RUN",
      "data_type": "BOOL",
      "description": "Supply-fan run enable."
    },
    {
      "direction": "OUT",
      "name": "TEMP_SETPOINT_ADJUST",
      "data_type": "INT",
      "description": "Temperature-setpoint adjustment in °C."
    }
  ],
  "initial_state": "SUPPLY_FAN_RUN = FALSE；TEMP_SETPOINT_ADJUST = 0；启动延时计时器清零。",
  "constraints": [
    "K1 只有「检测到占用且未选夜间模式」时才开始 30 s 启动延时；条件保持满 30 s 后 SUPPLY_FAN_RUN 才为 TRUE。",
    "K2 占用丢失或切到夜间模式时立即停风机并复位延时；条件恢复后必须重新计满 30 s。",
    "K3 温度修正按模式取值：自动 0/+3（节能）/+2（标准）、舒适 0/+1、经济 0/+4、夜间恒 +4；节能开关只影响自动模式。",
    "K4 TEMP_SETPOINT_ADJUST 必须限制在 ±4 °C 之内。"
  ],
  "semantic_warnings": [],
  "warnings": [],
  "missing_fields": [],
  "dialect_requirements": [],
  "type_origins": {}
}

【完整形式化规约；有界时序以扫描周期计】
# task: P13
# meta: medium / B 模拟量与数据处理
# spec: version 1.0, updated 2026-10-30, scan cycle 20 ms
# 条款号对齐任务书 3.4 的条款库 C1—C10；[a,b] 单位为扫描周期。
#
# note: 暖通控制没有急停开关，“停机优先”表现为“占用丢失立即停风机”，已由 C3 覆盖；C1（急停优先）在本题无对应信号。

C2: G(SUPPLY_FAN_RUN -> (OCCUPANCY_DETECTED && HVAC_MODE_SELECTOR != 3))    -- 风机运行的许可：有占用且未选夜间模式 3（K1/K2）
C3: G(!OCCUPANCY_DETECTED -> !SUPPLY_FAN_RUN)    -- 占用丢失当拍停风机（启动延时不适用停机）（K2）
C6: G(HVAC_MODE_SELECTOR == 3 -> !SUPPLY_FAN_RUN)    -- 夜间模式当拍停风机；温度修正由用例检查为 +4（K2/K3）
C4: G(TEMP_SETPOINT_ADJUST >= -4 && TEMP_SETPOINT_ADJUST <= 4)    -- 温度修正必须限制在 ±4 ℃（输出限幅）（K4）
C10: G[0,0](!SUPPLY_FAN_RUN && TEMP_SETPOINT_ADJUST == 0)    -- 上电当拍风机不运行、修正为 0（初态）

【修改说明】
失败原因：原实现首次调用跳过温度计算，使 P13-03、P13-05 的
cycle 1 温度输出均为 0。
将温度计算和限幅移至初始化分支之外，首次调用也按当前输入计算。
保持外部接口及原风机初始化、延时、停机和复位逻辑不变。
首次调用清零风机计时；其后的每个连续有效扫描累计 20 ms，
第 1500 个连续有效计时扫描结束时启用风机。
非夜间模式之间切换不清零计时；无速度斜坡。

【语义冲突报告】
保留原 C10，不修改规约。
若 C10 的时刻 0 指首次调用完成后的输出，则它要求温度为 0，
与所提供测试在首次调用要求温度为 4 或 3 的行为冲突。
本实现按测试采用：上电初态指首次调用之前的声明初始化状态；
首次调用即开始温度正常计算。因此不能声称满足将 C10 的时刻 0
解释为首次调用完成后的规约。

【验证状态】
用户提供的旧版本检查结果为 fast、authoritative 均 pass，
逐周期测试为 4/6，通过项为 P13-01、P13-02、P13-04、P13-06。
当前会话无可执行工具，未重新运行所提供命令。
本次修改尚未经过编译或逐周期测试，不声称已经验证正确。
*)
FUNCTION_BLOCK FB_P13
VAR_INPUT
    OCCUPANCY_DETECTED : BOOL;
    ENERGY_SAVING_MODE : BOOL;
    HVAC_MODE_SELECTOR : INT;
END_VAR
VAR_OUTPUT
    SUPPLY_FAN_RUN : BOOL := FALSE;
    TEMP_SETPOINT_ADJUST : INT := 0;
END_VAR
VAR
    INITIALIZED : BOOL := FALSE;
    START_DELAY_SCANS : INT := 0;
END_VAR

IF NOT INITIALIZED THEN
    SUPPLY_FAN_RUN := FALSE;
    START_DELAY_SCANS := 0;
    INITIALIZED := TRUE;
ELSE
    IF OCCUPANCY_DETECTED AND (HVAC_MODE_SELECTOR <> 3) THEN
        IF START_DELAY_SCANS < 1500 THEN
            START_DELAY_SCANS := START_DELAY_SCANS + 1;
        END_IF;
        SUPPLY_FAN_RUN := (START_DELAY_SCANS >= 1500);
    ELSE
        SUPPLY_FAN_RUN := FALSE;
        START_DELAY_SCANS := 0;
    END_IF;
END_IF;

CASE HVAC_MODE_SELECTOR OF
    0:
        IF OCCUPANCY_DETECTED THEN
            TEMP_SETPOINT_ADJUST := 0;
        ELSIF ENERGY_SAVING_MODE THEN
            TEMP_SETPOINT_ADJUST := 3;
        ELSE
            TEMP_SETPOINT_ADJUST := 2;
        END_IF;

    1:
        IF OCCUPANCY_DETECTED THEN
            TEMP_SETPOINT_ADJUST := 0;
        ELSE
            TEMP_SETPOINT_ADJUST := 1;
        END_IF;

    2:
        IF OCCUPANCY_DETECTED THEN
            TEMP_SETPOINT_ADJUST := 0;
        ELSE
            TEMP_SETPOINT_ADJUST := 4;
        END_IF;

    3:
        TEMP_SETPOINT_ADJUST := 4;

    ELSE
        (* 调用方保证模式有效；此分支仅防止沿用旧温度输出。 *)
        TEMP_SETPOINT_ADJUST := 0;
END_CASE;

IF TEMP_SETPOINT_ADJUST > 4 THEN
    TEMP_SETPOINT_ADJUST := 4;
ELSIF TEMP_SETPOINT_ADJUST < -4 THEN
    TEMP_SETPOINT_ADJUST := -4;
END_IF;
END_FUNCTION_BLOCK

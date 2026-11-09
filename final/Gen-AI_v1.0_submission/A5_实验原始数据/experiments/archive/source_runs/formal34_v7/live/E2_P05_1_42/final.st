(*
【必留：需求原文】
Control a weld-gap alarm with power-up monitoring inhibition, input debouncing during normal monitoring and emergency-stop priority.

1. Gap_Exceeded indicates that the scanner has detected a weld gap exceeding the permitted 1.5 mm value.
2. Begin with a 5-second initialization inhibition period after power-up. During this period, Operator_Alert is FALSE, Weld_Soft_Start_Active is TRUE, and gap-signal debounce time does not accumulate.
3. Resume gap monitoring after initialization. Allow the alarm only after Gap_Exceeded has remained TRUE for DebounceTime. When the signal becomes FALSE, switch off the alarm and clear debounce timing.
4. When Weld_E_Stop_NC is FALSE, the emergency stop takes priority over initialization and normal monitoring. Operator_Alert must immediately become FALSE and any incomplete debounce timing must be cleared.
5. Weld_Soft_Start_Active indicates only the power-up inhibition period; it does not represent a continuous speed ramp.

中文摘要：焊缝间隙报警：上电后 5 秒抑制期内不报警，抑制结束后间隙超限需去抖才报警，急停优先于一切。

扫描周期：20 ms（全组统一，见 docs/tasks_note.md）

【必留：接口、初态、约束与数据告警】
{
  "task_id": "P05",
  "title": "Weld Gap Alarm and Startup Inhibition",
  "io_table": [
    {
      "direction": "IN",
      "name": "Gap_Exceeded",
      "data_type": "BOOL",
      "description": "Scanner indication that the gap exceeds 1.5 mm."
    },
    {
      "direction": "IN",
      "name": "Weld_E_Stop_NC",
      "data_type": "BOOL",
      "description": "TRUE means the emergency stop is inactive; FALSE means it is active."
    },
    {
      "direction": "IN",
      "name": "DebounceTime",
      "data_type": "TIME",
      "description": "Gap-signal debounce duration during normal monitoring; must be positive."
    },
    {
      "direction": "OUT",
      "name": "Operator_Alert",
      "data_type": "BOOL",
      "description": "Audible and visual alarm command."
    },
    {
      "direction": "OUT",
      "name": "Weld_Soft_Start_Active",
      "data_type": "BOOL",
      "description": "Monitoring-inhibition status during the 5-second power-up initialization."
    }
  ],
  "initial_state": "Operator_Alert = FALSE；Weld_Soft_Start_Active = TRUE（抑制期开始）；去抖计时器清零。",
  "constraints": [
    "K1 上电后进入 5 s 初始化抑制期，期间 Weld_Soft_Start_Active = TRUE、Operator_Alert = FALSE，且去抖计时不累计。",
    "K2 抑制期结束后恢复监视：Gap_Exceeded 连续为 TRUE 达 DebounceTime 才置 Operator_Alert。",
    "K3 Gap_Exceeded 变 FALSE 时立即复位 Operator_Alert 并清去抖计时。",
    "K4 Weld_E_Stop_NC = FALSE 时急停优先于抑制期与正常监视：Operator_Alert 立即 FALSE，未完成的去抖计时清除。"
  ],
  "semantic_warnings": [],
  "warnings": [],
  "missing_fields": [],
  "dialect_requirements": [],
  "type_origins": {}
}

【必留：完整形式化规约；有界时序以扫描周期计】
# task: P05
# meta: easy / A 开关量联锁
# spec: version 1.0, updated 2026-10-30, scan cycle 20 ms
# 条款号对齐任务书 3.4 的条款库 C1—C10；[a,b] 单位为扫描周期。

C1: G(!Weld_E_Stop_NC -> !Operator_Alert)    -- 急停当周期必须清报警（急停优先于抑制期与监视）（K4）
C2: G(Operator_Alert -> Weld_E_Stop_NC)    -- 报警的前提是急停正常（不得在急停状态下报警）（K4）
C6: G(Operator_Alert -> (Operator_Alert W !Gap_Exceeded))    -- 间隙恢复后报警才允许撤销（报警保持）（K3）
C9: G(Operator_Alert -> G[0,25](Operator_Alert))    -- 报警一旦置位至少保持 500 ms（去抖后的最小脉宽）（K2）
C10: G[0,1](!Operator_Alert && Weld_Soft_Start_Active)    -- 上电首周期处于抑制期：不报警、软启动有效（K1）

实现变更：
以固定 20 ms 扫描计时替换占位 RETURN，加入初始化抑制、
正常监视去抖、间隙恢复复位以及急停优先逻辑，不修改外部接口。

规约冲突报告：
1. C6 不允许在 Gap_Exceeded 仍为 TRUE 时撤销已置位的报警，
   但 C1、C2、K4 要求急停当周期清报警，两者存在冲突。
2. C9 无条件要求报警在当前及后续 25 个周期保持 TRUE，
   与该窗口内急停必须清报警的 C1、K4 冲突，
   也与该窗口内间隙恢复必须清报警的 K3 冲突。
3. C9 中的嵌套 G 对每个报警为 TRUE 的周期重新施加保持要求，
   并不等同于仅在上升沿触发一次的最小脉宽要求。
因此不存在对任意输入序列同时满足全部条款的实现。
本实现保留上述原始条款，按明确的急停优先要求及需求原文
执行 K1 至 K4，不实现与即时复位冲突的 C6/C9 无条件保持。

扫描边界约定：
每次调用计入一个 20 ms 区间。
前 250 次调用输出初始化抑制有效；第 251 次开始正常监视。
初始化计时不因急停暂停或重启，急停解除不会启动新的抑制期。
正常监视中，每个有效的连续 TRUE 扫描计入 20 ms；
第 CEIL(DebounceTime / 20 ms) 个有效扫描允许报警。
抑制期的最后一个扫描不累计去抖时间。
急停清除全部去抖计时；解除急停后必须重新完成去抖。
DebounceTime 必须为正；非法值禁止报警并清除计时。
未报警时使用当前 DebounceTime；已报警后保持到间隙恢复、
急停或 DebounceTime 非法，不因正值参数变化撤销报警。
计时达到目标后饱和，避免持续 TRUE 引起 TIME 累加溢出。
内部变量不得配置为掉电保持；实例重新初始化即开始上电抑制。

验证状态：
当前对话未提供可执行测试环境、已配置测试命令或编译 profile，
无法运行编译或逐周期测试。以下源码未经过真实编译器验证，
也未声称功能已验证正确。
*)

FUNCTION_BLOCK FB_P05
VAR_INPUT
    Gap_Exceeded : BOOL;
    Weld_E_Stop_NC : BOOL;
    DebounceTime : TIME;
END_VAR
VAR_OUTPUT
    Operator_Alert : BOOL := FALSE;
    Weld_Soft_Start_Active : BOOL := TRUE;
END_VAR
VAR
    InitializationElapsed : TIME := T#0ms;
    DebounceElapsed : TIME := T#0ms;
END_VAR

(* 根据扫描开始时的累计时间决定本扫描是否仍处于抑制期。 *)
Weld_Soft_Start_Active := InitializationElapsed < T#5s;

IF Weld_Soft_Start_Active THEN
    InitializationElapsed := InitializationElapsed + T#20ms;
END_IF;

(* 急停优先，且不影响独立的上电初始化计时。 *)
IF NOT Weld_E_Stop_NC THEN
    Operator_Alert := FALSE;
    DebounceElapsed := T#0ms;

ELSIF Weld_Soft_Start_Active THEN
    Operator_Alert := FALSE;
    DebounceElapsed := T#0ms;

ELSIF NOT Gap_Exceeded THEN
    Operator_Alert := FALSE;
    DebounceElapsed := T#0ms;

ELSIF DebounceTime <= T#0ms THEN
    (* 非法参数采用禁止报警的确定性处理。 *)
    Operator_Alert := FALSE;
    DebounceElapsed := T#0ms;

ELSIF NOT Operator_Alert THEN
    (* 先比较剩余时间，避免直接累加在 TIME 上界发生溢出。 *)
    IF DebounceElapsed >= DebounceTime THEN
        DebounceElapsed := DebounceTime;
        Operator_Alert := TRUE;
    ELSIF (DebounceTime - DebounceElapsed) <= T#20ms THEN
        DebounceElapsed := DebounceTime;
        Operator_Alert := TRUE;
    ELSE
        DebounceElapsed := DebounceElapsed + T#20ms;
        Operator_Alert := FALSE;
    END_IF;
END_IF;

END_FUNCTION_BLOCK

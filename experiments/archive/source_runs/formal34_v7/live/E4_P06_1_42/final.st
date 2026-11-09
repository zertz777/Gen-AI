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
    StartPermitted : BOOL := FALSE;
END_VAR

(*
需求原文：
Control a wastewater-treatment aeration blower with a low-dissolved-oxygen
demand, a 5-second start delay, emergency-stop priority and start-cycle counting.

1. Start delay timing when both DO_LOW and AERATION_E_STOP_NC are TRUE.
   Allow BLOWER_RUN to become TRUE only after these conditions have remained
   satisfied for 5 seconds.
2. If DO_LOW becomes FALSE or an emergency stop occurs, immediately disable
   BLOWER_RUN and reset the start timer, whether timing is incomplete or complete.
   A new demand must wait the full 5 seconds again.
3. Increment AERATION_BLOWER_CYCLE_COUNT once on each FALSE-to-TRUE transition
   of BLOWER_RUN. Do not count repeatedly during continuous operation.
4. At power-up, initialize the blower to OFF and the start count to zero.
   The start delay gates a BOOL enable; no continuous speed ramp is required.

完整形式化规约：
C1: G(!AERATION_E_STOP_NC -> !BLOWER_RUN)
C2: G(BLOWER_RUN -> (DO_LOW && AERATION_E_STOP_NC))
C3: G(!DO_LOW -> X(!BLOWER_RUN))
C6: G(BLOWER_RUN -> (BLOWER_RUN W !DO_LOW))
C10: G[0,1](!BLOWER_RUN)

待审语义冲突：
C6 在 DO_LOW 始终为 TRUE 时要求已启动的风机持续运行；
此时若发生急停，C1 和需求第 2 条要求立即停机。
两者不能同时满足。本实现保留急停优先，未声称满足 C6。

计时约定：
每次调用代表一个完整的 20 ms 扫描区间。
连续 250 次双许可调用累计 5 s；许可中断当扫描清零。

数值边界：
UINT 无法表示无限启动次数。题面未指定溢出策略，待审。
这里显式采用模 65536 加一，避免越界算术；
65535 后下一次启动输出 0，不代表无限精度累计次数。

本源码未经编译或逐周期测试验证。
*)

StartPermitted := DO_LOW AND AERATION_E_STOP_NC;

IF NOT StartPermitted THEN
    (* 停机优先；完成或未完成的计时均复位。 *)
    StartDelayScans := UINT#0;
    BLOWER_RUN := FALSE;
ELSE
    IF StartDelayScans < UINT#250 THEN
        StartDelayScans := StartDelayScans + UINT#1;
    END_IF;

    BLOWER_RUN := (StartDelayScans >= UINT#250);
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

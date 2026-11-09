TYPE ST_Pump :
STRUCT
    priority : INT;
    selection : BOOL;
    RunComd : BOOL;
END_STRUCT
END_TYPE

FUNCTION_BLOCK FB_P07
VAR_INPUT
    mode : BOOL;
    start : BOOL;
    stop : BOOL;
END_VAR
VAR_IN_OUT
    pumpGroup : ARRAY[1..5] OF ST_Pump;
END_VAR
VAR
    StartupScans : INT := 0;
    RunningEnabled : BOOL := FALSE;
    i : INT;
    j : INT;
    HigherRankCount : INT;
END_VAR

(*
必留：需求原文
In an industrial water supply system, there are 5 pumps, each of which
can be controlled independently. The system needs to support both manual
and automatic operating modes.
Based on the value of the mode variable, switch to the corresponding
operating mode.
In manual mode, control the start and stop of the selected pump based on
the value of pumpGroup[1..5].selection.
In automatic mode, compare the priority of each pump, and automatically
select the 3 pumps with higher priority for water supply according to the
method of three in use and two on standby.

扫描周期：20 ms。
结构映射：priority、selection、RunComd 为 ST_Pump 字段；
保持指定骨架接口，不增加同名独立标量端口。
只读取 priority 和 selection，只写入 RunComd。

待审语义冲突：
1. C4 约束只读输入 start、stop 不得同时有效，FB 无法保证该环境条件。
   同时有效时按 K4 执行停止，不修改输入。
2. K2 无条件要求自动模式恰有三台运行，与 stop 清除全部运行命令、
   上电无运行命令及 start 启动语义冲突。本实现停止和上电抑制优先；
   启动许可保持后，自动模式选出三台。
3. C6 若逐泵解释为运行命令保持至 stop，则与手动取消选择、
   模式切换及自动优先级变化后重新选泵存在冲突。
   本实现保持组启动许可至 stop，但逐泵命令按当前模式和字段重算；
   因而不声称满足上述情况下的逐泵 C6。
4. C10 的 G[0,1] 与文字“上电首周期”范围不一致。
   本实现按明确的扫描区间，在第 0、1 两个扫描清除全部命令；
   此期间不记忆 start。

未经过编译profile或逐周期测试验证。
*)

IF StartupScans < 2 THEN
    StartupScans := StartupScans + 1;
    RunningEnabled := FALSE;

    FOR i := 1 TO 5 DO
        pumpGroup[i].RunComd := FALSE;
    END_FOR;

ELSE
    (* stop 优先；start 为电平请求，启动许可保持至 stop。 *)
    IF stop THEN
        RunningEnabled := FALSE;
    ELSIF start THEN
        RunningEnabled := TRUE;
    END_IF;

    IF NOT RunningEnabled THEN
        FOR i := 1 TO 5 DO
            pumpGroup[i].RunComd := FALSE;
        END_FOR;

    ELSIF NOT mode THEN
        FOR i := 1 TO 5 DO
            pumpGroup[i].RunComd := pumpGroup[i].selection;
        END_FOR;

    ELSE
        (* 排名计数无需优先级算术，避免 INT 极值溢出。
           优先级相同则泵号较小者先；排名前三运行。 *)
        FOR i := 1 TO 5 DO
            HigherRankCount := 0;

            FOR j := 1 TO 5 DO
                IF pumpGroup[j].priority > pumpGroup[i].priority THEN
                    HigherRankCount := HigherRankCount + 1;
                ELSIF (pumpGroup[j].priority = pumpGroup[i].priority)
                      AND (j < i) THEN
                    HigherRankCount := HigherRankCount + 1;
                END_IF;
            END_FOR;

            pumpGroup[i].RunComd := HigherRankCount < 3;
        END_FOR;
    END_IF;
END_IF;

END_FUNCTION_BLOCK

(*
修改说明：
1. 删除 END_STRUCT 后的分号。当前权威编译器对该分号报告
   E_SYNTAX：应该采用 'END_TYPE' 取代 ';'。
2. 已提供结果表明两套编译器对该类型声明的语法要求不同：
   无分号版本曾通过权威编译，但快速编译报告缺少分号；
   有分号版本通过快速编译，但权威编译失败。
   本次采用权威编译器接受的无分号写法，不声称兼容两个 profile。
   若要求两套编译器同时通过，需要在编译工具链中明确方言适配，
   不能仅凭当前日志保证同一声明满足两者。
3. 保持接口、结构字段映射和扫描逻辑不变。
   首次调用先初始化内部状态，再处理当周期输入，不抑制启动。

实现说明：
使用内部运行状态，避免依赖调用方传入的 RunComd 初值。
按每次调用 20 ms 执行，不需要计时器。
启动采用电平语义，停止优先；停止后必须有有效 start 才恢复运行。
手动模式下，start 启动所有 selection 为 TRUE 的泵，其他泵保持原状态。
自动启动后每周期按当前优先级选取三台，优先级相同时泵号小者优先。
切回手动模式不自行停止已经运行的泵，只有手动启动与全组停止动作生效。

必须报告的语义冲突：
1. K2 要求自动模式恰有三台运行，与 stop 时全停、初始全停以及
   自动泵也必须通过 start 启动的接口描述不能无条件同时满足。
   本实现将三用两备限定于已启动且 stop 为 FALSE 时。
2. C6 要求每台泵一直运行到 stop，但自动模式按实时优先级重选，
   或从手动模式切入自动模式后限制为三台，都可能停止已有运行泵。
   本实现保留原规约，并优先执行工作模式及自动优先级选择要求；
   因而不声称满足无条件 C6。
3. C4 约束的是输入，功能块无法禁止外部同时给出 start 和 stop。
   对非法组合仍执行 stop 优先，不修改输入。
4. C10 的 G[0,1] 要求前两个扫描采样点无运行命令，
   文字说明只说首周期，而已提供测试要求首个扫描可响应启动。
   三者存在冲突。本实现按测试期望允许首个扫描响应 start，
   初态仅指处理输入前内部命令全 FALSE，不声称满足原 C10。
5. selection 是只读字段，其初值全 FALSE 必须由调用方保证，
   功能块不能写 selection 来建立该初态。
6. 手动按 selection 单泵停止的原文，与 stop 停止全组的接口描述、
   以及 C6 的保持要求存在边界歧义。本实现采用 stop 全组停止，
   selection 仅作为 start 的选泵条件，取消选择不自行停止。

验证说明：
最新提供结果为快速编译通过、权威编译失败，未提供该版本的功能测试结果。
更早版本的逐周期测试仅通过 1/7；不能将编译通过视为功能正确。
本次修改未在真实编译器或测试环境中执行，
当前对话无可调用的命令执行工具，不能运行所给 Windows 命令。
需重新执行原测试命令，检查权威编译及完整逐周期测试结果。
删除分号可能再次触发快速编译器的已知语法错误；
需按配置的编译 profile 分别记录，不声称全部编译或测试通过。
*)

(*
【必留：需求原文】
In an industrial water supply system, there are 5 pumps, each of which can be controlled independently. The system needs to support both manual and automatic operating modes.
Based on the value of the mode variable, switch to the corresponding operating mode.
In manual mode, control the start and stop of the selected pump based on the value of pumpGroup[1..5].selection.
In automatic mode, compare the priority of each pump, and automatically select the 3 pumps with higher priority for water supply according to the method of three in use and two on standby.

中文摘要：五泵切换控制：手动模式按选择开关单泵启停，自动模式按优先级选出 3 台运行、2 台备用（三用两备）。

扫描周期：20 ms（全组统一，见 docs/tasks_note.md）
*)

(*
【必留：接口、初态、约束与数据告警】
{
  "task_id": "P07",
  "title": "Multi-Pump Switching Control System",
  "io_table": [
    {
      "direction": "IN",
      "name": "mode",
      "data_type": "BOOL",
      "description": "FALSE: Manual mode<br>TRUE: Automatic mode"
    },
    {
      "direction": "IN",
      "name": "start",
      "data_type": "BOOL",
      "description": "Start button, used to start the manually selected or automatically selected pump"
    },
    {
      "direction": "IN",
      "name": "stop",
      "data_type": "BOOL",
      "description": "Stop button, used to stop all pumps"
    },
    {
      "direction": "INOUT",
      "name": "pumpGroup",
      "data_type": "ARRAY[1..5] OF ST_Pump",
      "description": "Five pump records passed by reference. Read priority and selection; write only RunComd."
    },
    {
      "direction": "IN",
      "name": "priority",
      "data_type": "INT",
      "description": "Priority; larger values have higher priority. Read-only to the function block."
    },
    {
      "direction": "IN",
      "name": "selection",
      "data_type": "BOOL",
      "description": "Manual-selection state. Read-only to the function block."
    },
    {
      "direction": "OUT",
      "name": "RunComd",
      "data_type": "BOOL",
      "description": "Run command written by the function block; TRUE runs and FALSE stops."
    }
  ],
  "initial_state": "5 台泵输出全 FALSE；pumpGroup[1..5].selection 全 FALSE；自动模式下运行台数目标 = 3。",
  "constraints": [
    "K1 mode 决定工作模式，手动与自动互斥，同一时刻只有一种模式的动作生效。",
    "K2 自动模式下同时运行的泵数恰为 3 台，其余 2 台作为备用。",
    "K3 自动模式下按优先级选出运行泵：优先级高者先启，优先级相同时按泵号升序，保证结果确定。",
    "K4 stop 信号优先于 start：停止请求有效时不得因 start 或自动需求而启动任何泵。"
  ],
  "semantic_warnings": [],
  "warnings": [],
  "missing_fields": [],
  "dialect_requirements": [],
  "type_origins": {
    "ST_Pump": {
      "evidence": "requirement中的结构说明 + io_table字段类型",
      "fields": [
        "priority",
        "selection",
        "RunComd"
      ]
    }
  }
}

补充映射说明：
priority、selection、RunComd 对应 ST_Pump 的结构字段，
不是新增的功能块独立端口。
*)

(*
【必留：完整形式化规约；有界时序以扫描周期计】
# task: P07
# meta: easy / A 开关量联锁
# spec: version 1.0, updated 2026-10-30, scan cycle 20 ms
# 条款号对齐任务书 3.4 的条款库 C1—C10；[a,b] 单位为扫描周期。

C1: G(stop -> !RunComd)    -- 停止请求当周期必须清除运行命令（stop 优先于 start）（K4）
C2: G(RunComd -> !stop)    -- 运行命令的前提是没有停止请求（互斥的许可形式）（K4）
C4: G(!(start && stop))    -- 启动与停止同时有效属于非法请求，不得出现（K4）
C6: G(RunComd -> (RunComd W stop))    -- 运行命令保持到停止请求出现为止（不自行掉线）（K1）
C10: G[0,1](!RunComd)    -- 上电首周期无运行命令（初态）

RunComd 的输出约束逐泵应用。
*)

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
    initialized : BOOL := FALSE;
    enabled : BOOL := FALSE;
    commands : ARRAY[1..5] OF BOOL;
    i : INT;
    j : INT;
    higherCount : INT;
END_VAR

(* 建立内部初态，不跳过当周期输入处理。 *)
IF NOT initialized THEN
    enabled := FALSE;
    FOR i := 1 TO 5 DO
        commands[i] := FALSE;
    END_FOR;
    initialized := TRUE;
END_IF;

(* 停止请求覆盖启动和自动需求。 *)
IF stop THEN
    enabled := FALSE;
    FOR i := 1 TO 5 DO
        commands[i] := FALSE;
    END_FOR;
ELSE
    IF start THEN
        enabled := TRUE;
    END_IF;

    IF mode THEN
        IF enabled THEN
            (* 排名小于三即入选，不做 INT 优先级减法，避免溢出。 *)
            FOR i := 1 TO 5 DO
                higherCount := 0;
                FOR j := 1 TO 5 DO
                    IF pumpGroup[j].priority > pumpGroup[i].priority THEN
                        higherCount := higherCount + 1;
                    ELSIF (pumpGroup[j].priority = pumpGroup[i].priority)
                        AND (j < i) THEN
                        higherCount := higherCount + 1;
                    END_IF;
                END_FOR;
                commands[i] := higherCount < 3;
            END_FOR;
        ELSE
            FOR i := 1 TO 5 DO
                commands[i] := FALSE;
            END_FOR;
        END_IF;
    ELSE
        (* 未选中或 start 无效时保留运行状态，stop 已在上层处理。 *)
        IF start THEN
            FOR i := 1 TO 5 DO
                IF pumpGroup[i].selection THEN
                    commands[i] := TRUE;
                END_IF;
            END_FOR;
        END_IF;
    END_IF;
END_IF;

(* 唯一外部写入点：不修改 priority 或 selection。 *)
FOR i := 1 TO 5 DO
    pumpGroup[i].RunComd := commands[i];
END_FOR;

END_FUNCTION_BLOCK

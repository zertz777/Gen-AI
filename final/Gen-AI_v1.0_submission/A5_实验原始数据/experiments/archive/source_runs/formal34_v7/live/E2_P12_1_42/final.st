(*
需要修改：替换占位 RETURN，实现报警保持、有效故障上升沿统计、
最近五条历史和正常切割运行时间累计，保持外部接口不变。

需求原文：
Monitor slab-thickness faults on a stone-cutting line, including minimum alarm holding, fault counting, normal-cutting runtime accumulation and a history of the five most recent faults.

1. When THICKNESS_SIGNAL_VALID is TRUE, THICKNESS_FAULT indicates that thickness deviation exceeds tolerance. Activate THICKNESS_ALARM immediately when the fault becomes TRUE, and hold each triggered alarm for at least 500 ms. Keep the alarm active while the fault persists.
2. On each FALSE-to-TRUE transition of a valid fault signal, increment Slab_Fault_Counter and store the current FaultTimestamp in element 0 of Slab_Fault_History. Shift older entries toward higher indices, retaining only the five most recent entries.
3. Accumulate Slab_Runtime_Accumulator using CycleTime only while CUTTING_RUN is TRUE, the thickness signal is valid and no thickness fault is present. Otherwise preserve the accumulated value.
4. At power-up or whenever THICKNESS_SIGNAL_VALID is FALSE, switch off the alarm and clear its holding state. Do not add fault records or accumulate normal runtime while the signal is invalid.
5. At power-up, initialize the fault count, accumulated runtime and all five history entries to zero. Statistics and history are for observation and maintenance only; they must not alter the cutting equipment's operating permissive, and external callers must not modify history entries.

中文摘要：板坯厚度故障：信号有效时判故障、报警至少保持 500 ms、
故障上升沿计数并保留最近 5 条历史，正常运行时间按周期累计。
扫描周期：20 ms（全组统一，见 docs/tasks_note.md）

接口、初态、约束与数据告警：
{
  "task_id": "P12",
  "title": "Slab Thickness Alarm and Fault History",
  "io_table": [
    {
      "direction": "IN",
      "name": "THICKNESS_FAULT",
      "data_type": "BOOL",
      "description": "Thickness deviation exceeds the permitted tolerance."
    },
    {
      "direction": "IN",
      "name": "THICKNESS_SIGNAL_VALID",
      "data_type": "BOOL",
      "description": "Thickness-signal validity; FALSE means the signal is lost or unavailable."
    },
    {
      "direction": "IN",
      "name": "CUTTING_RUN",
      "data_type": "BOOL",
      "description": "Actual cutting-equipment running status."
    },
    {
      "direction": "IN",
      "name": "FaultTimestamp",
      "data_type": "DINT",
      "description": "Current timestamp in seconds, used as the fault-record identifier."
    },
    {
      "direction": "IN",
      "name": "CycleTime",
      "data_type": "TIME",
      "description": "Actual elapsed interval represented by this invocation; must be positive."
    },
    {
      "direction": "OUT",
      "name": "THICKNESS_ALARM",
      "data_type": "BOOL",
      "description": "Thickness alarm with a minimum 500 ms hold duration."
    },
    {
      "direction": "OUT",
      "name": "Slab_Fault_Counter",
      "data_type": "UINT",
      "description": "Number of valid thickness-fault occurrences."
    },
    {
      "direction": "OUT",
      "name": "Slab_Runtime_Accumulator",
      "data_type": "LTIME",
      "description": "Accumulated normal-cutting runtime."
    },
    {
      "direction": "OUT",
      "name": "Slab_Fault_History",
      "data_type": "ARRAY[0..4] OF DINT",
      "description": "Five most recent fault timestamps; index 0 is newest; read-only to callers."
    }
  ],
  "initial_state": "THICKNESS_ALARM = FALSE；Slab_Fault_Counter = 0；Slab_Runtime_Accumulator = T#0s；Slab_Fault_History[0..4] 全为 0；保持计时器清零。",
  "constraints": [
    "K1 只在 THICKNESS_SIGNAL_VALID = TRUE 时判定 THICKNESS_FAULT，信号无效期间不报警、不计数、不累计运行时间。",
    "K2 故障上升沿时 Slab_Fault_Counter 加 1，并把 FaultTimestamp 写入历史元素 0，原有记录向高索引移位，只保留最近 5 条。",
    "K3 THICKNESS_ALARM 一旦置位至少保持 500 ms；故障持续期间保持为 TRUE。",
    "K4 仅当 CUTTING_RUN = TRUE、信号有效且无厚度故障时，按 CycleTime 累加 Slab_Runtime_Accumulator；否则保持不变。"
  ],
  "semantic_warnings": [],
  "warnings": [],
  "missing_fields": [],
  "dialect_requirements": [
    "LTIME需要编译profile支持长时间类型"
  ],
  "type_origins": {}
}

完整形式化规约；有界时序以扫描周期计：
# task: P12
# meta: medium / D 故障与安全
# spec: version 1.0, updated 2026-10-30, scan cycle 20 ms
# 条款号对齐任务书 3.4 的条款库 C1—C10；[a,b] 单位为扫描周期。
#
# note: 本题只给了品质信号与切割运行信号，没有急停，因此 C1 以「信号无效即不报警」的形式归入 C2/C8。

C2: G(THICKNESS_ALARM -> THICKNESS_SIGNAL_VALID)    -- 信号无效期间不得报警（报警的前提是信号有效）（K1）
C5: G(THICKNESS_FAULT && THICKNESS_SIGNAL_VALID -> F[0,25](THICKNESS_ALARM))    -- 故障出现后 500 ms 内必须报警（响应时限）（K3）
C6: G(THICKNESS_ALARM -> (THICKNESS_ALARM W !THICKNESS_FAULT))    -- 故障持续期间报警保持（至少 500 ms 由此推出）（K3）
C8: G(!THICKNESS_SIGNAL_VALID -> X(!THICKNESS_ALARM))    -- 信号失效后下一周期清报警，不保留陈旧报警（K1）
C10: G[0,1](!THICKNESS_ALARM)    -- 上电首周期不报警（初态）

语义冲突与实现边界：
1. 信号无效时立即清报警，优先于无条件的 500 ms 保持。
   若无效时 THICKNESS_FAULT 仍为 TRUE，C2 与 C6 可以冲突。
2. C6 的弱直到并不能推出 500 ms 最短保持；本实现单独计时。
3. C8 的 X 要求无效扫描之后一帧也不报警；若下一帧恢复有效且
   存在故障，这与需求 1 的立即报警冲突。本实现按当前扫描有效性处理。
4. C10 的 [0,1] 与“首周期”注释不完全一致；初始输入即有效故障时，
   其禁止报警的要求又与需求 1 冲突。本实现初始化为零后执行首帧逻辑，
   有效故障在首帧即报警，因此不声称满足 C10。
5. 有效故障定义为 THICKNESS_SIGNAL_VALID AND THICKNESS_FAULT。
   无效扫描清除上升沿记忆，恢复有效且故障为 TRUE 时记录新故障。
6. UINT 不能表示无限故障次数。计数达到 65535 后饱和，历史仍更新；
   此边界不满足无限次逐次加一要求，且不增加接口。
7. 历史由内部状态保存，每次调用重新发布全部输出，避免外部写入
   改变内部历史；固定 VAR_OUTPUT 接口无法从语言层禁止调用方写入。
8. CycleTime 必须为正；非正值不累计。累计值须处于 LTIME 可表示范围。
9. 保持时间按固定 20 ms 扫描推进，运行时间按 CycleTime 累计。
   不使用依赖真实时钟的厂商定时器。
10. 编译 profile 必须支持 LTIME、LTIME 字面量和 TIME_TO_LTIME。
    未使用 VARIANT、开放数组或替代类型。
11. 当前聊天没有可执行工具、编译 profile 或已配置测试命令，
    因此未运行编译和逐周期测试，不声称已经验证正确。
    应逐周期检查首帧故障、25 个间隔保持、保持期间再触发、
    信号丢失及恢复、历史移位、计数饱和与运行时间累计。
*)

FUNCTION_BLOCK FB_P12
VAR_INPUT
    THICKNESS_FAULT : BOOL;
    THICKNESS_SIGNAL_VALID : BOOL;
    CUTTING_RUN : BOOL;
    FaultTimestamp : DINT;
    CycleTime : TIME;
END_VAR
VAR_OUTPUT
    THICKNESS_ALARM : BOOL := FALSE;
    Slab_Fault_Counter : UINT := UINT#0;
    Slab_Runtime_Accumulator : LTIME := LTIME#0s;
    Slab_Fault_History : ARRAY[0..4] OF DINT :=
        [DINT#0, DINT#0, DINT#0, DINT#0, DINT#0];
END_VAR
VAR
    Initialized : BOOL := FALSE;
    PreviousValidFault : BOOL := FALSE;
    CurrentValidFault : BOOL := FALSE;
    HoldRemaining : TIME := T#0ms;
    FaultCountState : UINT := UINT#0;
    RuntimeState : LTIME := LTIME#0s;
    HistoryState : ARRAY[0..4] OF DINT :=
        [DINT#0, DINT#0, DINT#0, DINT#0, DINT#0];
END_VAR

(* 内部状态应采用非保持实例；冷启动恢复声明初值。 *)
IF NOT Initialized THEN
    PreviousValidFault := FALSE;
    CurrentValidFault := FALSE;
    HoldRemaining := T#0ms;
    FaultCountState := UINT#0;
    RuntimeState := LTIME#0s;
    HistoryState[0] := DINT#0;
    HistoryState[1] := DINT#0;
    HistoryState[2] := DINT#0;
    HistoryState[3] := DINT#0;
    HistoryState[4] := DINT#0;

    THICKNESS_ALARM := FALSE;
    Slab_Fault_Counter := UINT#0;
    Slab_Runtime_Accumulator := LTIME#0s;
    Slab_Fault_History[0] := DINT#0;
    Slab_Fault_History[1] := DINT#0;
    Slab_Fault_History[2] := DINT#0;
    Slab_Fault_History[3] := DINT#0;
    Slab_Fault_History[4] := DINT#0;
    Initialized := TRUE;
END_IF;

CurrentValidFault := THICKNESS_SIGNAL_VALID AND THICKNESS_FAULT;

IF NOT THICKNESS_SIGNAL_VALID THEN
    THICKNESS_ALARM := FALSE;
    HoldRemaining := T#0ms;
    PreviousValidFault := FALSE;
ELSE
    (* 先推进上一扫描留下的保持时间，再处理本扫描新触发。
       触发扫描不扣减；第 25 个后续扫描才允许撤销报警。 *)
    IF HoldRemaining > T#20ms THEN
        HoldRemaining := HoldRemaining - T#20ms;
    ELSE
        HoldRemaining := T#0ms;
    END_IF;

    IF CurrentValidFault AND NOT PreviousValidFault THEN
        HoldRemaining := T#500ms;

        IF FaultCountState < UINT#65535 THEN
            FaultCountState := FaultCountState + UINT#1;
        END_IF;

        HistoryState[4] := HistoryState[3];
        HistoryState[3] := HistoryState[2];
        HistoryState[2] := HistoryState[1];
        HistoryState[1] := HistoryState[0];
        HistoryState[0] := FaultTimestamp;
    END_IF;

    THICKNESS_ALARM :=
        CurrentValidFault OR (HoldRemaining > T#0ms);

    IF CUTTING_RUN AND NOT CurrentValidFault THEN
        IF CycleTime > T#0ms THEN
            RuntimeState := RuntimeState + TIME_TO_LTIME(CycleTime);
        END_IF;
    END_IF;

    PreviousValidFault := CurrentValidFault;
END_IF;

(* 输出仅为观测数据，不生成或改变设备运行许可。 *)
Slab_Fault_Counter := FaultCountState;
Slab_Runtime_Accumulator := RuntimeState;
Slab_Fault_History[0] := HistoryState[0];
Slab_Fault_History[1] := HistoryState[1];
Slab_Fault_History[2] := HistoryState[2];
Slab_Fault_History[3] := HistoryState[3];
Slab_Fault_History[4] := HistoryState[4];

END_FUNCTION_BLOCK

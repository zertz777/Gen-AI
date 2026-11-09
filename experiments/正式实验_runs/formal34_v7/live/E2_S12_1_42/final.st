(*
【需求原文】
设备急停后不允许简单松手就恢复，必须经过一套确认流程。

控制要求：
1. EStop_NC = FALSE 时 MachineRun 立即 FALSE，AlarmLamp = TRUE，
   Status = 16#8B01。
2. 急停解除后（EStop_NC = TRUE）进入待复位态：
   必须同时满足 DoorClosed = TRUE，且 ResetBtn 上升沿确认，
   再出现 StartBtn 上升沿，MachineRun 才允许为 TRUE。
3. 上述三个条件必须按「门关 → 复位 → 启动」的顺序满足；
   复位后若门再次打开，必须重新复位。
4. 急停期间 ShiftCount 冻结不变；重启后继续累加，不清零。
5. MachineRun = TRUE 时每 60 s 使 ShiftCount 加 1，
   用于统计本班运行时长，单位分钟。
6. Status：16#0000 正常、16#8B01 急停、
   16#8B02 待复位、16#8B03 门未关。

扫描周期：20 ms（全组统一，见 docs/tasks_note.md）

【接口、初态、约束与数据告警】
task_id: S12
title: 急停后安全重启与班次统计

输入：
EStop_NC : BOOL，急停常闭触点，TRUE = 正常。
ResetBtn : BOOL，复位按钮，上升沿有效。
StartBtn : BOOL，启动按钮，上升沿有效。
DoorClosed : BOOL，安全门关闭。

输出：
MachineRun : BOOL，设备运行。
ShiftCount : UINT，本班运行分钟数。
AlarmLamp : BOOL，报警灯。
Status : WORD，状态码。

initial_state:
MachineRun = FALSE；ShiftCount = 0；AlarmLamp = FALSE；
Status = 16#0000；已复位标志 = FALSE；
ResetBtnLast = StartBtnLast = FALSE。

constraints:
K1 EStop_NC = FALSE 时 MachineRun 必须为 FALSE。
K2 重启必须依次满足「门关 → 复位上升沿 → 启动上升沿」，
   缺一不可。
K3 门在复位后再次打开时，已复位标志失效，必须重新复位。
K4 急停期间 ShiftCount 保持不变；运行满 60 s 加 1。

semantic_warnings: []
warnings: []
missing_fields: []
dialect_requirements: []
type_origins: {}

【完整形式化规约；有界时序以扫描周期计】
# task: S12
# meta: medium / D 故障与安全
# spec: version 1.0, updated 2026-10-30, scan cycle 20 ms
# 条款号对齐任务书 3.4 的条款库 C1—C10；
# [a,b] 单位为扫描周期。

C1: G(!EStop_NC -> !MachineRun)
    -- 急停当周期设备必须停（K1）
C2: G(MachineRun -> DoorClosed)
    -- 运行的许可：安全门关闭（K2）
C3: G(StartBtn && !DoorClosed -> X(!MachineRun))
    -- 门未关时按启动不得启动（三步确认缺一不可）（K2/K3）
C4: G(!(MachineRun && AlarmLamp))
    -- 报警期间不得运行（互斥）（K1）
C10: G[0,1](!MachineRun && ShiftCount == 0 && !AlarmLamp)
     -- 上电首周期不运行、计数为 0（初态）

【修改说明与边界选择】
替换占位 RETURN；增加按钮边沿历史、门关闭历史、
复位确认状态以及累计运行扫描计数，保持外部接口不变。
严格按跨扫描顺序确认：先观察门关闭，再接收复位上升沿，
再在后续扫描接收启动上升沿。同扫描复位和启动不能启动。
急停及开门撤销复位许可，按钮历史每扫描均更新；
急停期间按住按钮不能在解除急停后产生虚假上升沿。
门关闭但尚未启动时 Status 为 16#8B02；
AlarmLamp 仅在急停有效时点亮。
运行不足一分钟的累计扫描数在停止期间保留；
累计 3000 个运行扫描加一分钟。
UINT 达到 65535 后饱和，避免溢出；接口无法表示更大分钟数。

【保留并报告的语义冲突】
C10 要求初始两个扫描 AlarmLamp = FALSE，
但控制要求 1 要求任意急停扫描 AlarmLamp = TRUE。
若这两个扫描内 EStop_NC = FALSE，两者无法同时满足。
本实现保留初始变量值，但扫描逻辑优先响应急停，
不为满足 C10 而屏蔽急停报警。
无限运行时“每分钟加 1”亦无法由有限 UINT 无限表示；
采用上述饱和边界，不新增接口。

【验证状态】
当前对话未提供可执行工具、测试命令或编译 profile；
未运行真实编译器或逐周期测试，不声称已经验证正确。
编译通过只证明编译；功能正确必须由逐周期测试判定。
*)

FUNCTION_BLOCK FB_S12
VAR_INPUT
    EStop_NC : BOOL;
    ResetBtn : BOOL;
    StartBtn : BOOL;
    DoorClosed : BOOL;
END_VAR

VAR_OUTPUT
    MachineRun : BOOL := FALSE;
    ShiftCount : UINT := UINT#0;
    AlarmLamp : BOOL := FALSE;
    Status : WORD := WORD#16#0000;
END_VAR

VAR
    ResetConfirmed : BOOL := FALSE;
    ResetBtnLast : BOOL := FALSE;
    StartBtnLast : BOOL := FALSE;
    DoorClosedLast : BOOL := FALSE;
    ResetRise : BOOL := FALSE;
    StartRise : BOOL := FALSE;
    RunScans : UINT := UINT#0;
END_VAR

ResetRise := ResetBtn AND NOT ResetBtnLast;
StartRise := StartBtn AND NOT StartBtnLast;

IF NOT EStop_NC THEN
    MachineRun := FALSE;
    ResetConfirmed := FALSE;
    AlarmLamp := TRUE;
    Status := WORD#16#8B01;

ELSIF NOT DoorClosed THEN
    MachineRun := FALSE;
    ResetConfirmed := FALSE;
    AlarmLamp := FALSE;
    Status := WORD#16#8B03;

ELSE
    AlarmLamp := FALSE;

    (* 先使用此前扫描的复位许可，避免同扫描复位并启动。 *)
    IF NOT MachineRun THEN
        IF ResetConfirmed AND StartRise THEN
            MachineRun := TRUE;
        END_IF;
    END_IF;

    (* 门必须已在前一扫描关闭；急停期间不接收复位。 *)
    IF ResetRise AND DoorClosedLast THEN
        ResetConfirmed := TRUE;
    END_IF;

    IF MachineRun THEN
        Status := WORD#16#0000;
    ELSE
        Status := WORD#16#8B02;
    END_IF;
END_IF;

(* 20 ms × 3000 = 60 s；停止及急停期间保留余数。 *)
IF MachineRun THEN
    RunScans := RunScans + UINT#1;

    IF RunScans >= UINT#3000 THEN
        RunScans := UINT#0;

        IF ShiftCount < UINT#65535 THEN
            ShiftCount := ShiftCount + UINT#1;
        END_IF;
    END_IF;
END_IF;

ResetBtnLast := ResetBtn;
StartBtnLast := StartBtn;
DoorClosedLast := DoorClosed;

END_FUNCTION_BLOCK

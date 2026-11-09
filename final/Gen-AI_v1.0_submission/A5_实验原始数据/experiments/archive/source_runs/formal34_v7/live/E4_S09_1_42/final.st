FUNCTION_BLOCK FB_S09
VAR_INPUT
    StartCIP : BOOL;
    StepDone : BOOL;
    EStop_NC : BOOL;
END_VAR
VAR_OUTPUT
    WaterValve : BOOL := FALSE;
    LyeValve : BOOL := FALSE;
    RinseValve : BOOL := FALSE;
    PumpRun : BOOL := FALSE;
    StepNo : INT := 0;
    Status : WORD := WORD#16#0000;
END_VAR
VAR
    StepTicks : UINT := UINT#0;
    StartCIPLast : BOOL := FALSE;
    StepDoneLast : BOOL := FALSE;
    StartRise : BOOL := FALSE;
    DoneRise : BOOL := FALSE;
END_VAR

(*
    待审语义冲突，不能声称全部规约同时满足：
    1. 原文仅明确 Step 2 可由 StepDone 提前结束；K4 则允许
       当前任意步提前结束。本实现保留原文固定水洗、清水时长，
       仅 Step 2 接受 StepDone 上升沿，K4 的其他解释待审。
    2. C5 使用 StartCIP 电平且未限定急停正常，与上升沿启动及
       急停优先相冲突。本实现只在空闲且急停正常时接受启动沿。
    3. C10 若约束首次执行后的输出始终空闲，则与首次扫描
       StartCIP 上升沿立即启动相冲突。本实现采用所给初态，
       首次扫描仍执行正常逻辑，不额外屏蔽启动沿。
    4. K1 的正常顺序不包含急停/非法步序直接归零；
       此处按明示安全要求将其视为安全中断。

    每次调用代表 20 ms。
    入步扫描计数为零；随后经过 1500/3000/1500 次调用转步，
    对应 30/60/30 s。每次调用最多执行一次正常步序转换。
    Status 表示当前扫描状态，急停解除且步序合法时恢复正常。
    本源码未声称经过编译或逐周期测试验证。
*)

(* 每次扫描都更新边沿记忆，急停期间的启动沿不予保存。 *)
StartRise := StartCIP AND NOT StartCIPLast;
DoneRise := StepDone AND NOT StepDoneLast;
StartCIPLast := StartCIP;
StepDoneLast := StepDone;

(* 先关闭输出，再由最终步号统一映射，避免阀门重叠及泵空转。 *)
WaterValve := FALSE;
LyeValve := FALSE;
RinseValve := FALSE;
PumpRun := FALSE;
Status := WORD#16#0000;

IF NOT EStop_NC THEN
    StepNo := 0;
    StepTicks := UINT#0;
    Status := WORD#16#8902;
ELSIF (StepNo < 0) OR (StepNo > 3) THEN
    StepNo := 0;
    StepTicks := UINT#0;
    Status := WORD#16#8901;
ELSE
    CASE StepNo OF
        0:
            StepTicks := UINT#0;
            IF StartRise THEN
                StepNo := 1;
            END_IF;

        1:
            IF StepTicks < UINT#1500 THEN
                StepTicks := StepTicks + UINT#1;
            END_IF;
            IF StepTicks >= UINT#1500 THEN
                StepNo := 2;
                StepTicks := UINT#0;
            END_IF;

        2:
            IF StepTicks < UINT#3000 THEN
                StepTicks := StepTicks + UINT#1;
            END_IF;
            IF DoneRise OR (StepTicks >= UINT#3000) THEN
                StepNo := 3;
                StepTicks := UINT#0;
            END_IF;

        3:
            IF StepTicks < UINT#1500 THEN
                StepTicks := StepTicks + UINT#1;
            END_IF;
            IF StepTicks >= UINT#1500 THEN
                StepNo := 0;
                StepTicks := UINT#0;
            END_IF;
    END_CASE;
END_IF;

IF EStop_NC AND (Status = WORD#16#0000) THEN
    CASE StepNo OF
        1:
            WaterValve := TRUE;
        2:
            LyeValve := TRUE;
        3:
            RinseValve := TRUE;
    END_CASE;
END_IF;

PumpRun := WaterValve OR LyeValve OR RinseValve;

END_FUNCTION_BLOCK

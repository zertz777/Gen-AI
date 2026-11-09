(*
 任务: S02 输送线正反转与检修锁
 扫描周期: 20 ms
 本文件为 ST 实现，保持给定接口不变。

 语义冲突报告（保留，不声称已验证正确）：
 1) K4 要求 EStop_NC = FALSE 时立即清空死区计时；而 C9 要求某方向输出为 TRUE 后
    的 10 个扫描周期内不得出现反向输出。若急停发生时正转正在运行，按 K4 清空
    死区后，急停解除即可反向，可能在 C9 的 10 周期窗口内出现 MotorRev = TRUE。
    本实现按 K4 优先（急停清空死区并复位最后方向），C9 在该边界条件下可能被
    违反。该冲突来自规约本身，未自行新增接口或修改规约。
 2) 需求 1 要求按钮有效时输出置位；C10 要求上电首周期两方向都不输出。两者在
    首周期相互冲突；本实现以需求 1 / 判定用例为准，首周期即响应按钮。
 3) RunLamp 在非检修态的具体行为未在规约中明确约束（仅要求检修态 1 Hz 闪烁）。
    依据判定用例的观测，本实现取：正常运行态 RunLamp := NOT (MotorFwd OR MotorRev)；
    检修态按 1 Hz 闪烁（前 25 周期亮、后 25 周期灭）；急停时熄灭。
 4) K2 原文仅要求“换向”经过 200 ms 死区；判定用例要求“任何停机后再次启动
    （含同方向重启）”也必须等满 200 ms 死区。本实现按判定用例取更严格行为。
*)
FUNCTION_BLOCK FB_S02
VAR_INPUT
    FwdBtn : BOOL;
    RevBtn : BOOL;
    MaintKey : BOOL;
    EStop_NC : BOOL;
END_VAR
VAR_OUTPUT
    MotorFwd : BOOL;
    MotorRev : BOOL;
    RunLamp : BOOL;
    Status : WORD;
END_VAR
VAR
    DeadCnt : INT := 0;
    LastDir : INT := 0;  (* 0 = 无, 1 = 正转, 2 = 反转 *)
    PrevFwd : BOOL := FALSE;
    PrevRev : BOOL := FALSE;
    BlinkCnt : INT := 0;
END_VAR

(* 记录上一周期输出，用于下降沿检测 *)
PrevFwd := MotorFwd;
PrevRev := MotorRev;

(* 200 ms 死区计时递减（10 个 20 ms 扫描周期） *)
IF DeadCnt > 0 THEN
    DeadCnt := DeadCnt - 1;
END_IF;

(* 输出默认清零，保证正反转互斥（C4） *)
MotorFwd := FALSE;
MotorRev := FALSE;
RunLamp := FALSE;

(* 优先级：急停 > 检修 > 正常运行 *)
IF NOT EStop_NC THEN
    (* C1 / K4：急停当周期两方向断开，清空死区计时 *)
    MotorFwd := FALSE;
    MotorRev := FALSE;
    DeadCnt := 0;
    LastDir := 0;
    RunLamp := FALSE;
    Status := 16#8202;
ELSIF MaintKey THEN
    (* C2 / C2b / K3：检修锁定两方向输出，运行灯 1 Hz 闪烁 *)
    MotorFwd := FALSE;
    MotorRev := FALSE;
    Status := 16#8201;
    (* BlinkCnt 为扫描开始时计数（前一周期值），前 25 周期亮、后 25 周期灭 *)
    IF BlinkCnt < 25 THEN
        RunLamp := TRUE;
    ELSE
        RunLamp := FALSE;
    END_IF;
ELSE
    (* 正常运行 *)
    IF FwdBtn AND NOT RevBtn THEN
        (* 目标方向：正转 *)
        IF DeadCnt > 0 THEN
            (* 处于死区中（含同方向重启），禁止启动（K2 / 判定用例） *)
            Status := 16#8203;
        ELSE
            MotorFwd := TRUE;
            Status := 16#0000;
        END_IF;
    ELSIF RevBtn AND NOT FwdBtn THEN
        (* 目标方向：反转 *)
        IF DeadCnt > 0 THEN
            (* 处于死区中（含同方向重启），禁止启动（K2 / 判定用例） *)
            Status := 16#8203;
        ELSE
            MotorRev := TRUE;
            Status := 16#0000;
        END_IF;
    ELSE
        (* 无有效方向请求（含两按钮同时按下时的互斥处理） *)
        Status := 16#0000;
    END_IF;

    (* 运行灯（非检修态）：电机停止时为 TRUE，电机运行时为 FALSE *)
    RunLamp := NOT (MotorFwd OR MotorRev);
END_IF;

(* 1 Hz 闪烁计数推进：50 周期 = 1 s，半周期 25 周期 = 500 ms *)
IF BlinkCnt < 49 THEN
    BlinkCnt := BlinkCnt + 1;
ELSE
    BlinkCnt := 0;
END_IF;

(* 下降沿处理：输出由运行变为停止时，记录最后方向并启动死区（C9 / K2） *)
IF EStop_NC THEN
    IF PrevFwd AND NOT MotorFwd THEN
        LastDir := 1;
        DeadCnt := 10;
    END_IF;
    IF PrevRev AND NOT MotorRev THEN
        LastDir := 2;
        DeadCnt := 10;
    END_IF;
ELSE
    (* 急停期间死区必须保持为 0（K4） *)
    DeadCnt := 0;
    LastDir := 0;
END_IF;

END_FUNCTION_BLOCK

(* ============================================================ *)
(* FB_S13 : 双段输送合流同步与堵料防撞                          *)
(* 扫描周期: 20 ms                                              *)
(*                                                              *)
(* [语义冲突报告]                                               *)
(*   条款 1 要求 LineRun=FALSE 时 Status 立即写入 16#0000，      *)
(*   条款 4/5 要求堵料报警时 Status=16#8C01 且锁存到复位才清除。 *)
(*   两者在"报警已锁存 且 LineRun=FALSE"这一交叉场景下互相矛盾。 *)
(*   本实现按条款 1 的优先级处理：LineRun=FALSE 时 Status 强制   *)
(*   为 16#0000；JamAlarm 仍保持锁存，LineRun 恢复为 TRUE 后     *)
(*   Status 会重新呈现 16#8C01，直到复位条件满足。               *)
(*                                                              *)
(* [其他实现约定]                                               *)
(*   - ModeAuto=FALSE 只禁用"自动启动"（LineRun 上升沿启动），   *)
(*     总停(C1)、防撞互锁(C4)、堵料报警(C5)仍然生效。            *)
(*   - 堵料计时按 JamSensor 连续 TRUE 计数（不附加 LineRun 前置），*)
(*     符合条款 4 的字面描述。                                   *)
(*   - 计时类状态（堵料报警、升/降档）采用"上一拍累计值判定、     *)
(*     达到阈值后于下一扫描应用"的时序：即 IF timer>=阈值 THEN    *)
(*     动作 ELSE 递增 END_IF。这样连续计时满足阈值后输出晚一拍    *)
(*     生效，避免在阈值当拍提前改变输出。                        *)
(*   - 速度档在不满足升/降条件时保持原档位（不掉档抖动）。       *)
(* ============================================================ *)

FUNCTION_BLOCK FB_S13
VAR_INPUT
    LineRun : BOOL;
    PartAtMerge : BOOL;
    PartOnMain : BOOL;
    JamSensor : BOOL;
    ResetBtn : BOOL;
    ModeAuto : BOOL;
END_VAR
VAR_OUTPUT
    MainMotor : BOOL;
    MergeMotor : BOOL;
    SpeedHigh : BOOL;
    JamAlarm : BOOL;
    Status : WORD;
END_VAR
VAR
    LineRunLast : BOOL := FALSE;
    ResetBtnLast : BOOL := FALSE;
    Started : BOOL := FALSE;
    JamTimer : INT := 0;
    PartHiTimer : INT := 0;
    PartLoTimer : INT := 0;
    LineRunRising : BOOL := FALSE;
    ResetRising : BOOL := FALSE;
END_VAR

(* ---------- 边沿检测 ---------- *)
LineRunRising := LineRun AND NOT LineRunLast;
ResetRising := ResetBtn AND NOT ResetBtnLast;
LineRunLast := LineRun;
ResetBtnLast := ResetBtn;

(* ---------- 堵料连续计时（连续 100 周期 = 2 s） ----------
   先判定上一拍的累计值是否已达阈值，达到则在本次扫描置位报警；
   否则继续累计。这样"连续 100 周期"在第 100 个周期结束后于
   下一扫描生效，避免提前一拍报警。                            *)
IF JamSensor THEN
    IF JamTimer >= 100 THEN
        JamAlarm := TRUE;
    ELSE
        JamTimer := JamTimer + 1;
    END_IF;
ELSE
    JamTimer := 0;
END_IF;

(* ---------- 复位：JamSensor=FALSE 且 ResetBtn 上升沿（C6 / 条款 5） ---------- *)
IF ResetRising AND NOT JamSensor THEN
    JamAlarm := FALSE;
END_IF;

(* ---------- 启动锁存（C2 / 条款 2 / 条款 7） ----------
   LineRun 上升沿 且 无报警 且 自动模式 ---------- *)
IF LineRunRising AND NOT JamAlarm AND ModeAuto THEN
    Started := TRUE;
END_IF;

(* ---------- 停机条件（C1 总停 / 堵料停机） ----------
   这里把 Started 清掉，从而保证"复位后必须重新给 LineRun 上升沿"才允许再启动 *)
IF (NOT LineRun) OR JamAlarm THEN
    Started := FALSE;
END_IF;

(* ---------- 电机输出（C1 / C2 / C4 / 条款 3） ---------- *)
IF LineRun AND Started AND NOT JamAlarm THEN
    MainMotor := TRUE;
ELSE
    MainMotor := FALSE;
END_IF;

(* 防撞互锁：合流段有料时汇流段不得送料 *)
IF MainMotor AND NOT PartAtMerge THEN
    MergeMotor := TRUE;
ELSE
    MergeMotor := FALSE;
END_IF;

(* ---------- 速度档：有料 3 s(150) 升高速，无料 5 s(250) 降低速（C7 / K5） ----------
   同样采用"上一拍累计值判定、达到阈值后于下一扫描应用"，避免提前一拍换档。 *)
IF MainMotor AND PartOnMain THEN
    IF PartHiTimer >= 150 THEN
        SpeedHigh := TRUE;
    ELSE
        PartHiTimer := PartHiTimer + 1;
    END_IF;
    PartLoTimer := 0;
ELSIF MainMotor AND NOT PartOnMain THEN
    IF PartLoTimer >= 250 THEN
        SpeedHigh := FALSE;
    ELSE
        PartLoTimer := PartLoTimer + 1;
    END_IF;
    PartHiTimer := 0;
ELSE
    (* 电机停止：清两个时限计时器，SpeedHigh 保持原档位 *)
    PartHiTimer := 0;
    PartLoTimer := 0;
END_IF;

(* ---------- 总停 / 报警：对 SpeedHigh 与 Status 的强制覆盖 ---------- *)
IF NOT LineRun THEN
    SpeedHigh := FALSE;
    Status := 16#0000;
ELSIF JamAlarm THEN
    Status := 16#8C01;
ELSE
    Status := 16#0000;
END_IF;

END_FUNCTION_BLOCK

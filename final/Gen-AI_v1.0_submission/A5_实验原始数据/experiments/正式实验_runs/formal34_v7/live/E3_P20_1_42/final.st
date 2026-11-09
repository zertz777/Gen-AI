(* 冲突报告：原文要求称重不合格时立即启动 kick；形式化 C2 要求 G(kick -> SensorOutput)，
   即 kick 仅可在成品站 SensorOutput=TRUE 时输出。本实现按 C2 将不合格标志 rejected
   延迟到成品站 SensorOutput=TRUE 时执行 kick；未新增接口。若需称重站立即剔除，需澄清/修改规约。 *)

TYPE P20_STATE :
(
    S_IDLE,
    S_TO_WASH,
    S_WAIT_WASH,
    S_TO_WEIGHT,
    S_WAIT_WEIGHT,
    S_TO_FIRING,
    S_WAIT_FIRING,
    S_TO_OUTPUT,
    S_AT_OUTPUT
);
END_TYPE

FUNCTION_BLOCK FB_P20
VAR_INPUT
    Mode : BOOL;
    ForwardButton : BOOL;
    ReverseButton : BOOL;
    SensorFeed : BOOL;
    SensorWash : BOOL;
    SensorWeight : BOOL;
    SensorFiring : BOOL;
    SensorOutput : BOOL;
    washComplete : BOOL;
    weightComplete : BOOL;
    weight : REAL;
    firingComplete : BOOL;
END_VAR
VAR_OUTPUT
    MotorForward : BOOL;
    MotorReverse : BOOL;
    kick : BOOL;
    CompletionLight : BOOL;
    firingTemp : REAL;
END_VAR
VAR
    state : P20_STATE := S_IDLE;
    rejected : BOOL := FALSE;
    kicked : BOOL := FALSE;
    prevMode : BOOL := FALSE;
    startupCnt : INT := 0;
END_VAR

(* C10: 上电初始阶段无输出，覆盖 G[0,1] 区间。 *)
IF startupCnt < 2 THEN
    MotorForward := FALSE;
    MotorReverse := FALSE;
    kick := FALSE;
    CompletionLight := FALSE;
    firingTemp := 0.0;
    state := S_IDLE;
    rejected := FALSE;
    kicked := FALSE;
    prevMode := Mode;
    startupCnt := startupCnt + 1;
ELSE
    IF Mode THEN
        (* 自动模式：手动切自动时复位自动流程。 *)
        IF NOT prevMode THEN
            state := S_IDLE;
            rejected := FALSE;
            kicked := FALSE;
            CompletionLight := FALSE;
            kick := FALSE;
            MotorForward := FALSE;
            MotorReverse := FALSE;
            firingTemp := 0.0;
        END_IF;

        (* 自动模式默认输出。 *)
        MotorForward := FALSE;
        MotorReverse := FALSE;
        kick := FALSE;
        CompletionLight := FALSE;

        CASE state OF
            S_IDLE:
                (* 上料站到位后启动正转去清洗站。 *)
                IF SensorFeed THEN
                    MotorForward := TRUE;
                    state := S_TO_WASH;
                END_IF;

            S_TO_WASH:
                IF SensorWash THEN
                    MotorForward := FALSE;
                    state := S_WAIT_WASH;
                ELSE
                    MotorForward := TRUE;
                END_IF;

            S_WAIT_WASH:
                (* K3: 完成信号必须与到位传感器一致。 *)
                IF SensorWash AND washComplete THEN
                    MotorForward := TRUE;
                    state := S_TO_WEIGHT;
                END_IF;

            S_TO_WEIGHT:
                IF SensorWeight THEN
                    MotorForward := FALSE;
                    state := S_WAIT_WEIGHT;
                ELSE
                    MotorForward := TRUE;
                END_IF;

            S_WAIT_WEIGHT:
                IF SensorWeight AND weightComplete THEN
                    IF (weight >= 100.0) AND (weight <= 200.0) THEN
                        (* 合格：100..200 线性映射到 500..550。 *)
                        rejected := FALSE;
                        firingTemp := 500.0 + (weight - 100.0) * 0.5;
                        MotorForward := TRUE;
                        state := S_TO_FIRING;
                    ELSE
                        (* 不合格：按 C2 延迟到成品站输出 kick。 *)
                        rejected := TRUE;
                        firingTemp := 0.0;
                        MotorForward := TRUE;
                        state := S_TO_FIRING;
                    END_IF;
                END_IF;

            S_TO_FIRING:
                IF SensorFiring THEN
                    MotorForward := FALSE;
                    state := S_WAIT_FIRING;
                ELSE
                    MotorForward := TRUE;
                END_IF;

            S_WAIT_FIRING:
                IF SensorFiring AND firingComplete THEN
                    MotorForward := TRUE;
                    state := S_TO_OUTPUT;
                END_IF;

            S_TO_OUTPUT:
                IF SensorOutput THEN
                    MotorForward := FALSE;
                    state := S_AT_OUTPUT;
                    kicked := FALSE;
                ELSE
                    MotorForward := TRUE;
                END_IF;

            S_AT_OUTPUT:
                IF NOT SensorOutput THEN
                    (* 产品离开成品站：熄灭完成灯并复位。 *)
                    CompletionLight := FALSE;
                    kick := FALSE;
                    rejected := FALSE;
                    kicked := FALSE;
                    firingTemp := 0.0;
                    state := S_IDLE;
                ELSE
                    IF rejected AND NOT kicked THEN
                        (* C2: kick 仅在 SensorOutput=TRUE 时输出。 *)
                        kick := TRUE;
                        CompletionLight := FALSE;
                        kicked := TRUE;
                    ELSE
                        (* K4/C1/C6: 出料动作后点亮并保持到产品离开。 *)
                        kick := FALSE;
                        CompletionLight := TRUE;
                    END_IF;
                END_IF;
        END_CASE;

        prevMode := TRUE;
    ELSE
        (* 手动模式：正反转互斥。 *)
        MotorForward := ForwardButton AND NOT ReverseButton;
        MotorReverse := ReverseButton AND NOT ForwardButton;
        kick := FALSE;
        CompletionLight := FALSE;
        firingTemp := 0.0;
        state := S_IDLE;
        rejected := FALSE;
        kicked := FALSE;
        prevMode := FALSE;
    END_IF;
END_IF;

END_FUNCTION_BLOCK

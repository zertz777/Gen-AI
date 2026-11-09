TYPE P11_State :
(
    P11_IDLE,
    P11_MOVE_TO_B,
    P11_WAIT_B,
    P11_MOVE_TO_C,
    P11_WAIT_C,
    P11_DONE
);
END_TYPE

FUNCTION_BLOCK FB_P11
VAR_INPUT
    Mode : BOOL;
    ForwardButton : BOOL;
    ReverseButton : BOOL;
    SensorA : BOOL;
    SensorB : BOOL;
    SensorC : BOOL;
    ButtonA : BOOL;
    ButtonB : BOOL;
    ButtonC : BOOL;
END_VAR
VAR_OUTPUT
    MotorForward : BOOL;
    MotorReverse : BOOL;
    CompletionLight : BOOL;
END_VAR
VAR
    State : P11_State := P11_IDLE;
    FirstScan : BOOL := TRUE;
    ButtonATrig : R_TRIG;
    ButtonBTrig : R_TRIG;
    ButtonCTrig : R_TRIG;
END_VAR

ButtonATrig(CLK := ButtonA);
ButtonBTrig(CLK := ButtonB);
ButtonCTrig(CLK := ButtonC);

IF FirstScan THEN
    MotorForward := FALSE;
    MotorReverse := FALSE;
    CompletionLight := FALSE;
    State := P11_IDLE;
    FirstScan := FALSE;
ELSE
    IF NOT Mode THEN
        (* 手动模式：正反转按钮控制，软件互锁 *)
        State := P11_IDLE;
        IF ForwardButton AND NOT ReverseButton THEN
            MotorForward := TRUE;
            MotorReverse := FALSE;
        ELSIF ReverseButton AND NOT ForwardButton THEN
            MotorForward := FALSE;
            MotorReverse := TRUE;
        ELSE
            MotorForward := FALSE;
            MotorReverse := FALSE;
        END_IF;
    ELSE
        (* 自动模式：A -> B -> C 顺序推进 *)
        MotorForward := FALSE;
        MotorReverse := FALSE;

        CASE State OF
            P11_IDLE:
                IF SensorA AND ButtonATrig.Q THEN
                    State := P11_MOVE_TO_B;
                    MotorForward := TRUE;
                    MotorReverse := FALSE;
                END_IF;

            P11_MOVE_TO_B:
                IF SensorB THEN
                    State := P11_WAIT_B;
                    MotorForward := FALSE;
                    MotorReverse := FALSE;
                ELSE
                    MotorForward := TRUE;
                    MotorReverse := FALSE;
                END_IF;

            P11_WAIT_B:
                IF NOT SensorB THEN
                    State := P11_IDLE;
                    MotorForward := FALSE;
                    MotorReverse := FALSE;
                ELSIF SensorB AND ButtonBTrig.Q THEN
                    State := P11_MOVE_TO_C;
                    MotorForward := TRUE;
                    MotorReverse := FALSE;
                END_IF;

            P11_MOVE_TO_C:
                IF SensorC THEN
                    State := P11_WAIT_C;
                    MotorForward := FALSE;
                    MotorReverse := FALSE;
                ELSE
                    MotorForward := TRUE;
                    MotorReverse := FALSE;
                END_IF;

            P11_WAIT_C:
                IF NOT SensorC THEN
                    State := P11_IDLE;
                    MotorForward := FALSE;
                    MotorReverse := FALSE;
                ELSIF SensorC AND ButtonCTrig.Q THEN
                    CompletionLight := TRUE;
                    State := P11_DONE;
                END_IF;

            P11_DONE:
                IF NOT SensorC THEN
                    CompletionLight := FALSE;
                    State := P11_IDLE;
                END_IF;
        END_CASE;
    END_IF;

    (* 硬互锁：正转与反转不能同时为 TRUE *)
    IF MotorForward AND MotorReverse THEN
        MotorForward := FALSE;
        MotorReverse := FALSE;
    END_IF;

    (* 完成灯保持到 C 站产品离开；无产品时强制熄灭 *)
    IF NOT SensorC THEN
        CompletionLight := FALSE;
    END_IF;
END_IF;
END_FUNCTION_BLOCK

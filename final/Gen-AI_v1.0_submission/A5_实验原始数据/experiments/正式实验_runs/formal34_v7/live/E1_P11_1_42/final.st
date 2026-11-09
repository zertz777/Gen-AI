FUNCTION_BLOCK FB_P11
VAR_INPUT
    Mode : BOOL;            (* 0=手动, 1=自动 *)
    ForwardButton : BOOL;   (* 手动正转按钮 *)
    ReverseButton : BOOL;   (* 手动反转按钮 *)
    SensorA : BOOL;         (* A站到位 *)
    SensorB : BOOL;         (* B站到位 *)
    SensorC : BOOL;         (* C站到位 *)
    ButtonA : BOOL;         (* A站完成按钮 *)
    ButtonB : BOOL;         (* B站完成按钮 *)
    ButtonC : BOOL;         (* C站完成按钮 *)
END_VAR
VAR_OUTPUT
    MotorForward : BOOL;    (* 电机正转 *)
    MotorReverse : BOOL;    (* 电机反转 *)
    CompletionLight : BOOL; (* 完成指示灯 *)
END_VAR
VAR
    (* 自动模式工位状态机（K2：只能 A->B->C，不得跳站/回流）
       0 = 等待A站到位并触发完成按钮
       1 = A 到 B 输送中
       2 = 等待B站到位并触发完成按钮
       3 = B 到 C 输送中
       4 = 等待C站完成按钮 / 产品离开C站 *)
    State : INT := 0;
    (* C站完成锁存（K4：完成后置位，产品离开C站时复位） *)
    C_Complete : BOOL := FALSE;
END_VAR

(* ================= 电机与工位推进 ================= *)
IF Mode THEN
    (* -------- 自动模式（K2/K3：逐站推进，可正转不可反转） -------- *)
    MotorForward := FALSE;
    MotorReverse := FALSE;
    CASE State OF
        0:  (* 等待A站：SensorA + ButtonA 缺一不可 *)
            IF SensorA AND ButtonA THEN
                MotorForward := TRUE;
                State := 1;
            END_IF;
        1:  (* A->B 输送中，到达B站即停止 *)
            IF SensorB THEN
                State := 2;
            ELSE
                MotorForward := TRUE;
            END_IF;
        2:  (* 等待B站：SensorB + ButtonB 缺一不可 *)
            IF SensorB AND ButtonB THEN
                MotorForward := TRUE;
                State := 3;
            END_IF;
        3:  (* B->C 输送中，到达C站即停止 *)
            IF SensorC THEN
                State := 4;
            ELSE
                MotorForward := TRUE;
            END_IF;
        4:  (* 等待C站完成：SensorC + ButtonC *)
            IF SensorC AND ButtonC THEN
                C_Complete := TRUE;
            END_IF;
        ELSE
            State := 0;
    END_CASE;
ELSE
    (* -------- 手动模式（K1：正反转互锁；正转优先，反转被正转封锁） --------
       - 两者同时按下：MotorForward=TRUE，MotorReverse=FALSE（仍满足 K1/C4/C2）
       - 单独按下：对应方向动作，另一方向为 FALSE *)
    MotorForward := ForwardButton;
    MotorReverse := ReverseButton AND NOT ForwardButton;
END_IF;

(* ============ C站产品离开：复位完成锁存并回到等待A站 ============ *)
IF NOT SensorC THEN
    C_Complete := FALSE;
    IF State = 4 THEN
        State := 0;
    END_IF;
END_IF;

(* ================= 完成灯 =================
   C3: 点灯必须以 SensorC 为真为前提
   C6: 点亮后保持到产品离开C站（SensorC 变假） *)
CompletionLight := SensorC AND C_Complete;

END_FUNCTION_BLOCK

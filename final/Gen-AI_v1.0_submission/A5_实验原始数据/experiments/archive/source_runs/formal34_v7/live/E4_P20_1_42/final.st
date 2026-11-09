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
    MotorForward : BOOL := FALSE;
    MotorReverse : BOOL := FALSE;
    kick : BOOL := FALSE;
    CompletionLight : BOOL := FALSE;
    firingTemp : REAL := 0.0;
END_VAR
VAR
    startupScans : INT := 0;
    stationState : INT := 0;
    previousLight : BOOL := FALSE;
END_VAR

(*
需求原文：
An automated production line consists of 5 workstations: material loading
station, cleaning station, weighing station, firing station, and finished
product station. The production line has a motor responsible for moving
products from one workstation to the next, the sequence of the line is from
the material loading station, cleaning station, weighing station, firing
station, to the finished product station. Each workstation has a sensor
(used to detect if the product has arrived).
Control requirements:
1. Mode Switching: The mode switch (Mode) is used to switch between manual
and automatic modes of the production line. 0 = manual mode, 1 = automatic mode.
2. Manual Mode: In manual mode, the forward rotation button (ForwardButton)
controls the forward rotation of the motor, and the reverse rotation button
(ReverseButton) controls the reverse rotation of the motor. Forward and reverse
rotation operations need to be interlocked and cannot be performed simultaneously.
3. Automatic Mode:
   - When the material arrives at the material loading station, the SensorFeed
detects the material, the motor starts forward rotation, and moves the material
to the cleaning station.
   - When the material arrives at the cleaning station, the SensorWash detects
the material, the motor stops, and upon receiving the signal washComplete after
cleaning is finished, the motor starts forward rotation, moving the material
to the weighing station.
   - When the material arrives at the weighing station, the SensorWeight detects
the material, the motor stops, and upon receiving weightComplete after weighing
is complete, the material is judged to be qualified based on the weight value.
If the weight value is greater than or equal to 100 and less than or equal to
200, it is qualified, otherwise not.
     If the material is unqualified, the rejection command kick is initiated.
     If the material is qualified, the firing temperature is calculated based
on the weight value. The calculation rule is that the weight value from 100
to 200 linearly corresponds to the temperature value from 500 to 550. The firing
temperature firingTemp is output. At the same time, the motor starts forward
rotation, moving the material to the firing station.
   - When the product arrives at the firing station, the SensorFiring detects
the material, the motor stops, and upon receiving the signal firingComplete
after firing is finished, the motor starts forward rotation, moving the product
to the finished product station.
   - When the product arrives at the finished product station, the SensorOutput
detects the product, the motor stops, and the completion light (CompletionLight)
turns on, indicating that the product processing is complete. When the product
is taken away, i.e., the SensorOutput does not detect the product, the completion
light (CompletionLight) turns off.

中文摘要：五工位生产线：手动正反转互斥，自动按上料→清洗→称重→烧成→成品
顺序推进，各工位完成信号触发推进，成品站执行 kick 动作。

数据冲突报告，待审：
1. 英文要求称重不合格立即 kick；K4/C2 要求 kick 只能在成品站到位时执行。
   称重到位并不保证 SensorOutput，因此这些要求不能对所有输入同时满足。
   本实现保留冲突：不合格进入状态 90，停机保持，禁止 kick，不擅自将不合格
   产品送往烧成或成品站。此分支等待需求澄清，没有新增恢复接口。
2. 英文要求成品到位立即亮灯；K4 要求出料动作之后亮灯。
   本实现采用先单扫描 kick、下一扫描仍到位才亮灯的 K4 时序。
3. C10 的 G[0,1] 按包含端点的周期索引要求首两次调用输出关闭；
   “上电首周期”文字只描述一次。本实现保留较严格的首两扫描禁止输出。
上述冲突不能因代码生成或编译通过而视为已解决。
没有编译或逐周期测试验证声明。

每次调用为 20 ms。状态：
0 IDLE；10 去清洗；20 清洗等待；30 去称重；40 称重等待；
50 去烧成；60 烧成等待；70 去成品；80 已执行出料；
81 成品保持；90 不合格待审停机。

完成信号按电平处理，并必须与对应到位传感器同时有效。
到位扫描先停机，随后扫描才处理该工位完成信号。
手动模式暂停自动状态，不清除完成灯或自动工序。
双按钮同时按下时两个方向均关闭。
firingTemp 在合格称重完成时更新，其余扫描保持。
*)

previousLight := CompletionLight;
MotorForward := FALSE;
MotorReverse := FALSE;
kick := FALSE;

IF startupScans < 2 THEN
    startupScans := startupScans + 1;
    stationState := 0;
    CompletionLight := FALSE;
    firingTemp := 0.0;
ELSE
    (* 灯保持不受模式切换影响，只在产品离开时清除。 *)
    IF NOT SensorOutput THEN
        CompletionLight := FALSE;
    END_IF;

    IF NOT Mode THEN
        MotorForward := ForwardButton AND NOT ReverseButton;
        MotorReverse := ReverseButton AND NOT ForwardButton;
    ELSE
        CASE stationState OF
            0:
                IF SensorFeed AND NOT CompletionLight THEN
                    stationState := 10;
                    MotorForward := NOT SensorWash;
                END_IF;

            10:
                IF SensorWash THEN
                    stationState := 20;
                ELSE
                    MotorForward := TRUE;
                END_IF;

            20:
                IF SensorWash AND washComplete THEN
                    stationState := 30;
                    MotorForward := NOT SensorWeight;
                END_IF;

            30:
                IF SensorWeight THEN
                    stationState := 40;
                ELSE
                    MotorForward := TRUE;
                END_IF;

            40:
                IF SensorWeight AND weightComplete THEN
                    IF (weight >= 100.0) AND (weight <= 200.0) THEN
                        firingTemp := 500.0 + (weight - 100.0) * 0.5;
                        stationState := 50;
                        MotorForward := NOT SensorFiring;
                    ELSE
                        (* 待审冲突：不得在称重站擅自执行成品站 kick。 *)
                        stationState := 90;
                    END_IF;
                END_IF;

            50:
                IF SensorFiring THEN
                    stationState := 60;
                ELSE
                    MotorForward := TRUE;
                END_IF;

            60:
                IF SensorFiring AND firingComplete THEN
                    stationState := 70;
                    MotorForward := NOT SensorOutput;
                END_IF;

            70:
                IF SensorOutput THEN
                    IF NOT CompletionLight AND NOT previousLight THEN
                        kick := TRUE;
                        stationState := 80;
                    END_IF;
                ELSE
                    MotorForward := TRUE;
                END_IF;

            80:
                (* 出料脉冲已在前一个自动执行扫描输出。 *)
                IF SensorOutput THEN
                    CompletionLight := TRUE;
                    stationState := 81;
                ELSE
                    stationState := 0;
                END_IF;

            81:
                IF NOT SensorOutput THEN
                    stationState := 0;
                END_IF;

            90:
                (* 不合格待审保持：所有运动及 kick 均保持关闭。 *)
                MotorForward := FALSE;
                MotorReverse := FALSE;
                kick := FALSE;

            ELSE
                (* 非法内部状态安全停机，不自动跳站。 *)
                stationState := 90;
        END_CASE;
    END_IF;
END_IF;

(* 最终输出防护：到位前提、完成灯下一扫描约束、方向互锁。 *)
IF (NOT SensorOutput) OR previousLight THEN
    kick := FALSE;
END_IF;

IF MotorForward AND MotorReverse THEN
    MotorForward := FALSE;
    MotorReverse := FALSE;
END_IF;
END_FUNCTION_BLOCK

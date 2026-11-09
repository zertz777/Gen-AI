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
    tempHold : REAL := 0.0;
    lastMF : BOOL := FALSE;
    lastMR : BOOL := FALSE;
    qualified : BOOL := FALSE;
END_VAR

(*
  语义冲突（保留并报告, 不静默消除）:
  1) 需求原文: 在称重工位对不合格品发出 kick 剔除 (本实现遵循, 见自动分支)。
     约束 K4 与形式规约 C2 又要求 kick 只能发生在成品工位且 G(kick -> SensorOutput)。
     二者不可能同时成立，冲突保留上报。
  2) 形式规约 C10 G[0,1](无输出) 要求上电周期输出为 FALSE;
     而给定逐周期测试在首次调用即驱动输入并期望立即输出。二者不可能同时成立,
     本实现按测试时序立即响应, 冲突保留上报。
*)

(* 每个扫描周期的默认输出 *)
MotorForward := FALSE;
MotorReverse := FALSE;
kick := FALSE;
CompletionLight := FALSE;

IF NOT Mode THEN
    (* ---------- 手动模式 ----------
       K1: 正反转互斥；方向切换需要一个扫描周期的死区 (互锁记忆) *)
    IF ForwardButton AND NOT ReverseButton AND NOT lastMR THEN
        MotorForward := TRUE;
    ELSIF ReverseButton AND NOT ForwardButton AND NOT lastMF THEN
        MotorReverse := TRUE;
    END_IF;
    firingTemp := 0.0;
    tempHold := 0.0;
ELSE
    (* ---------- 自动模式 ----------
       工位顺序 上料->清洗->称重->烧成->成品, 由到位传感器与完成信号推进,
       传感器序列天然保证不跳站 (K2)。 *)
    qualified := (weight >= 100.0) AND (weight <= 200.0);

    IF SensorFeed THEN
        (* 上料站: 正转送清洗站 *)
        MotorForward := TRUE;
    ELSIF SensorWash AND washComplete THEN
        (* 清洗站: 清洗完成才推进 *)
        MotorForward := TRUE;
    ELSIF SensorWeight AND weightComplete THEN
        (* 称重站: 到位停转; 完成信号到达后判定 *)
        IF qualified THEN
            (* 合格: 100..200 线性映射 500..550, 推进到烧成站 *)
            tempHold := 500.0 + (weight - 100.0) * 0.5;
            MotorForward := TRUE;
        ELSE
            (* 不合格: 在称重站剔除, 不推进 (遵循需求原文) *)
            kick := TRUE;
        END_IF;
    ELSIF SensorFiring AND firingComplete THEN
        (* 烧成站: 烧成完成才推进到成品站 *)
        MotorForward := TRUE;
    END_IF;

    (* 成品站: 到位点亮完成灯, 产品取走后熄灭 (C6) *)
    IF SensorOutput THEN
        CompletionLight := TRUE;
    END_IF;

    firingTemp := tempHold;
END_IF;

lastMF := MotorForward;
lastMR := MotorReverse;

END_FUNCTION_BLOCK

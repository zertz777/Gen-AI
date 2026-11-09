FUNCTION_BLOCK FB_P15
VAR_INPUT
    estop : BOOL;
    opeMode : BOOL;
    valveAStart : BOOL;
    valveBStart : BOOL;
    valveCStart : BOOL;
    valveDStart : BOOL;
    mixMotorStart : BOOL;
    autoStart : BOOL;
    processMode : BOOL;
    levelSensor : INT;
    mixMotorComplete : BOOL;
END_VAR
VAR_OUTPUT
    valveARun : BOOL;
    valveBRun : BOOL;
    valveCRun : BOOL;
    valveDRun : BOOL;
    mixMotorRun : BOOL;
END_VAR
VAR
    (* ---- 输入边沿检测 ---- *)
    prevValveAStart  : BOOL;
    prevValveBStart  : BOOL;
    prevValveCStart  : BOOL;
    prevValveDStart  : BOOL;
    prevMixMotorStart: BOOL;
    prevAutoStart    : BOOL;
    prevOpeMode      : BOOL;

    reValveAStart    : BOOL;
    reValveBStart    : BOOL;
    reValveCStart    : BOOL;
    reValveDStart    : BOOL;
    reMixMotorStart  : BOOL;
    reAutoStart      : BOOL;

    (* ---- 手动模式锁存 ---- *)
    manValveA   : BOOL;
    manValveB   : BOOL;
    manValveC   : BOOL;
    manValveD   : BOOL;
    manMixMotor : BOOL;

    (* ---- 自动模式状态 ---- *)
    (* autoState: 0=空闲 1=开A进料 2=开B进料 3=开C进料 4=混料 5=出料 *)
    autoState    : INT;
    autoValveA   : BOOL;
    autoValveB   : BOOL;
    autoValveC   : BOOL;
    autoValveD   : BOOL;
    autoMixMotor : BOOL;
END_VAR

(* ============================================================ *)
(* 输入上升沿检测（每周期执行）                                   *)
(* ============================================================ *)
reValveAStart   := valveAStart   AND NOT prevValveAStart;
reValveBStart   := valveBStart   AND NOT prevValveBStart;
reValveCStart   := valveCStart   AND NOT prevValveCStart;
reValveDStart   := valveDStart   AND NOT prevValveDStart;
reMixMotorStart := mixMotorStart AND NOT prevMixMotorStart;
reAutoStart     := autoStart     AND NOT prevAutoStart;

(* ============================================================ *)
(* C1 / C2 / K1 / K4: 急停（estop=FALSE）                       *)
(* 当周期立即停止全部设备，内部步序复位到安全态；                *)
(* 恢复后必须重新按 autoStart 从安全步开始，不续跑。             *)
(* ============================================================ *)
IF NOT estop THEN

    valveARun   := FALSE;
    valveBRun   := FALSE;
    valveCRun   := FALSE;
    valveDRun   := FALSE;
    mixMotorRun := FALSE;

    manValveA   := FALSE;
    manValveB   := FALSE;
    manValveC   := FALSE;
    manValveD   := FALSE;
    manMixMotor := FALSE;

    autoValveA   := FALSE;
    autoValveB   := FALSE;
    autoValveC   := FALSE;
    autoValveD   := FALSE;
    autoMixMotor := FALSE;
    autoState    := 0;

ELSE

    (* -------------------------------------------------- *)
    (* 模式切换：清空另一模式遗留的内部指令，避免跳变       *)
    (* -------------------------------------------------- *)
    IF opeMode <> prevOpeMode THEN
        manValveA   := FALSE;
        manValveB   := FALSE;
        manValveC   := FALSE;
        manValveD   := FALSE;
        manMixMotor := FALSE;

        autoValveA   := FALSE;
        autoValveB   := FALSE;
        autoValveC   := FALSE;
        autoValveD   := FALSE;
        autoMixMotor := FALSE;
        autoState    := 0;
    END_IF;

    IF opeMode THEN
        (* ================= 自动模式 (K3) ================= *)
        CASE autoState OF

            0:  (* 空闲：等待 autoStart 上升沿启动 *)
                IF reAutoStart THEN
                    autoValveA   := TRUE;
                    autoValveB   := FALSE;
                    autoValveC   := FALSE;
                    autoValveD   := FALSE;
                    autoMixMotor := FALSE;
                    autoState    := 1;
                END_IF;

            1:  (* 阀 A 进料；液位到 50cm 关 A 开 B *)
                IF levelSensor >= 50 THEN
                    autoValveA := FALSE;
                    autoValveB := TRUE;
                    autoState  := 2;
                END_IF;

            2:  (* 阀 B 进料；液位到 80cm 关 B 后按 processMode 分流 *)
                IF levelSensor >= 80 THEN
                    autoValveB := FALSE;
                    IF processMode THEN
                        (* 需要第三组分：先开 C *)
                        autoValveC := TRUE;
                        autoState  := 3;
                    ELSE
                        (* 两组分：直接进入混料 *)
                        autoMixMotor := TRUE;
                        autoState    := 4;
                    END_IF;
                END_IF;

            3:  (* 阀 C 进料；液位到 100cm 关 C 后启动混料 *)
                IF levelSensor >= 100 THEN
                    autoValveC   := FALSE;
                    autoMixMotor := TRUE;
                    autoState    := 4;
                END_IF;

            4:  (* 混料保持运行，直到收到完成信号 (C6) *)
                IF mixMotorComplete THEN
                    autoMixMotor := FALSE;
                    autoValveD   := TRUE;
                    autoState    := 5;
                END_IF;

            5:  (* 出料阀 D 保持开启，自动流程结束；再次 autoStart 重新开始 *)
                IF reAutoStart THEN
                    autoValveA   := TRUE;
                    autoValveB   := FALSE;
                    autoValveC   := FALSE;
                    autoValveD   := FALSE;
                    autoMixMotor := FALSE;
                    autoState    := 1;
                END_IF;

        END_CASE;

    ELSE
        (* ================= 手动模式 (K2) ================= *)
        (* 每个按钮上升沿翻转对应设备；同时保证 D 与 A/B/C 互斥 (C4) *)
        IF reValveAStart THEN
            manValveA := NOT manValveA;
            IF manValveA THEN
                manValveD := FALSE;
            END_IF;
        END_IF;

        IF reValveBStart THEN
            manValveB := NOT manValveB;
            IF manValveB THEN
                manValveD := FALSE;
            END_IF;
        END_IF;

        IF reValveCStart THEN
            manValveC := NOT manValveC;
            IF manValveC THEN
                manValveD := FALSE;
            END_IF;
        END_IF;

        IF reValveDStart THEN
            manValveD := NOT manValveD;
            IF manValveD THEN
                manValveA := FALSE;
                manValveB := FALSE;
                manValveC := FALSE;
            END_IF;
        END_IF;

        IF reMixMotorStart THEN
            manMixMotor := NOT manMixMotor;
        END_IF;
    END_IF;

    (* -------------------------------------------------- *)
    (* 输出合并：仅当前模式的状态参与输出                   *)
    (* -------------------------------------------------- *)
    IF opeMode THEN
        valveARun   := autoValveA;
        valveBRun   := autoValveB;
        valveCRun   := autoValveC;
        valveDRun   := autoValveD;
        mixMotorRun := autoMixMotor;
    ELSE
        valveARun   := manValveA;
        valveBRun   := manValveB;
        valveCRun   := manValveC;
        valveDRun   := manValveD;
        mixMotorRun := manMixMotor;
    END_IF;

    (* C4: 出料阀 D 与配比阀 A/B/C 互斥（D 优先，作为最后保护） *)
    IF valveDRun THEN
        valveARun := FALSE;
        valveBRun := FALSE;
        valveCRun := FALSE;
    END_IF;

END_IF;

(* ============================================================ *)
(* 每周期末无条件更新输入历史值                                   *)
(* ============================================================ *)
prevValveAStart   := valveAStart;
prevValveBStart   := valveBStart;
prevValveCStart   := valveCStart;
prevValveDStart   := valveDStart;
prevMixMotorStart := mixMotorStart;
prevAutoStart     := autoStart;
prevOpeMode       := opeMode;

END_FUNCTION_BLOCK

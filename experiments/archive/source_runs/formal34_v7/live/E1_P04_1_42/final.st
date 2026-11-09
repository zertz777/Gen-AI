FUNCTION_BLOCK FB_P04
VAR_INPUT
    VISCOSITY_OK : BOOL;
    PASTE_E_STOP_NC : BOOL;
    DebounceTime : TIME;
    CycleTime : TIME;
END_VAR
VAR_OUTPUT
    VFD_RUN : BOOL;
    PUMP_MAINT_DUE : BOOL;
    PUMP_RUNTIME_ACC : LTIME;
END_VAR
VAR
    DebounceElapsed : TIME;   (* 粘度信号连续有效累计时间 (K2)，TIME 域 *)
    ViscosityValid : BOOL;    (* 去抖后的粘度有效条件 *)
    CycleTimeLT : LTIME;      (* 本周期调用间隔，显式转为 LTIME 供 LTIME 域累加 *)
END_VAR

(* -------------------------------------------------------------------- *)
(* 上电初态 (K5 / C10)：                                                *)
(*   VFD_RUN = FALSE, PUMP_RUNTIME_ACC = 0, PUMP_MAINT_DUE = FALSE,       *)
(*   去抖计时清零。由 IEC 冷启动的非保持变量默认值保证（BOOL=FALSE，     *)
(*   数值时间型=0），因此无需单独占用一个扫描周期做初始化。              *)
(* -------------------------------------------------------------------- *)

(* 显式转换本周期实际调用间隔，之后仅在 LTIME 域内做同类型算术。 *)
CycleTimeLT := TIME_TO_LTIME(CycleTime);

(* -------------------------------------------------------------------- *)
(* K1/K2：急停有效或粘度原始信号为 FALSE 时立即清零未完成的去抖计时；    *)
(* 仅在安全回路允许且粘度信号为 TRUE 时累计，保证“连续为真”语义。        *)
(* -------------------------------------------------------------------- *)
IF PASTE_E_STOP_NC AND VISCOSITY_OK THEN
    DebounceElapsed := DebounceElapsed + CycleTime;
ELSE
    DebounceElapsed := T#0ms;
END_IF;

(* 连续达到 DebounceTime 才算有效；输入一旦变 FALSE 立即作废。            *)
ViscosityValid := VISCOSITY_OK AND (DebounceElapsed >= DebounceTime);

(* -------------------------------------------------------------------- *)
(* K1/K3：急停优先。仅当无急停且粘度条件有效时 VFD_RUN 才为 TRUE。        *)
(* -------------------------------------------------------------------- *)
VFD_RUN := PASTE_E_STOP_NC AND ViscosityValid;

(* -------------------------------------------------------------------- *)
(* K4：仅 VFD_RUN = TRUE 时按 CycleTime 累加；停机期间保持不变。          *)
(* 全程 LTIME 同类型运算，避免 TIME → LTIME 隐式赋值转换。                *)
(* -------------------------------------------------------------------- *)
IF VFD_RUN THEN
    PUMP_RUNTIME_ACC := PUMP_RUNTIME_ACC + CycleTimeLT;
END_IF;

(* -------------------------------------------------------------------- *)
(* K5：累计到 500h 置位维护提示，仅信息输出，不影响 VFD_RUN/安全允许。    *)
(* -------------------------------------------------------------------- *)
IF PUMP_RUNTIME_ACC >= LTIME#500h THEN
    PUMP_MAINT_DUE := TRUE;
END_IF;

END_FUNCTION_BLOCK

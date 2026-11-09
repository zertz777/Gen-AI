FUNCTION_BLOCK FB_P03
VAR_INPUT
    Value : REAL;
    hiLevel : REAL;
    loLevel : REAL;
    hystWindow : REAL;
END_VAR
VAR_OUTPUT
    hiAlarm : BOOL;
    loAlarm : BOOL;
    error : BOOL;
    status : WORD;
END_VAR
VAR
    (* 内部状态：上一周期的错误标志，用于满足 C1“错误后一周期内不得报警” *)
    prevError : BOOL := FALSE;
END_VAR
(*
    语义冲突报告（保留，不自行消除外部接口、不新增接口）：
    1) C10 要求上电后 G[0,1]（前两个扫描周期）内 !hiAlarm && !loAlarm
       && !error && status == 16#0000；而 K1/K2 要求首周期参数非法时立即
       置 error 并给出 16#8001/16#8002。二者在“首周期即参数非法”时不可
       同时成立。本实现按任务书条款 K1/K2 的“立即报错”优先：从首个扫描
       周期起即执行参数检查与报警判定；参数合法时自然满足初态要求。
    2) C1 要求 error 为真时本周期及其后一周期均不得输出报警；C7/C7b 要求
       报警仅在到达滞回阈值之外才复位。当报警保持期间出现参数错误时二者
       冲突。本实现按“错误优先于报警”处理：错误周期及其后一周期将
       hiAlarm/loAlarm 强制清零，滞回保持状态随之复位。
*)

(* 默认无错误 *)
error := FALSE;
status := 16#0000;

(* K1 / K2：参数合法性检查，错误优先；两者同时不满足时以 K1 为准 *)
IF loLevel >= hiLevel THEN
    error := TRUE;
    status := 16#8001;
ELSIF hystWindow >= (hiLevel - loLevel) THEN
    error := TRUE;
    status := 16#8002;
END_IF;

IF error OR prevError THEN
    (* C1：错误周期及其后一周期不得输出报警，且滞回保持状态复位 *)
    hiAlarm := FALSE;
    loAlarm := FALSE;
ELSE
    (* 参数合法（paramsValid = TRUE），执行带滞回的报警判定 *)

    (* K3：高报 —— Value > hiLevel 置位；Value < hiLevel-hystWindow 复位；其余保持 *)
    IF Value > hiLevel THEN
        hiAlarm := TRUE;
    ELSIF Value < (hiLevel - hystWindow) THEN
        hiAlarm := FALSE;
    END_IF;

    (* K4：低报 —— Value < loLevel 置位；Value > loLevel+hystWindow 复位；其余保持 *)
    IF Value < loLevel THEN
        loAlarm := TRUE;
    ELSIF Value > (loLevel + hystWindow) THEN
        loAlarm := FALSE;
    END_IF;
END_IF;

(* 保存本周期的错误状态，供下一周期 C1 使用 *)
prevError := error;

END_FUNCTION_BLOCK

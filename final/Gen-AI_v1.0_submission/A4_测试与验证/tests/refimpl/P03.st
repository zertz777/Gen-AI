(* P03 参考实现：带滞回的上下限报警（成员4 自写，仅作变异测试底本）

   规范来源：data/tasks/P03.yaml 的 K1—K4；逐拍期望见 tests/cases/P03.csv。
   本文件不是模型产物，也不得冒充成员2 的 final.st —— 用途见 docs/interp.md。
*)
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

    error := FALSE;
    status := 16#0000;

    (* K1：参数非法优先，置 16#8001 后立即退出，不执行报警逻辑 *)
    IF loLevel >= hiLevel THEN
        error := TRUE;
        status := 16#8001;
        RETURN;
    END_IF;

    (* K2：滞回窗口大于等于量程 *)
    IF hystWindow >= (hiLevel - loLevel) THEN
        error := TRUE;
        status := 16#8002;
        RETURN;
    END_IF;

    (* K3：高报滞回——超上限置位，跌破 hiLevel-hystWindow 才复位 *)
    IF Value > hiLevel THEN
        hiAlarm := TRUE;
    ELSIF Value < hiLevel - hystWindow THEN
        hiAlarm := FALSE;
    END_IF;

    (* K4：低报滞回——低于下限置位，升过 loLevel+hystWindow 才复位 *)
    IF Value < loLevel THEN
        loAlarm := TRUE;
    ELSIF Value > loLevel + hystWindow THEN
        loAlarm := FALSE;
    END_IF;

END_FUNCTION_BLOCK

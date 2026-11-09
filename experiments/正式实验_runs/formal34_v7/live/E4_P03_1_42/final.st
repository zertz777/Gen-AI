FUNCTION_BLOCK FB_P03
VAR_INPUT
    Value : REAL;
    hiLevel : REAL;
    loLevel : REAL;
    hystWindow : REAL;
END_VAR
VAR_OUTPUT
    hiAlarm : BOOL := FALSE;
    loAlarm : BOOL := FALSE;
    error : BOOL := FALSE;
    status : WORD := WORD#16#0000;
END_VAR

(*
需求原文：
In industrial automation systems, monitoring the status of equipment is crucial. When equipment parameters exceed the normal range, the system needs to issue an alarm. To avoid frequent triggering of alarms due to minor fluctuations in parameters, an alarm management system with hysteresis function needs to be implemented.
When Value is greater than hiLevel, trigger high alarm hiAlarm.
When Value is less than hiLevel-hystWindow, exit high alarm hiAlarm.
When Value is less than loLevel, trigger low alarm loAlarm.
When Value is greater than loLevel+hystWindow, exit low alarm loAlarm.
If loLevel is greater than or equal to hiLevel, output error error=true, status=16#8001, and exit the program
If the hysteresis window value hystWindow is greater than or equal to the deviation range between hiLevel and loLevel, output error error=true, status=16#8002

P03；每次调用为一个20 ms扫描。

规约冲突报告（待审，不能宣称同时满足全部条款）：
1. K3/K4允许两个报警同时保持，C4却要求互斥。
   例如loLevel=0、hiLevel=10、hystWindow=8：
   Value依次为11、3、-1时，最终两个报警均为TRUE。
   本实现保留独立滞回，不擅自增加互斥仲裁。
2. 参数错误时按C2的安全要求立即关闭两个报警，再退出本次调用。
   如果尚未越过相应复位阈值，这会与C7/C7b的无条件保持要求冲突。
3. C1要求错误后的下一周期仍关闭报警；K3/K4则可能要求在该周期
   参数恢复且Value越限时立即报警。本实现不增加未规定的恢复闭锁。
4. 输出声明满足给定初态；C10要求前两个周期无条件保持初态，
   与首周期即出现非法参数或越限时的K1—K4冲突。
   本实现不增加启动屏蔽周期。
5. 未禁止负hystWindow。其为负时，同一个报警的置位与复位条件
   可能同时成立；本实现按K3/K4书写顺序采用置位优先，冲突待审。

未经过真实编译器或逐周期测试验证。
*)

(* 参数错误处理优先于正常报警逻辑；8001优先于8002。 *)
IF loLevel >= hiLevel THEN
    error := TRUE;
    status := WORD#16#8001;
    hiAlarm := FALSE;
    loAlarm := FALSE;
    RETURN;
END_IF;

IF hystWindow >= (hiLevel - loLevel) THEN
    error := TRUE;
    status := WORD#16#8002;
    hiAlarm := FALSE;
    loAlarm := FALSE;
    RETURN;
END_IF;

error := FALSE;
status := WORD#16#0000;

(* 严格比较；未命中任何分支时保持上一次扫描状态。 *)
IF Value > hiLevel THEN
    hiAlarm := TRUE;
ELSIF Value < (hiLevel - hystWindow) THEN
    hiAlarm := FALSE;
END_IF;

IF Value < loLevel THEN
    loAlarm := TRUE;
ELSIF Value > (loLevel + hystWindow) THEN
    loAlarm := FALSE;
END_IF;

END_FUNCTION_BLOCK

(*
需要修改：替换占位 RETURN，实现参数检查、错误状态及上下限滞回报警。
接口名称、方向和类型保持不变，每次调用代表一个 20 ms 扫描周期。

需求原文：
In industrial automation systems, monitoring the status of equipment is crucial. When equipment parameters exceed the normal range, the system needs to issue an alarm. To avoid frequent triggering of alarms due to minor fluctuations in parameters, an alarm management system with hysteresis function needs to be implemented.
When Value is greater than hiLevel, trigger high alarm hiAlarm.
When Value is less than hiLevel-hystWindow, exit high alarm hiAlarm.
When Value is less than loLevel, trigger low alarm loAlarm.
When Value is greater than loLevel+hystWindow, exit low alarm loAlarm.
If loLevel is greater than or equal to hiLevel, output error error=true, status=16#8001, and exit the program
If the hysteresis window value hystWindow is greater than or equal to the deviation range between hiLevel and loLevel, output error error=true, status=16#8002

中文摘要：
带滞回的上下限报警。超过 hiLevel 置位高报，
低于 hiLevel-hystWindow 复位高报；
低于 loLevel 置位低报，高于 loLevel+hystWindow 复位低报。

接口：
IN  Value      : REAL，输入值。
IN  hiLevel    : REAL，高限。
IN  loLevel    : REAL，低限。
IN  hystWindow : REAL，滞回窗口。
OUT hiAlarm    : BOOL，高报。
OUT loAlarm    : BOOL，低报。
OUT error      : BOOL，执行错误标志。
OUT status     : WORD，状态码。

初态：
hiAlarm=FALSE；loAlarm=FALSE；error=FALSE；status=16#0000。

约束：
K1：loLevel >= hiLevel 时，error=TRUE、status=16#8001，
    立即退出本次调用，不执行后续正常报警逻辑。
K2：hystWindow >= hiLevel-loLevel 时，error=TRUE、
    status=16#8002，同样退出本次调用。
K3：Value > hiLevel 置位高报；
    Value < hiLevel-hystWindow 复位高报；否则保持。
K4：Value < loLevel 置位低报；
    Value > loLevel+hystWindow 复位低报；否则保持。

原始数据告警：
semantic_warnings=[]；warnings=[]；missing_fields=[]。
dialect_requirements=[]；type_origins={}。

完整形式化规约：
# task: P03
# meta: easy / D 故障与安全
# spec: version 1.0, updated 2026-10-30, scan cycle 20 ms
# 条款号对齐任务书 3.4 的条款库 C1—C10；[a,b] 单位为扫描周期。
#
# 命题映射（I/O 名 -> 派生命题）：
# alias: paramsValid := loLevel < hiLevel && hystWindow < (hiLevel - loLevel)

C1: G(error -> X(!hiAlarm && !loAlarm))    -- 参数错误时不得输出报警，且下一周期保持关断（错误优先于报警）（K1/K2）
C2: G(hiAlarm || loAlarm -> paramsValid)    -- 任何报警都要求参数合法（无合法参数不得报警）（K1/K2）
C4: G(!(hiAlarm && loAlarm))    -- 高报与低报互斥（同一时刻不可能既高又低）（K3/K4）
C7: G(hiAlarm -> (hiAlarm W Value < hiLevel - hystWindow))    -- 高报只在回落到 hiLevel - hystWindow 以下才允许复位（滞回）（K3）
C7b: G(loAlarm -> (loAlarm W Value > loLevel + hystWindow))    -- 低报只在回升到 loLevel + hystWindow 以上才允许复位（滞回）（K4）
C10: G[0,1](!hiAlarm && !loAlarm && !error && status == 16#0000)    -- 上电首周期无报警、无错误、状态码为 0（初态）

语义冲突报告及实现选择：
1. C10 的闭区间 [0,1] 要求两个时刻均无报警、无错误；
   若首个扫描输入越限或参数非法，这与 K1-K4 的即时处理冲突。
   本实现提供声明初态，但从第一次调用即执行 K1-K4，不屏蔽扫描。
2. C1 要求错误后的下一周期仍关闭报警；
   若下一周期参数恢复且输入越限，这与 K3/K4 即时置位冲突。
   本实现错误周期关闭报警，恢复合法后立即恢复正常判定，
   不额外引入一周期报警屏蔽。
3. C7/C7b 未给出错误关闭的例外；参数非法时强制关闭报警
   可能违反其无条件滞回保持要求。本实现选择错误处理优先，
   关闭两路报警以满足 C2 的安全要求。
4. 题面未禁止负 hystWindow。负窗口可能使同一路报警的
   置位条件与复位条件同时成立，无法同时满足两条要求。
   本实现不新增参数错误码，采用置位优先的 IF/ELSIF。
5. 正常、合法参数下严格比较；等于边界时，若另一条件
   未成立则保持报警状态。两个参数错误同时成立时 K1 优先。
6. 正常周期清除 error，status 恢复为 16#0000。
   RETURN 仅结束本次功能块调用，不停止外部控制任务。

验证说明：
当前对话没有可调用的编译器、执行工具或已配置测试命令，
因此未运行编译或逐周期测试，未声称编译通过或功能验证正确。
上述冲突保留，不声称本实现同时满足全部原始形式化条款。
*)

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

(* 参数错误优先；错误分支不进入正常报警逻辑。 *)
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

(* 高报：严格越限置位，严格越过复位阈值复位，否则保持。 *)
IF Value > hiLevel THEN
    hiAlarm := TRUE;
ELSIF Value < (hiLevel - hystWindow) THEN
    hiAlarm := FALSE;
END_IF;

(* 低报：严格越限置位，严格越过复位阈值复位，否则保持。 *)
IF Value < loLevel THEN
    loAlarm := TRUE;
ELSIF Value > (loLevel + hystWindow) THEN
    loAlarm := FALSE;
END_IF;

END_FUNCTION_BLOCK

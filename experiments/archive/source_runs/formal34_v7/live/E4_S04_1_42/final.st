FUNCTION_BLOCK FB_S04
VAR_INPUT
    RawWeight : INT;
    ZeroBtn : BOOL;
    CalibWeight : REAL;
END_VAR
VAR_OUTPUT
    CompensatedWeight : REAL := 0.0;
    ZeroOffset : INT := 0;
    DriftAlarm : BOOL := FALSE;
    Status : WORD := WORD#16#0000;
END_VAR
VAR
    ZeroBtnLast : BOOL := FALSE;
    ZeroRise : BOOL;
    RawWide : DINT;
    ZeroDelta : DINT;
    AbsDelta : DINT;
END_VAR

(*
    每次调用为一个20 ms扫描；状态不声明为RETAIN。
    CalibWeight仅作显示输入，不参与换算或标定。

    待审语义冲突（保留接口，按需求原文的逐周期语义实现）：
    1. 原文要求绝对偏差严格超过200才置警，形式化driftOut使用>=200。
    2. C2要求报警时始终满足driftOut，与C6及原文要求在
       150<绝对偏差<200时保持已有报警相冲突。
    3. C10要求启动扫描输出保持零值，与任意RawWeight下的C4、
       首次扫描的ZeroBtn上升沿标定及超限报警要求存在冲突。
       此处声明初态为零，首次调用即执行正常扫描逻辑。
    4. RawWeight为INT，其全部可表示值均在-32768..32767内；
       因此外部接口无法表达16#8402对应的超量程输入。
       不改变接口、不将合法端点视为故障。
    未声称通过编译或逐周期功能验证。
*)

ZeroRise := ZeroBtn AND NOT ZeroBtnLast;
ZeroBtnLast := ZeroBtn;

IF ZeroRise THEN
    ZeroOffset := RawWeight;
    DriftAlarm := FALSE;
END_IF;

(* 先扩宽再相减，避免INT差值溢出。 *)
RawWide := INT_TO_DINT(RawWeight);
ZeroDelta := RawWide - INT_TO_DINT(ZeroOffset);
CompensatedWeight := DINT_TO_REAL(ZeroDelta) * REAL#0.01;

IF ZeroDelta < DINT#0 THEN
    AbsDelta := -ZeroDelta;
ELSE
    AbsDelta := ZeroDelta;
END_IF;

IF AbsDelta > DINT#200 THEN
    DriftAlarm := TRUE;
ELSIF AbsDelta <= DINT#150 THEN
    DriftAlarm := FALSE;
END_IF;

(* 超量程状态优先；在当前INT接口下该条件不可达。 *)
IF (RawWide < DINT#-32768) OR (RawWide > DINT#32767) THEN
    Status := WORD#16#8402;
ELSIF DriftAlarm THEN
    Status := WORD#16#8401;
ELSE
    Status := WORD#16#0000;
END_IF;

END_FUNCTION_BLOCK

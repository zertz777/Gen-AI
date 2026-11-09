(*
修改说明：
保持 FB_S02 外部接口，替换占位 RETURN，添加初始化扫描保护、
双向互锁、200 ms 换向死区、检修闪灯及急停处理。

验证说明：
当前对话没有可用的编译器、测试执行工具或已配置测试命令，
因此未执行编译或逐周期测试，不声称已经验证正确。

语义冲突与边界约定：
1. 要求1的立即响应与检修、急停、死区和上电禁止输出冲突，
   本实现保留这些要求，但安全禁止条件优先。
2. C10 的 G[0,1] 按包含两个采样点解释，前两次调用禁止驱动。
3. C9 从最后一个正转输出采样点起禁止随后10个采样点反转，
   与从关断开始等待200 ms的要求共同实施，并对反向换向对称处理。
4. 两按钮同时有效时不选择方向，两个输出均关闭。
5. 急停优先于检修状态码；急停与检修同时有效时仍显示检修闪灯。
6. 急停清空死区计数，但保留最后运行方向。急停释放后若请求
   相反方向，重新执行完整200 ms死区，避免绕过C9。
7. 检修闪灯周期50次调用，前25次亮、后25次灭；退出检修复位。
   非检修时 RunLamp 表示任一电机方向正在输出。

【必留：需求原文】
输送线由一台可正反转的电机驱动，用于把工件送进和送出工位。

控制要求：
1. FwdBtn 有效且无反转输出时，MotorFwd = TRUE；RevBtn 有效且无正转输出时，MotorRev = TRUE。
2. 正转切换到反转（或反之）时，必须先关断当前方向，等待 200 ms 死区后才能启动另一方向。
3. MaintKey = TRUE（检修钥匙插入）时，MotorFwd 与 MotorRev 均不得为 TRUE；RunLamp 以 1 Hz 闪烁提示检修态。
4. EStop_NC = FALSE 时立即停止两个方向，并清空死区计时。
5. 任何时刻 MotorFwd 与 MotorRev 不得同时为 TRUE。
6. Status：16#0000 正常、16#8201 检修锁定、16#8202 急停、16#8203 换向死区中。

扫描周期：20 ms（全组统一，见 docs/tasks_note.md）

【必留：接口、初态、约束与数据告警】
{
  "task_id": "S02",
  "title": "输送线正反转与检修锁",
  "io_table": [
    {
      "direction": "IN",
      "name": "FwdBtn",
      "data_type": "BOOL",
      "description": "正转按钮"
    },
    {
      "direction": "IN",
      "name": "RevBtn",
      "data_type": "BOOL",
      "description": "反转按钮"
    },
    {
      "direction": "IN",
      "name": "MaintKey",
      "data_type": "BOOL",
      "description": "检修钥匙，TRUE = 检修态"
    },
    {
      "direction": "IN",
      "name": "EStop_NC",
      "data_type": "BOOL",
      "description": "急停常闭触点，TRUE = 正常"
    },
    {
      "direction": "OUT",
      "name": "MotorFwd",
      "data_type": "BOOL",
      "description": "电机正转"
    },
    {
      "direction": "OUT",
      "name": "MotorRev",
      "data_type": "BOOL",
      "description": "电机反转"
    },
    {
      "direction": "OUT",
      "name": "RunLamp",
      "data_type": "BOOL",
      "description": "运行指示灯（检修态闪烁）"
    },
    {
      "direction": "OUT",
      "name": "Status",
      "data_type": "WORD",
      "description": "状态码"
    }
  ],
  "initial_state": "MotorFwd = FALSE；MotorRev = FALSE；RunLamp = FALSE；Status = 16#0000；死区计时器 = 0。",
  "constraints": [
    "K1 MotorFwd 与 MotorRev 不得同时为 TRUE。",
    "K2 换向必须先两侧全 FALSE 并经过 200 ms 死区，才允许另一方向启动。",
    "K3 MaintKey = TRUE 时两个方向输出恒为 FALSE。",
    "K4 EStop_NC = FALSE 时立即停机并清死区计时。"
  ],
  "semantic_warnings": [],
  "warnings": [],
  "missing_fields": [],
  "dialect_requirements": [],
  "type_origins": {}
}

【必留：完整形式化规约；有界时序以扫描周期计】
# task: S02
# meta: easy / A 开关量联锁
# spec: version 1.0, updated 2026-10-30, scan cycle 20 ms
# 条款号对齐任务书 3.4 的条款库 C1—C10；[a,b] 单位为扫描周期。

C1: G(!EStop_NC -> (!MotorFwd && !MotorRev))    -- 急停当周期两个方向都必须断开（K4）
C2: G(MotorFwd -> !MaintKey)    -- 检修钥匙插入时禁止正转（K3）
C2b: G(MotorRev -> !MaintKey)    -- 检修钥匙插入时禁止反转（K3）
C4: G(!(MotorFwd && MotorRev))    -- 正反转互斥（K1）
C9: G(MotorFwd && !MotorRev -> G[0,10](!MotorRev))    -- 正转期间 200 ms 内不得出现反转（换向死区）（K2）
C10: G[0,1](!MotorFwd && !MotorRev)    -- 上电首周期两个方向都不输出（初态）
*)

FUNCTION_BLOCK FB_S02
VAR_INPUT
    FwdBtn : BOOL;
    RevBtn : BOOL;
    MaintKey : BOOL;
    EStop_NC : BOOL;
END_VAR
VAR_OUTPUT
    MotorFwd : BOOL := FALSE;
    MotorRev : BOOL := FALSE;
    RunLamp : BOOL := FALSE;
    Status : WORD := WORD#16#0000;
END_VAR
VAR
    StartupScans : INT := 0;
    StartupInhibit : BOOL := TRUE;
    RequestedDirection : INT := 0;
    PreviousDirection : INT := 0;
    LastDirection : INT := 0;
    DeadScans : INT := 0;
    RearmAfterEStop : BOOL := FALSE;
    BlinkScans : INT := 0;
END_VAR

(* 保存上次调用的实际输出方向，再统一关闭输出。 *)
PreviousDirection := 0;
IF MotorFwd THEN
    PreviousDirection := 1;
ELSIF MotorRev THEN
    PreviousDirection := 2;
END_IF;

MotorFwd := FALSE;
MotorRev := FALSE;
Status := WORD#16#0000;

StartupInhibit := StartupScans < 2;
IF StartupScans < 2 THEN
    StartupScans := StartupScans + 1;
END_IF;

RequestedDirection := 0;
IF FwdBtn AND NOT RevBtn THEN
    RequestedDirection := 1;
ELSIF RevBtn AND NOT FwdBtn THEN
    RequestedDirection := 2;
END_IF;

IF NOT EStop_NC THEN
    (* 急停当周期立即关闭，死区计数严格清零。 *)
    DeadScans := 0;
    RearmAfterEStop := LastDirection <> 0;
    Status := WORD#16#8202;
ELSE
    (* 关断调用不扣减；其后每次调用代表经过20 ms。 *)
    IF DeadScans > 0 THEN
        DeadScans := DeadScans - 1;
    END_IF;

    IF PreviousDirection <> 0 THEN
        IF MaintKey OR StartupInhibit
           OR (RequestedDirection <> PreviousDirection) THEN
            (* 关断瞬间启动死区；10次后续调用才满200 ms。 *)
            DeadScans := 10;
            RearmAfterEStop := FALSE;
        END_IF;
    END_IF;

    IF NOT MaintKey AND NOT StartupInhibit THEN
        IF RequestedDirection <> 0 THEN
            IF RearmAfterEStop
               AND (LastDirection <> 0)
               AND (RequestedDirection <> LastDirection) THEN
                (* 急停不允许通过清计时绕过换向保护。 *)
                DeadScans := 10;
                RearmAfterEStop := FALSE;
            END_IF;

            IF DeadScans = 0 THEN
                IF RequestedDirection = 1 THEN
                    MotorFwd := TRUE;
                ELSIF RequestedDirection = 2 THEN
                    MotorRev := TRUE;
                END_IF;
                LastDirection := RequestedDirection;
                RearmAfterEStop := FALSE;
            END_IF;
        END_IF;
    END_IF;

    IF MaintKey THEN
        Status := WORD#16#8201;
    ELSIF DeadScans > 0 THEN
        Status := WORD#16#8203;
    END_IF;
END_IF;

IF MaintKey THEN
    (* 每25次调用切换一次明暗，完整周期为1000 ms。 *)
    RunLamp := BlinkScans < 25;
    BlinkScans := BlinkScans + 1;
    IF BlinkScans >= 50 THEN
        BlinkScans := 0;
    END_IF;
ELSE
    BlinkScans := 0;
    RunLamp := MotorFwd OR MotorRev;
END_IF;

END_FUNCTION_BLOCK

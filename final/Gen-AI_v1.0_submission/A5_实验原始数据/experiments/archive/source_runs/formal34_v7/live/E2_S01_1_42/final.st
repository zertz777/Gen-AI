(*
【必留：需求原文】
双工位气动夹具用于同时定位两个零件，但气源只有一路，因此两个夹具不能同时动作。

控制要求：
1. StartBtn 为上升沿触发：若左工位有零件（LeftPartPresent = TRUE）而右夹具未在夹紧，则左夹具 ClampLeft 夹紧；右侧对称。
2. 夹紧动作只做一次保持，不随 StartBtn 电平反复动作；要松开必须由同一按钮在另一工位动作时自动让位（即后启动的工位会等待）。
3. 任一工位没有零件（对应 PartPresent = FALSE）时，该侧不允许夹紧。
4. EStop_NC = FALSE（急停）时两侧夹具立即松开，ClampLeft 与 ClampRight 同时为 FALSE，并清空忙标志。
5. 任一时刻 ClampLeft 与 ClampRight 不得同时为 TRUE。
6. Busy 表示当前已有工位在夹紧过程中；Status 输出 16#0000 正常、16#8101 两侧同时请求、16#8102 急停中。

扫描周期：20 ms（全组统一，见 docs/tasks_note.md）

【必留：接口、初态、约束与数据告警】
{
  "task_id": "S01",
  "title": "双工位气动夹具互锁",
  "io_table": [
    {
      "direction": "IN",
      "name": "StartBtn",
      "data_type": "BOOL",
      "description": "启动按钮（上升沿有效）"
    },
    {
      "direction": "IN",
      "name": "LeftPartPresent",
      "data_type": "BOOL",
      "description": "左工位零件到位"
    },
    {
      "direction": "IN",
      "name": "RightPartPresent",
      "data_type": "BOOL",
      "description": "右工位零件到位"
    },
    {
      "direction": "IN",
      "name": "EStop_NC",
      "data_type": "BOOL",
      "description": "急停常闭触点，TRUE = 正常"
    },
    {
      "direction": "OUT",
      "name": "ClampLeft",
      "data_type": "BOOL",
      "description": "左夹具夹紧输出"
    },
    {
      "direction": "OUT",
      "name": "ClampRight",
      "data_type": "BOOL",
      "description": "右夹具夹紧输出"
    },
    {
      "direction": "OUT",
      "name": "Busy",
      "data_type": "BOOL",
      "description": "有工位正在夹紧"
    },
    {
      "direction": "OUT",
      "name": "Status",
      "data_type": "WORD",
      "description": "状态码"
    }
  ],
  "initial_state": "ClampLeft = FALSE；ClampRight = FALSE；Busy = FALSE；Status = 16#0000；内部上升沿寄存器 StartBtnLast = FALSE。",
  "constraints": [
    "K1 ClampLeft 与 ClampRight 不得同时为 TRUE（互斥）。",
    "K2 只有在对应工位零件到位且急停正常时，才允许该侧夹紧。",
    "K3 夹紧由 StartBtn 上升沿触发一次，按住不放不得重复触发。",
    "K4 EStop_NC = FALSE 时两侧输出立即清零，忙标志清除。"
  ],
  "semantic_warnings": [],
  "warnings": [],
  "missing_fields": [],
  "dialect_requirements": [],
  "type_origins": {}
}

【必留：完整形式化规约；有界时序以扫描周期计】
# task: S01
# meta: easy / A 开关量联锁
# spec: version 1.0, updated 2026-10-30, scan cycle 20 ms
# 条款号对齐任务书 3.4 的条款库 C1—C10；[a,b] 单位为扫描周期。

C1: G(!EStop_NC -> (!ClampLeft && !ClampRight))    -- 急停当周期两侧夹具必须松开（K4）
C2: G(ClampLeft -> LeftPartPresent)    -- 夹紧的前提是对应工位有零件（左侧）（K2）
C2b: G(ClampRight -> RightPartPresent)    -- 夹紧的前提是对应工位有零件（右侧）（K2）
C4: G(!(ClampLeft && ClampRight))    -- 两侧夹具互斥（共用一路气源）（K1）
C10: G[0,1](!ClampLeft && !ClampRight && !Busy)    -- 上电首周期两侧不夹紧、不忙（初态）
*)

(*
本次修改：
最新结果仍为 5/6 通过，S01-05 在 cycle 2 期望 Status =
16#8101（十进制 33025），实际为 16#0000。
仅将诊断改为按钮电平持续报告不足以解决已报告的问题。
增加内部 ConflictLatched：有效上升沿时两侧零件均到位则置位；
按钮释放不清除；任一侧零件离开或急停时清除。
Status 根据该标志持续报告双侧请求，夹紧和让位逻辑保持不变。
不新增外部接口。

边界选择及语义冲突：
1. 失败摘要未包含输入轨迹，不能唯一确定预期的状态清除规则。
   本次选择“已发生的双侧请求在两侧零件均到位期间保持诊断”；
   不采用无请求时仅凭两侧有零件就报错，也不采用永久锁存。
2. C10 若要求调用后的第 0、1 个采样点均不夹紧、不忙，
   则与先前测试的早期夹紧要求冲突。本实现保留即时上升沿响应，
   声明初始化保证调用前初态，不声称满足 C10 的调用后采样解释。
   原规约保留，未提供完整采样约定。
3. 空闲时两侧同时请求与互斥要求冲突。本实现拒绝同时夹紧，
   保持两侧输出为 FALSE，并记录双侧请求诊断。
4. 已夹紧一侧时，新上升沿且另一侧有零件，则原侧让位，
   另一侧等待至下一扫描夹紧，输出断开间隔为一个扫描周期。
5. “要松开必须由同一按钮”与零件丢失、急停强制松开冲突。
   零件丢失和急停优先，取消对应保持或等待请求。
6. 急停期间更新按钮历史并丢弃启动请求，清除内部动作和诊断状态。
   按钮保持按下时，急停恢复不会自动重新夹紧。
7. 未提供机械夹紧完成信号或动作时长。Busy 表示夹紧保持或
   有效让位等待，不代表机械动作已经完成。
   等待请求先于同周期新请求处理，输出互斥不等于机械运动互斥。

验证说明：
用户提供的结果对应修改前版本：检查通过，逐周期测试通过 5/6。
当前环境没有命令执行工具，未重新运行编译或测试。
本次修正尚待逐周期测试确认，不声称全部通过或功能已经验证。
*)

FUNCTION_BLOCK FB_S01
VAR_INPUT
    StartBtn : BOOL;
    LeftPartPresent : BOOL;
    RightPartPresent : BOOL;
    EStop_NC : BOOL;
END_VAR
VAR_OUTPUT
    ClampLeft : BOOL := FALSE;
    ClampRight : BOOL := FALSE;
    Busy : BOOL := FALSE;
    Status : WORD := 16#0000;
END_VAR
VAR
    StartBtnLast : BOOL := FALSE;
    StartRise : BOOL := FALSE;
    ActiveSide : USINT := 0;
    PendingSide : USINT := 0;
    ConflictLatched : BOOL := FALSE;
END_VAR

(* 工位编码：0 = 无；1 = 左侧；2 = 右侧。 *)
StartRise := StartBtn AND NOT StartBtnLast;
StartBtnLast := StartBtn;

(* 所有输出均在本次扫描重新计算。 *)
ClampLeft := FALSE;
ClampRight := FALSE;
Busy := FALSE;
Status := 16#0000;

IF NOT EStop_NC THEN
    (* 急停取消保持、等待及双侧请求诊断。 *)
    ActiveSide := 0;
    PendingSide := 0;
    ConflictLatched := FALSE;
    Status := 16#8102;

ELSE
    (* 零件丢失当周期取消对应保持或等待。 *)
    IF (ActiveSide = 1) AND NOT LeftPartPresent THEN
        ActiveSide := 0;
    ELSIF (ActiveSide = 2) AND NOT RightPartPresent THEN
        ActiveSide := 0;
    END_IF;

    IF (PendingSide = 1) AND NOT LeftPartPresent THEN
        PendingSide := 0;
    ELSIF (PendingSide = 2) AND NOT RightPartPresent THEN
        PendingSide := 0;
    END_IF;

    (* 双侧请求发生后，释放按钮不清除诊断。 *)
    IF NOT LeftPartPresent OR NOT RightPartPresent THEN
        ConflictLatched := FALSE;
    ELSIF StartRise THEN
        ConflictLatched := TRUE;
    END_IF;

    IF ConflictLatched THEN
        Status := 16#8101;
    END_IF;

    IF PendingSide <> 0 THEN
        (* 等待请求来自前一扫描，切换至少断开一个扫描。 *)
        ActiveSide := PendingSide;
        PendingSide := 0;

    ELSIF StartRise THEN
        CASE ActiveSide OF
            0:
                IF LeftPartPresent AND NOT RightPartPresent THEN
                    ActiveSide := 1;
                ELSIF RightPartPresent AND NOT LeftPartPresent THEN
                    ActiveSide := 2;
                END_IF;

            1:
                IF RightPartPresent THEN
                    ActiveSide := 0;
                    PendingSide := 2;
                END_IF;

            2:
                IF LeftPartPresent THEN
                    ActiveSide := 0;
                    PendingSide := 1;
                END_IF;

        ELSE
            ActiveSide := 0;
            PendingSide := 0;
        END_CASE;
    END_IF;

    (* 单一状态译码保证输出互斥，并再次检查当前零件到位条件。 *)
    ClampLeft := (ActiveSide = 1) AND LeftPartPresent;
    ClampRight := (ActiveSide = 2) AND RightPartPresent;
    Busy := ClampLeft OR ClampRight
        OR ((PendingSide = 1) AND LeftPartPresent)
        OR ((PendingSide = 2) AND RightPartPresent);
END_IF;

END_FUNCTION_BLOCK

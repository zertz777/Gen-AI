(*
【必留：需求原文】
分拣线按产品高度分到左右两条支线，阈值来自配方。切换配方必须在线上无料时进行。

控制要求：
1. RecipeSelect 为 1—3 时对应三组配方：1 = 左 30 mm / 右 60 mm；2 = 左 50 mm / 右 90 mm；3 = 左 70 mm / 右 120 mm（阈值为分界高度）。
2. ChangeoverReq 上升沿时，若 Busy = FALSE 且当前无料（PartHeight = 0.0），则 ActiveRecipe 切换为 RecipeSelect，Busy 置 TRUE 并保持 2 s 后自动清除。
3. Busy = TRUE 期间 SortLeft 与 SortRight 必须都为 FALSE。
4. RecipeSelect 不在 1—3 时拒绝切换，ActiveRecipe 保持不变，Status = 16#8801。
5. 正常分拣：PartHeight 小于左阈值时 SortLeft = TRUE；大于等于左阈值且小于右阈值时 SortRight = TRUE；超过右阈值时不动作并置 Status = 16#8802（超规格）。
6. 上电时 ActiveRecipe = 1，Busy = FALSE。

扫描周期：20 ms（全组统一，见 docs/tasks_note.md）

【必留：接口、初态、约束与数据告警】
{
  "task_id": "S08",
  "title": "分拣线配方切换",
  "io_table": [
    {
      "direction": "IN",
      "name": "RecipeSelect",
      "data_type": "INT",
      "description": "请求的配方号 1—3"
    },
    {
      "direction": "IN",
      "name": "ChangeoverReq",
      "data_type": "BOOL",
      "description": "切换请求（上升沿有效）"
    },
    {
      "direction": "IN",
      "name": "PartHeight",
      "data_type": "REAL",
      "description": "当前产品高度（mm），0 表示无料"
    },
    {
      "direction": "IN",
      "name": "EStop_NC",
      "data_type": "BOOL",
      "description": "急停常闭触点，TRUE = 正常"
    },
    {
      "direction": "OUT",
      "name": "ActiveRecipe",
      "data_type": "INT",
      "description": "当前生效配方号"
    },
    {
      "direction": "OUT",
      "name": "SortLeft",
      "data_type": "BOOL",
      "description": "分到左支线"
    },
    {
      "direction": "OUT",
      "name": "SortRight",
      "data_type": "BOOL",
      "description": "分到右支线"
    },
    {
      "direction": "OUT",
      "name": "Busy",
      "data_type": "BOOL",
      "description": "切换进行中"
    },
    {
      "direction": "OUT",
      "name": "Status",
      "data_type": "WORD",
      "description": "状态码"
    }
  ],
  "initial_state": "ActiveRecipe = 1；SortLeft = FALSE；SortRight = FALSE；Busy = FALSE；Status = 16#0000；ChangeoverReqLast = FALSE。",
  "constraints": [
    "K1 Busy = TRUE 期间 SortLeft 与 SortRight 均为 FALSE。",
    "K2 只有在无料且非忙时才允许切换配方。",
    "K3 RecipeSelect 非法（不在 1—3）时 ActiveRecipe 不变，仅置错误码。",
    "K4 分拣两路互斥，且同一产品只能分到一条支线。"
  ],
  "semantic_warnings": [],
  "warnings": [],
  "missing_fields": [],
  "dialect_requirements": [],
  "type_origins": {}
}

【必留：完整形式化规约；有界时序以扫描周期计】
# task: S08
# meta: hard / C 状态机与节拍
# spec: version 1.0, updated 2026-10-30, scan cycle 20 ms
# 条款号对齐任务书 3.4 的条款库 C1—C10；[a,b] 单位为扫描周期。

C1: G(Busy -> (!SortLeft && !SortRight))    -- 切换配方期间禁止分拣（切换优先于分拣）（K1）
C2: G(SortLeft -> PartHeight > 0.0)    -- 分拣的前提是线上有料（K4）
C4: G(!(SortLeft && SortRight))    -- 左右分拣互斥（K4）
C9: G(Busy -> G[0,100](Busy))    -- 切换状态至少保持 2 s（防止请求抖动造成反复切换）（K2）
C10: G[0,1](!SortLeft && !SortRight && !Busy && ActiveRecipe == 1)    -- 上电首周期默认配方 1、不分拣（初态）

实现说明与冲突报告：
1. 初态由变量声明的初值提供，第一次调用即处理当前输入。
   ChangeoverReqLast 初值为 FALSE，因此第一次调用中
   ChangeoverReq=TRUE 会形成上升沿。不屏蔽初始化后的执行扫描。
2. C9 按字面要求每个 Busy 周期的后续 100 周期均为 Busy。
   因而 Busy 一旦成立便不能再清除，与需求 2 的 2 s 后自动清除冲突。
   本实现采用有限 2 s 切换，不声称满足原始 C9。
   若在扫描 n 接受请求，则 n 至 n+99 输出 Busy=TRUE，
   在 n+100 清除并提交目标，两个扫描时刻相差 2000 ms。
   因此在 cycle=1 接受请求时，在 cycle=101 完成切换。
3. C10 的闭区间 [0,1] 覆盖两个扫描，与“上电首周期”的注释不一致。
   提供的逐周期测试要求首个执行扫描即可分拣或开始切换，
   与首个执行扫描强制禁止分拣和切换的 C10 字面要求冲突。
   本实现按测试反馈将初态解释为第一次调用前的状态，
   保留原始 C10，不声称同时满足该公式。
4. 先前测试要求接受切换时 ActiveRecipe 仍保持旧配方。
   本实现采用内部 PendingRecipe 锁存已接受的目标，
   Busy 期间保持旧 ActiveRecipe，2 s 结束后提交。
   这与需求 2 中接受请求时立即更新 ActiveRecipe 的原文冲突，
   原文保留，不声称同时满足两种时序。
5. 最新测试 S08-02 在 cycle=101 期望 ActiveRecipe=2，
   实际为 1。旧实现会在完成时重新检查无料、急停及配方合法性，
   任一条件不满足便取消已接受的目标。
   本次删除完成时的输入复查及取消逻辑，计时结束后
   无条件提交请求接受时锁存的合法 PendingRecipe。
   后续 RecipeSelect、PartHeight、EStop_NC 的变化不取消该事务。
   无料、非忙及合法配方检查仅用于接受新请求。
   如果 K2 要求 ActiveRecipe 实际更新的扫描也必须无料，
   本实现与该解释冲突；如果 K3 要求当前 RecipeSelect 非法时
   连先前已接受的切换也不得完成，本实现同样与该解释冲突。
   保留原始约束，不声称同时满足上述严格解释。
   测试摘要未提供 cycle=101 的完整输入，仍需复测确认。
6. 恰好等于右阈值时，原文没有给出动作或错误码；
   本实现两路均不动作且不置超规格码，严格保留“超过”的比较。
   PartHeight<=0.0 时不分拣，负高度没有另行新增错误码。
7. EStop_NC 的动作策略没有明文规定。
   本实现 FALSE 时禁止分拣及接受新切换；
   已开始的 Busy 继续计时，完成时仍提交已接受的目标。
   ActiveRecipe 不因急停复位，恢复时不合成新的请求沿。
8. 非法 RecipeSelect 的 16#8801 每扫描生效，
   优先于超规格码，禁止接受非法的新切换请求；
   已接受的合法目标仍可在完成扫描提交。
   分拣使用当前有效配方。Status 不锁存。
9. 先前 S08-01 要求连续有料期间高度跨越分界后输出新方向。
   本实现不使用 PartRoute，按当前高度逐扫描互斥分拣。
   没有产品标识或独立到料信号，无法识别跨扫描的同一产品；
   因此只能保证每扫描左右互斥，不能证明同一物理产品
   在高度变化的多个扫描中永远不会收到不同方向信号。
   若 K4 要求跨扫描锁定，则与该测试反馈及逐扫描分拣存在冲突。
10. 用户提供的上个版本编译检查通过，逐周期测试为 4/5，
    通过项为 S08-01、S08-03、S08-04、S08-05。
    当前对话没有测试执行工具，未重新编译或运行此修改版本；
    上个版本编译通过不能证明本版本编译通过或功能正确。
*)

FUNCTION_BLOCK FB_S08
VAR_INPUT
    RecipeSelect : INT;
    ChangeoverReq : BOOL;
    PartHeight : REAL;
    EStop_NC : BOOL;
END_VAR
VAR_OUTPUT
    ActiveRecipe : INT := 1;
    SortLeft : BOOL := FALSE;
    SortRight : BOOL := FALSE;
    Busy : BOOL := FALSE;
    Status : WORD := 16#0000;
END_VAR
VAR
    ChangeoverReqLast : BOOL := FALSE;
    ChangeoverRise : BOOL := FALSE;
    BusyScansRemaining : INT := 0;
    PendingRecipe : INT := 1;
    RecipeValid : BOOL := FALSE;
    LeftThreshold : REAL := 30.0;
    RightThreshold : REAL := 60.0;
END_VAR

(* 每扫描先关闭输出，只有允许分拣的路径才能重新开启。 *)
SortLeft := FALSE;
SortRight := FALSE;
Status := 16#0000;

ChangeoverRise := ChangeoverReq AND NOT ChangeoverReqLast;
ChangeoverReqLast := ChangeoverReq;
RecipeValid := (RecipeSelect >= 1) AND (RecipeSelect <= 3);

IF NOT RecipeValid THEN
    Status := 16#8801;
END_IF;

(* 已忙时只处理计时，不接受或缓存新的请求沿。 *)
IF Busy THEN
    IF BusyScansRemaining > 0 THEN
        BusyScansRemaining := BusyScansRemaining - 1;
    END_IF;

    IF BusyScansRemaining = 0 THEN
        (* 提交已接受的合法目标，不重新检查或采样当前请求输入。 *)
        ActiveRecipe := PendingRecipe;
        Busy := FALSE;
    END_IF;
ELSIF ChangeoverRise
    AND RecipeValid
    AND EStop_NC
    AND (PartHeight = 0.0) THEN
    PendingRecipe := RecipeSelect;
    Busy := TRUE;
    BusyScansRemaining := 100;
END_IF;

CASE ActiveRecipe OF
    1:
        LeftThreshold := 30.0;
        RightThreshold := 60.0;
    2:
        LeftThreshold := 50.0;
        RightThreshold := 90.0;
    3:
        LeftThreshold := 70.0;
        RightThreshold := 120.0;
END_CASE;

(* 每扫描根据当前高度分拣，不推断跨扫描的产品身份。 *)
IF EStop_NC AND NOT Busy AND (PartHeight > 0.0) THEN
    IF PartHeight < LeftThreshold THEN
        SortLeft := TRUE;
    ELSIF PartHeight < RightThreshold THEN
        SortRight := TRUE;
    ELSIF PartHeight > RightThreshold THEN
        IF RecipeValid THEN
            Status := 16#8802;
        END_IF;
    END_IF;
END_IF;
END_FUNCTION_BLOCK

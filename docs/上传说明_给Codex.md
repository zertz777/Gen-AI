# 上传说明（给 Codex / 执行上传的人）

目标仓库：`https://github.com/zertz777/Gen-AI`，分支 **main**。
上传者：组员1 的材料（题集与形式化规约，对应任务书 A3 / D1.1—D1.8）。

---

## 1　现在仓库里有什么（2026-11-05 核对）

```
Gen-AI/
├── .gitignore
├── README.md                     ← 组员5 写的骨架（三条命令、目录状态、FAQ）
├── docs/                         ← 组员5 的文档目录
├── examples/actual_package/E3_P03_r1_s42/   ← 一次真实运行快照
└── tests/                        ← 组员4：34 份用例、coverage.csv、runner/（含 ST 解释器）、ambiguities.md
```

**没有** `data/`、`tools/`、`refs/`——这三样正是本包要新增的。
`tests/` 里已经出现我方的条款号（`spec_refs` 里的 `C1`/`C2b`/`C7b` 等）与 K 编号，
所以**条款号是既有契约，不能改号**（内容已在 v1.7 修订，编号全部保留）。

---

## 2　放哪儿（包内路径 → 仓库路径）

| 包内路径 | 仓库路径 | 动作 |
| --- | --- | --- |
| `data/tasks/`（34 份 `.yaml`） | `data/tasks/` | 新增 |
| `data/specs/`（34 份 `.ltl` + `PROPOSITIONS.md`） | `data/specs/` | 新增 |
| `data/provenance.csv` | `data/provenance.csv` | 新增 |
| `data/diversity.md` | `data/diversity.md` | 新增 |
| `data/review.md` | `data/review.md` | 新增 |
| `data/CHANGELOG.md` | `data/CHANGELOG.md` | 新增 |
| `data/sha256sums.txt` | `data/sha256sums.txt` | 新增 |
| `tools/`（9 个 `.py`） | `tools/` | 新增 |
| `refs/tiku_json/大作业题库json/大作业题库.json` | 同左 | 新增（推荐；让 `import_bank.py --check` 可重放） |
| `docs/tasks_note.md` | `docs/tasks_note.md` | 新增 |
| `docs/report/ch2.md` | `docs/report/ch2.md` | 新增 |
| `docs/qa/member1.md` | `docs/qa/member1.md` | 新增 |
| `docs/判据修订说明.md` | `docs/判据修订说明.md` | 新增（成员4 阻塞清单的答复） |
| `docs/上传说明_给Codex.md` | `docs/上传说明_给Codex.md` | 新增（本文件） |
| `README.md`（包内） | — | **不要覆盖**仓库根 README；只在需要时把第 0、1 节的内容摘进仓库 README 的“数据集”小节 |

原则：**只增不改**。本包不修改 `tests/`、`examples/`、`.gitignore`、根 `README.md`。

---

## 3　我做了什么（一句话版 + 明细）

按成员4 在 `tests/ambiguities.md`「需要成员1 回答的阻塞项」里点名的 6 处判据错误修订了数据，
并给了 3 条口径确认。**只改派生字段（约束措辞、LTL 条款、说明），不改英文需求原文、
不改 I/O 变量名**，所以 `experiments/runs/formal34_v7` 的 136 条实验记录无需重跑。

| 编号 | 题号 | 原来是错的 | 现在是 |
| --- | --- | --- | --- |
| R7 / A-47 | P19 | K4 与 C1/C2 按 `TRUE = 急停` 写，与 I/O 表 `FALSE = 急停触发` 相反 | K4 措辞改正；`P19.ltl` C1 触发 `!EmergencyStop`、C2 许可 `EmergencyStop` |
| R8 / A-42 | S11 | C2/C4 禁止「降级且信号有效」，与需求3「恢复后再保持 3 s」矛盾 → 两条恒假 | 重写为 4 条（降级期输出备用值 / 恢复后保持 ≥150 周期 / 报警灯常亮 / 初态）；新增 K5 |
| R9 / A-35 | P17 | K3 把查/删/改不存在都写成 16#8001 | 查询 16#8001、删除 16#8004、修改 16#8005 |
| R10 / A-27 | P13 | C2 `HVAC_MODE_SELECTOR != 4` | `!= 3`（0 自动 / 1 舒适 / 2 节能 / 3 夜间） |
| R11 / A-23 | P01 | C2「泵运行时必须有瓶子」，与需求「continues to work」相反 | `G(cleaningConfirmButton -> X(!Pump_Motor))` |
| R13 | P08 | C2b 自加「32 路上限」；K5「停止处理后续通道」 | C2b `G(count == 0 -> !chEn)`；K5 改为逐通道报错、其余通道继续处理 |
| R12 / A-11 | P09 | `windowSizeReached` 无定义 | K4 补定义（窗口累计满 windowSize 个样本为 TRUE；未满时按已累计样本数求平均） |
| R14 | P14 | K4「测试需靠返回状态区分」（接口没有状态输出） | 改为「本接口没有状态输出，合法 0.0.0.0 与非法输入的输出值相同，用例不据此判错」 |
| — / A-40 | S11 | 过渡期输出未规定 | K5：`ControlValue = 0.0`，报警灯 1 Hz 先亮 500 ms |
| — / A-15 | P19 | `Start` 上升沿还是电平 | 上升沿（K2 措辞已有） |
| — / A-22 | P18 | `item`/`buffer` 是否判输出 | 不判；只在 notes 记 CODESYS 3.5.x 用 INT 等价实例化 |

数字变化：**条款 178→177、约束 143→144、I/O 316 不变、题数 34 不变**；
改动 6 份题面（P08、P09、P14、P17、P19、S11）与 5 份规约（P01、P08、P13、P19、S11），
`sha256sums.txt` 与 `provenance.csv` 已重算。

---

## 4　上传步骤（PowerShell，逐条执行）

```powershell
# 0) 工作目录
$work = "$env:USERPROFILE\Desktop\genai-upload"
New-Item -ItemType Directory -Force -Path $work | Out-Null
cd $work

# 1) 克隆（用你自己的账号登录过 Git 凭据管理器即可直接推送）
git clone https://github.com/zertz777/Gen-AI.git
cd Gen-AI

# 2) 先确认分支与干净状态
git branch --show-current        # 应为 main
git status --short                # 应为空

# 3) 把包内内容搬到仓库（把 <包路径> 换成解压后的 组员1_提交包 目录）
$pkg = "<包路径>\组员1_提交包"
Copy-Item -Recurse -Force "$pkg\data"  .\data
Copy-Item -Recurse -Force "$pkg\tools" .\tools
Copy-Item -Recurse -Force "$pkg\refs"  .\refs
New-Item -ItemType Directory -Force -Path .\docs\report, .\docs\qa | Out-Null
Copy-Item -Force "$pkg\docs\tasks_note.md"        .\docs\tasks_note.md
Copy-Item -Force "$pkg\docs\report\ch2.md"        .\docs\report\ch2.md
Copy-Item -Force "$pkg\docs\qa\member1.md"        .\docs\qa\member1.md
Copy-Item -Force "$pkg\docs\判据修订说明.md"        .\docs\判据修订说明.md
Copy-Item -Force "$pkg\docs\上传说明_给Codex.md"    .\docs\上传说明_给Codex.md

# 4) 确认要提交的东西（重点：data/ 不能被 .gitignore 吃掉）
git check-ignore -v data\tasks\P01.yaml     # 无输出 = 没被忽略；有输出则先修 .gitignore
git status --short

# 5) 提交与推送
git add data tools refs docs
git commit -m "feat(data): 题集与LTL规约 v1.7（34题/177条款）+ 入库与校验脚本

- data/tasks: 34 份 12 字段题面（P01-P20 公开题 + S01-S14 自编题）
- data/specs: 34 份 LTL 规约（177 条条款，C1-C10 条款库）+ PROPOSITIONS.md
- data/provenance.csv / diversity.md / review.md / CHANGELOG.md / sha256sums.txt
- tools: 9 个零依赖脚本（导入、生成、LTL 校验、schema 校验、元数据与文档生成）
- docs: 题集说明、报告第2章初稿、问答要点、判据修订说明（回应 member4 阻塞清单 A-11…A-47）
- 按 member4 ambiguities 修订 P19 急停极性、S11 恒假条款、P17 三码、P13 模式取值、
  P01 停泵条件、P08 逐通道、P09 windowSizeReached 定义、P14 判定口径"
git push origin main
```

**注意**

- 不要 `git push --force`；如果远端已有新提交，先 `git pull --rebase` 再推。
- 文件名含中文（`大作业题库.json`、`判据修订说明.md`）是正常的，Git 默认能处理；
  若提示路径乱码，先 `git config core.quotepath false` 再 `git status` 看。
- 不要提交 `gen_check.txt`、`backup_pre_v1_7/`、`out/`、`peers/` 这些本地临时物。

---

## 5　上传后自检（三条，在本机仓库根目录跑）

```powershell
python tools\ltl_check.py --quiet     # 期望：规约文件 34 份，条款合计 177 条 …… 全部通过
python tools\schema_check.py          # 期望：schema_check 通过（另附 38 条“约束由用例覆盖”警告）
python tools\import_bank.py --check   # 期望：校验通过，不写盘
```

三条都过，说明仓库里的数据是自洽的、可被别人复现的。

---

## 6　上传后要通知谁（三条，直接转发即可）

1. **给成员4（测试与验证）**：
   - `tests/coverage.csv` 需要重新生成（`k_text` 取自新的 `data/tasks/*.yaml`）；
   - 跟着改的用例：`P17` 的删除/修改期望码（8004/8005）、`S11` 过渡期期望 0 与 1 Hz 相位写 X、
     `P19-02/03/04` 限位相关条目（极性本身不用改，你的用例已经是对的）；
   - 条款号一个都没动，`spec_refs` 不用改号。
2. **给成员2（框架）**：`agent/src/parse.py` 里 `if tid == "P08" and "count > 32" in spec_text:`
   这段提示分支可以删了（C2b 已不再有 32 路上限），不删也不会报错，只是永远不会命中。
3. **给成员3（报告）**：第 2 章改两处数字（条款 178→177、P08 那行 6→5、S11 5→4）；
   第 4 章可加一句「P19 判据方向修正后，失败归因应为『程序在急停期间未封锁动作』」；
   实验记录不重跑（数据只改判定口径，不改输入输出）。

---

## 7　如果 repo 里已经有 `data/`（万一别人先传了）

```powershell
git pull --rebase
# 先看冲突面：只应出现在 data/ 与 docs/ 下
git status --short
```

以本包为准（本包是 v1.7，含 34 题全量与 R7—R14 修订），逐文件覆盖后
`python tools\schema_check.py` 必须通过；若别人也加过题，先在群里确认题号是否冲突再合并——
题号是全局唯一契约，两套编号并存会让下游的 `task_id` 全部对不上。

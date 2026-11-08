# 成员2提交包：PLC ST Agent 框架 v1.1

本包对应分工清单 D2.1—D2.8 / A2，已接入组员1提交包 v2.1 中的数据版本 v1.6。包含7个核心模块、统一入口、3套提示词、参数配置、Aider现成框架适配、CODESYS编译桥、运行记录、架构说明、报告第3章和3条答辩问答。

**当前交付状态：CODESYS SP22 Patch 4与MATIEC已安装并真实接通；34题声明骨架33通过，P18的VARIANT不受当前profile支持。真实模型生成和成员4功能测试仍待接通。`fixture`中的passed仅表示框架演示出口，不能计入实验通过率。** 本包不包含API密钥，也不替成员3编造四组实验结果。

## 先用三条命令本地验收

在本文件所在目录打开终端，使用 Python 3.10+：

```powershell
python -m pip install -r requirements.txt
python agent/run.py --framework self --model fixture --tasks data/tasks/S01.yaml --out runs/demo --mode fixture
python agent/run.py --framework self --model fixture --tasks data/tasks --task-set all34 --out runs/all34 --mode fixture
```

第二条能看到“生成3候选 → 模拟编译失败 → 增量修复 → 模拟测试通过”的完整连线；第三条遍历34题。再次执行相同命令会显示`SKIP`。这三条命令无需模型接口或PLC软件，不收费。示例记录也附在`agent/logs/`。

运行程序自身的检查：`python -m unittest discover -s tests_unit -v`。验证数据副本哈希、34题解析与日志契约：`python tools/validate_delivery.py`，结果写入`validation/`。

## 切换到真实运行

你给的DMXAPI说明已落实到`agent/src/generate.py`：`POST https://www.dmxapi.cn/v1/chat/completions`，使用`model/messages/stream=false`并读取`choices[0].message.content`。核心无需安装OpenAI SDK。

1. 向助教获取密钥，在本机设置`DMXAPI_API_KEY`。两个模型的准确名称从[模型页面](https://www.dmxapi.cn/rmb)复制；本包没有假定任何模型已经可用。密钥不填进配置文件。
2. 本机交付目录已提供`local/codesys.local.yaml`；真实入口追加`--config local/codesys.local.yaml`。其他机器按`docs/codesys_setup.md`使用随包模板生成本机配置，并按`docs/toolchain.md`接入成员4测试器。`agent/configs/default.yaml`使用JSON语法，属于YAML 1.2子集，可直接编辑。权威编译命令为空时，live入口会主动停止；目标设备、库和授权按实际机器核实。
3. 调用统一入口，例如：

```powershell
python agent/run.py --framework self --model "填写准确模型名" --tasks data/tasks/S01.yaml --out runs/E3 --setting-id E3 --config local/codesys.local.yaml
python agent/run.py --framework self --model "填写准确模型名" --tasks data/tasks --out runs/E3 --setting-id E3 --seed 42 --repeat 1 --config local/codesys.local.yaml
```

真实输出保存在`runs/E3/live/`，演示输出保存在`fixture/`。未接测试器的题只能成为`best-effort:tests_missing`，不会判passed。缺编译器或测试工具故障记录为tool_error原因，统计时与模型失败分开。所有工具结果都有原始输出。

## 数据规模与待审事项

- 默认目录入口选`core32`：P01—P20 + S01—S12，保持任务书的4×32主轮口径。
- `--task-set all34`使用组员1实际交付的34题；S13/S14保留为扩展题。成员3若决定四组全部用34题，主轮应为136跑，不能继续写128。
- P08/P14/P17/P19的既有数据矛盾写入`task_card.json.semantic_warnings`。live默认以`abandoned:data_degraded`结束；修正并重新冻结上游数据后再跑。`--allow-degraded`只供诊断，相关结果仍不进入正式统计资格。
- 规约包含有界时序和自定义命题别名；框架读取并提供给模型，不冒称已经转换为PLCverif模型。P18的VARIANT等扩展由目标profile确认。
- 原始data未改写，`data/sha256sums.txt`用于校验68份题面/规约。

## 交付物位置

| 清单 | 位置 | 用途 |
|---|---|---|
| D2.1 | `agent/src/{parse,task_card,generate,tools,repair,terminate,logging}.py` | 七模块源码 |
| D2.2 | `agent/run.py` | 单题/批量、超时隔离、断点续跑 |
| D2.3 | `agent/prompts/*_v1.md` | 生成、增量修复、评审提示 |
| D2.4 | `agent/configs/default.yaml` | 候选、预算、时间、工具接口 |
| D2.5 | `agent/logs/` | 34题连线记录及5类出口演示；真实≥5题证据待补 |
| D2.6 | `docs/framework.md`、`docs/report/ch3.md` | 架构图、执行图、能力映射与报告正文 |
| D2.7 | `docs/env.md`、`docs/toolchain.md` | 环境记录、编译profile与桥接协议 |
| D2.8 | `baseline/` | Aider适配器、判定桥、快捷调用 |
| 答辩 | `docs/qa/member2.md` | 3条问题及证据位置 |

## 基线接入与公平性

本包选Aider作为任务书允许的“等价开源CLI Agent”，原因是你提供的DMXAPI文档只明确Chat Completions格式。已核对[Codex非交互文档](https://learn.chatgpt.com/docs/non-interactive-mode)，但不能据此假定DMXAPI支持Codex所需接口，因此不把未经接通的Codex标成可用基线。

Aider需在独立Python环境安装`aider-chat`，随后配置`baseline.command`为该环境的可执行命令。入口只改`--framework baseline --setting-id E1`；模型参数仍填同一个准确模型名，适配器内部添加Aider的`openai/`路由前缀。Aider的`--auto-test --test-cmd`使用与自研相同的编译和测试适配器。其原生反思策略由所装版本决定，须在实验报告如实记录；本包没有虚构`--max-reflections`参数。[官方兼容接口说明](https://aider.chat/docs/llms/openai-compat.html)、[自动测试说明](https://aider.chat/docs/usage/lint-test.html)。

## 日志与续跑规则

每个run目录含`task_card.json`、`skeleton.st`、候选和修复源码、编译/测试原始输出、`repair_N.diff`、`events.jsonl`、`metadata.json`与严格22字段`run.jsonl`。`compile_status`只按权威通道判定；首轮状态另存metadata，用于区分首轮和修复后通过率。`metadata.execution_mode`和`eligible_for_experiments`必须与主记录联读。

`run_id={setting}_{task}_{repeat}_{seed}`。终态结果自动跳过；数据、规约、配置、提示、源码或用例变化会拒绝复用同一run_id，须使用新的输出目录。进程被强制终止时，如留下`running.lock`，先核对锁中PID确实已退出，再删除该锁。API请求发送前写pending记录；若无法确认远端是否已计费，默认不重发，需人工核对后显式用`--retry-uncertain`决定是否重试。自动续跑不能承诺已发出请求绝不收费。

Token字段来自远端usage，缺失时为null；不从终端摘要推算为真实账单。上下文6000是离线估算预算，并非所选模型精确分词。默认不发送DMX文档未保证的temperature/seed参数；确认模型支持后才改开关。因此真实模型同seed不能保证逐字一致。

## 给成员3、4、5的交接

- 成员3：先接通真实单题，确认metadata模式和资格，再跑同一题集的四种设置。模型A/B版本、Aider版本、编译profile、超时、用例版本必须固定。演示记录不要放进实验summary。
- 成员4：按`docs/toolchain.md`提供可命令行调用的测试器，返回稳定case_id、通过ID、失败周期、输入/期望/实际值。框架以用例身份检查回归，回归即回滚。
- 成员5：将本包根目录内容合并到总仓库，同名data先校验哈希再合并；使用`docs/env.md`补全真实机器资料。正式封包前至少补足5题真实日志并在另一台同环境机器复跑。


## v1.1 本机真实编译验收

专用模板agent/templates/compile_template.project已真实重建为0错0警告，固定Control Win x64、Standard/IoStandard 3.5.22.0与20ms任务。validation/codesys_release_v1.1/含40案例，约121.4秒；6探针符合预期，34骨架33通过且生成目标代码，仅P18失败。validation/toolchain_smoke_v1.1/验证了完整双通道：正确例通过约33.8秒（并发2），错误例拒绝约32.2秒（并发2）且定位源码第5行。

本机工作目录已有local/codesys.local.yaml，真实入口需追加--config local/codesys.local.yaml。新解压目录先按docs/codesys_setup.md使用本目录模板重新生成本机配置；zip不包含他人电脑不能复用的绝对路径。

```powershell
python tools/check_codesys_compiler.py --config local/codesys.local.yaml --out validation/codesys_recheck --tasks data/tasks
```

当前全量命令因P18不兼容返回1，并保留其余33题成功证据，不能写成全部通过。MATIEC对34骨架27通过、4方言失败、3超时，不替代CODESYS判定。实测边界和后续交接见docs/codesys_validation.md。

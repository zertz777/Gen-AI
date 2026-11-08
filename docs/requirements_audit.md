# 成员2任务范围核对与验收边界

本文保留 v1.1 交付时的核对口径。当前仓库的正式主轮使用 v1.7 题集的 34 道题。[仓库说明](../README.md)

核对日期：2026-10-31。依据：任务书《GenAI赋能工业编程_五人分工与交付清单》PDF第9-13页（文件第10-14页）及成员1提交包v2.1。PDF相关五页已经渲染并逐页视觉核对，以下内容没有把附件内的群通知、排期与验收签字当作已执行事项。

## 1. 题量与冻结数据

任务书基准是P01-P20、S01-S12，共32题。成员1实际提交数据版本v1.6，新增S13和S14，共34题、34份LTL、178条LTL条款、316个I/O点、143条K约束。框架按输入目录发现题目，不删除或重编号扩展题；默认`--task-set core32`使用任务书32题清单，`--task-set all34`显式运行全部34题，所有实验组使用同一清单。

若主轮采用34题，四设置主轮是136跑；仍对12题复跑则追加48跑，共184跑。176是原32题计划数字，不可将34题结果仍记作176跑。

原始成员1数据保持不变。已在原包执行只读检查：

- `tools/schema_check.py`：通过；报告24项警告，共35条K约束需要由成员4功能用例覆盖。
- `tools/ltl_check.py`：通过；34份规约共178条，命题可溯源到I/O或声明别名。

以上检查证明数据格式与规约语法/映射满足成员1校验器，不能证明PLC语义正确、功能通过或LTL属性已被模型检验。

## 2. 成员2交付项

| 编号 | 必交路径 | 任务书要求 |
| --- | --- | --- |
| D2.1 | `agent/src/` | parse、task_card、generate、tools、repair、terminate、logging七模块，含边界处理与注释 |
| D2.2 | `agent/run.py` | self/baseline统一入口，framework/model/tasks/out/seed/repeat参数，断点续跑 |
| D2.3 | `agent/prompts/` | 生成、修复、评审三套有版本的提示词 |
| D2.4 | `agent/configs/default.yaml` | 候选数、修复轮数、超时、预算参数化 |
| D2.5 | `agent/logs/` | 至少5题完整运行记录，包含失败题；任务书明确要求编译证据 |
| D2.6 | `docs/framework.md` | 架构图、执行流程图、五项能力与实现对照 |
| D2.7 | `docs/env.md` | 环境、编译profile、版本、许可说明 |
| D2.8 | `baseline/` | 现成框架适配层与调用脚本 |

此外，排期指定 `docs/report/ch3.md` 作为报告第3章素材；全组要求 `docs/qa/member2.md` 提供3条答辩问答及证据路径。D2.7、D2.8位于清单续页，不能遗漏。

## 3. 必须兑现的运行契约

1. 双通道编译：MATIEC或RuSTy快检；CODESYS脚本编译作为唯一正式编译通过依据。诊断统一为code/severity/line/message/raw。未安装编译器是工具故障，不能替代成通过。
2. 从题面产生task_card.json和ST骨架；缺字段degraded=true，不猜需求或悄悄改I/O。
3. 四级上下文：题面、规约必留；参考可裁；上一轮诊断按轮替换。6000 token是预设预算，必须说明token估算方法与超限处理。
4. 默认3候选、上限5，温度0.2/0.6/0.9；编译过滤后按通过用例数、修复轮数、token数排序。
5. 最多5轮修复、连续2轮无改进提前停；基于错误行附近上下文产生增量修改，逐轮回归，破坏已通过用例须回滚。
6. passed/best-effort/abandoned出口及原因；单题900秒硬超时，超时落盘且不阻塞后续题。
7. self和baseline使用同一外部编译/测试判定、同超时、同题集、同日志schema。已完成run_id重启跳过；中断请求仍可能已被服务商计费，不能承诺所有崩溃重启零重复费用。
8. 主日志保持表4-4的22字段；额外过程事件、provider原始统计、工具故障类型可另存trace/manifest，避免污染下游字段契约。日志不能泄露API key。

任务书4.7的四项正式验收是：单命令产出并有真实编译证据；同题同seed结论一致；失败轮次/错误/差异可定位；换机器按README复跑一致。模拟工具与本地单测只能验证框架自身行为，不能自动满足这些正式验收。

## 4. 本机只读环境核查

核查包括初始目录检查与后续官方安装、签名核验和真实编译；未读取API密钥或调用付费模型。

| 项目 | 核查结果 |
| --- | --- |
| 系统 | Windows；PowerShell |
| 默认Python | 3.14.4 |
| Bundled Python | 3.12.14；含pypdf/reportlab/pdfplumber/Pillow，无PyYAML/pytest |
| Poppler | pdftoppm可用，已渲染原任务书相关页 |
| Codex CLI | 0.165.0-alpha.1.2，可获取版本；临时目录清理有访问权限警告 |
| CODESYS | 已安装x64 3.5.22.40；模板通过，34骨架33通过，P18不支持VARIANT |
| MATIEC/RuSTy | MATIEC已构建实测；RuSTy未安装 |
| Aider | 未发现已安装CLI |
| 模型服务 | 用户提供DMXAPI Chat Completions地址；此审查时未获得实际model ID与API key |
| 成员4执行器 | 当前只收到成员1包，未收到真实逐周期用例与执行器 |

“未发现”限定在上述检查范围，不等同于证明整台电脑所有磁盘均不存在软件。模型服务、编译器及成员4执行器接通前，所有fixture日志必须标注为框架演示证据，不得写成真实PLC通过率。

## 5. DMXAPI现成框架接入建议

Aider是任务书允许的等价开源CLI Agent。官方文档明确支持OpenAI compatible端点，可避免在只给出Chat Completions接口时假定Codex的Responses接口也兼容。

适配时将用户提供的 `https://www.dmxapi.cn/v1/chat/completions` 拆成base URL `https://www.dmxapi.cn/v1`；给Aider的model参数使用 `openai/` 加用户实际模型ID。Key通过子进程环境变量OPENAI_API_KEY注入；不得写入argv、源码、日志、提交包。base可通过OPENAI_API_BASE或--openai-api-base传递。

可用于非交互适配的命令形态（所有尖括号为配置值，不是已验证可用的模型名称）：

```text
aider --model openai/<实际模型ID> --weak-model openai/<实际模型ID> --openai-api-base https://www.dmxapi.cn/v1 --message-file prompt.txt --yes-always --no-stream --no-git --no-auto-commits --no-check-update --no-analytics --no-auto-lint --map-tokens 0 --edit-format whole solution.st
```

CLI应在每题隔离目录运行。实际`baseline/adapter.py`还附加`--auto-test --test-cmd <统一judge命令>`，使Aider编辑后调用`baseline/judge.py`，使用同一Toolchain获得编译与功能反馈；Aider日志与最终solution.st留档。正式比较应记录确切Aider版本、模型返回ID、完整配置、重试次数，以及服务商不保证seed确定性的事实。不能用自研Chat API封装冒充“现成Agent基线”。本机未安装Aider，也未验证DMXAPI实际连通性；上述形态依据官方接口文档，接通后还须现场验收。当前官方CLI未定义`--max-reflections`，原生反思上限由实际安装版本决定，不臆造五轮参数。

官方依据（2026-10-31查阅）：

- [Aider OpenAI compatible APIs](https://aider.chat/docs/llms/openai-compat.html)：base/key环境与openai/模型前缀。
- [Aider scripting](https://aider.chat/docs/scripting.html)：单次--message/--message-file后应用修改并退出。
- [Aider options](https://aider.chat/docs/config/options.html)：非交互、API、输出、Git、编辑格式等配置项。
- [Aider installation](https://aider.chat/docs/install.html)：建议隔离安装，当前官方安装说明优先Python3.12环境。

## 6. 报告中不能当成实测结论的数字

3候选、5轮修复、900秒单题、6000 token、90秒权威编译和并发2可作为沿用任务书的预设参数。任务书引用的“8候选token高38.8%”“超过5候选不提升”等陈述，未核对原论文前不应写成本项目实测结果。

任务书称176跑、并发2、每题900秒能够保证8小时完成，这不是最坏情况算术：176×900÷2=22小时；34题口径184跑是23小时。因此报告应把批处理时长写为真实测量值，或清楚区分预计平均时长与超时上界，不能复述为保证。


当前编译实测详见docs/codesys_validation.md。D2.5真实模型端到端日志、成员4功能用例、Aider实跑与跨机复现仍待后续条件。P18原数据未改写，不兼容单列。

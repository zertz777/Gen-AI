# 成员2答辩问答与证据

文中的 `agent/logs/` 和 `tests_unit/` 随原交付包保存。[演示日志](../../release/member2-v1.1/成员2_提交包_v1.1/agent/logs) · [框架单测](../../release/member2-v1.1/成员2_提交包_v1.1/tests_unit)

## 问1：这个Agent体现了哪些能力，为什么不能把编译通过当作正确？

答：解析器组织题面并生成任务卡；上下文模块保留需求与规约、记录裁剪；统一工具层调用编译和逐周期测试；修复模块按诊断生成局部补丁并回归；终止模块限制轮数、停滞、时间和预算。正式编译通过只由CODESYS权威通道给出，功能passed还要求成员4非空用例全部通过。快检和fixture都不能替代正式证据。本机已真实编译34题声明骨架，33题通过并生成目标代码，P18因VARIANT不兼容失败；这是环境兼容性检查。模型生成程序的编译率和功能率仍需真实模型及成员4用例后补跑。

证据：`agent/src/parse.py`、`task_card.py`、`tools.py`、`repair.py`、`terminate.py`；`docs/framework.md`五项能力表；运行目录中的`metadata.json`、编译原始输出和功能结果。演示证据请指向`agent/logs/`的实际fixture运行目录，且说明`eligible_for_experiments=false`。

## 问2：修复怎么避免越改越坏，失败怎么追溯？

答：每轮只反馈诊断和错误行附近±3行代码及失败用例，模型返回唯一匹配的局部替换JSON。框架拒绝无目标、目标重复、过大替换等情况，保存差异，再重新编译并执行全量回归。若编译由pass退化，或者先前通过的case_id从本轮通过集合消失，框架回滚。最多5轮或连续2轮无改进就停止。这个机制依赖成员4提供稳定用例ID，尚不能把演示结果说成真实PLC程序“绝无回归”。

证据：`agent/src/repair.py`的`feedback/apply_patch/regresses`；`agent/run.py`的修复循环；单题`repair_N.diff`、`repair_N.evaluation.json`、`events.jsonl`。相关框架测试见`tests_unit/`。

## 问3：如何保证比较公平、结果可复现，为什么仍有未验收项？

答：self和现成Aider基线共用题集、900秒外部超时、编译/测试桥及22字段结果契约。任务书主轮用core32，扩展all34另标记，不能把34题主轮写成128跑。题面、规约、代码、配置和用例参与指纹，已完成同指纹run_id跳过；请求缓存避免已完成响应重复调用，pending请求必须先核实远端状态，断网并不保证未计费。seed是记录项，远端服务不保证完全确定性。本机CODESYS SP22 Patch 4与MATIEC已实测接通，完整编译桥在并发2时符合90秒配置。当前未获得模型Key/准确ID和成员4执行器，Aider尚未安装实跑，因此至少5题真实Agent日志、模型实验和跨机一致性仍待验收，不能用fixture填写正式通过率。

证据：`agent/src/logging.py`的22字段；`agent/run.py`的manifest、锁、跳过与批量汇总；`agent/src/generate.py`的缓存/pending；`docs/env.md`、`docs/requirements_audit.md`。基线版本和原生反思上限应在真正安装Aider后登记，不添加官方未提供的`--max-reflections`参数。

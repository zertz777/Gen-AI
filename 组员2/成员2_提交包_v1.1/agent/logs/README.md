# 框架演示记录

这里全部是fixture：没有真实模型调用、PLC编译或成员4功能测试。metadata中均为execution_mode=fixture、eligible_for_experiments=false；不满足D2.5至少5题真实Agent证据，不能计入正式实验统计。

- full34_fixture/：34题框架连线，每题含候选、模拟诊断、修复差异、过程事件与22字段终态。
- scenario_fixture/：passed、best-effort、abandoned、timeout、tool_error出口及baseline分支。baseline演示没有调用Aider。
- 实际CODESYS/MATIEC证据另见validation/，这些是无模型的编译环境检查。

为移交目录，公开日志中的本机路径已重定位；原时间、运行结果、源码字节与源码SHA256保持不变。此处保存的是演示证据副本，正式运行请使用新的runs目录。metadata.first_compile_status记录所选候选首轮状态，全部候选首轮通过率须从各candidate_N.evaluation.json按统一口径汇总。

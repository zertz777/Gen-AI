GenAI 赋能工业编程期末大作业 A1-A7 提交包

解压后在根目录按 README.md 的三条命令先做无费用 fixture 验收。
真实模型与 CODESYS 复现需要额外配置，见 docs/env.md、docs/codesys_setup.md 和 docs/toolchain.md。

目录：
A1_报告：Word 与 PDF
A2_框架源码：自研 Agent、Aider 适配层、配置与示例日志
A3_题集与规约：34 份题面与 LTL
A4_测试与验证：用例、执行器、缺陷单、变异测试与 PLCVerif 材料
A5_实验原始数据：136 个最终 run、32 个修订 run、原始批次、汇总与 4 图
A6_运行说明：README、环境、工具链与问答
A7_汇报材料：15 页 PPT、讲稿与主问答

实验结果的已知限制：
- E3 有 24 题受预算终止影响，其中存在 token 预算实现问题。
- P19、S11、S05-06 的判据争议不能作为框架或模型优劣的决定性证据。
- 精简实验包只保留结果、候选评估和最终 ST，不包含完整逐拍 actual 中间文件。
- 换机复现模型、CODESYS 和 Aider 尚未验证。

本包不含 API Key、本机绝对路径或临时文件。

备份建议：
- 将本 ZIP 上传云盘并保留一份本地硬盘副本。
- 将 A1 的 PDF与 A7 的 PPT 另存到演示 U 盘。
- 现场演示使用本包内 PPT；完整 CODESYS 逐拍重放仍需实验机原始批次。

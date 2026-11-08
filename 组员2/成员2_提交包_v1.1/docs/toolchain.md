# 编译与判定工具接入

本交付已实现工具调用、结果协议、超时回收和错误归一化。本机已安装CODESYS 3.5.22.40和官方源码构建的MATIEC，并完成真实编译联调，详见docs/codesys_validation.md；成员4逐周期执行器仍待接入。`--mode fixture` 运行的是框架集成样例，不产生可用于 CPR/EPR/VPR 的 PLC 实测证据。

## 1. 共同协议

`agent/src/tools.py` 的 `Toolchain` 接收配置、单题绝对截止时间（`time.monotonic()`）和产物目录。`fast`、`authoritative`、`test`、`verify` 四个配置节点均支持 `command`（argv 数组）和 `timeout_s`；`command` 不经过 shell。默认工作目录是项目根目录，可用节点内 `cwd` 覆盖。不存在的可执行文件记 `tool_error`，子进程超时记 `timeout`，不冒充模型失败。

| 占位符 | 注入内容 |
| --- | --- |
| `{source}` | 本次调用保存的 UTF-8 ST 源文件 |
| `{result}` | 本次调用应写入的 JSON 结果文件；执行前删除旧结果 |
| `{task_card}` | 当前任务卡路径，含 I/O、规约和初态 |
| `{artifact_dir}` | 本次工具调用的独立产物目录 |
| `{cases_dir}` | `test.cases_dir` 配置值，默认 `tests/cases` |

各工具的 `source.st`、`stdout.txt`、`stderr.txt`、`process.json` 存在 `tools/<候选或轮次>/<通道>/` 下；权威编译另存 `normalized.json`。工具主动生成的结果保留为 `result.json`。日志不保存环境变量。API 凭据不应放进 argv 或配置。

权威编译是最终编译状态的依据。快检结果单列保存，用于诊断；快检器与 CODESYS 方言不一致时，不用快检的失败替代权威编译结果。快检缺失也会保留为工具故障，不写成已完成双通道验收。

## 2. MATIEC 快通道

安装并固定团队统一的 MATIEC 版本后，配置可采用：

```json
"fast": {
  "command": ["iec2c", "-f", "-T", "{artifact_dir}", "{source}"],
  "timeout_s": 3,
  "kind": "matiec"
}
```

`-f` 请求更完整的位置诊断，`-T` 将生成的 C 文件放入独立目录。所需头文件/标准库搜索路径可按安装情况增加 `-I` 参数。MATIEC 完成 ST 到 C 的转换，不等于已生成可运行的本机程序。它基于较早的 IEC 61131-3 文本语言定义，CODESYS 的变长数组等特性需要单独核对。该调用形态和参数来自 [MATIEC 仓库](https://github.com/beremiz/matiec)及[命令行源码](https://github.com/beremiz/matiec/blob/master/main.cc)。

工具层不硬编码 RuSTy 的版本专用参数。改用 RuSTy 时将同一 `fast.command` 换成经团队机器验证的 argv，记录版本和调用参数，保持 `timeout_s`、错误格式和权威通道不变。

## 3. CODESYS 权威通道

提供两个脚本：

- `agent/scripts/codesys_bridge.py` 在普通 Python 中运行：检查路径、复制模板工程、写请求、启动 CODESYS。
- `agent/scripts/codesys_compile.py` 在 CODESYS 的脚本引擎中运行：导入 TYPE 与单一 POU、强制链接、重新编译、收集消息并写 JSON。

先在团队机器准备一个干净的专用模板 `local/compile_template.project`：含目标设备、应用、任务和所需库；应用默认名 `Application`。模板中不要存在与题目 POU 或 TYPE 同名的对象。模板只被复制，不会被覆写。实际 profile 必须采用该安装的“帮助→关于”所示名称。

在本机配置中将示例中的安装路径标记替换成真实值后使用：

```json
"authoritative": {
  "command": [
    "python", "agent/scripts/codesys_bridge.py",
    "--source", "{source}", "--result", "{result}",
    "--task-card", "{task_card}",
    "--exe", "REPLACE_WITH_CODESYS_EXE_PATH",
    "--profile", "REPLACE_WITH_INSTALLED_PROFILE",
    "--template", "local/compile_template.project",
    "--application", "Application"
  ],
  "timeout_s": 90
}
```

若使用同版本的多个安装实例，按实际安装补 `--additionalfolder`。启动桥通过子进程环境传递请求路径，避免复杂的 `--scriptargs` 引号问题。脚本使用 CODESYS 的 [`--runscript` 与 `--noUI`](https://content.helpme-codesys.com/en/CODESYS%20Development%20System/_cds_commandline.html)、[对象创建与文本编辑](https://content.helpme-codesys.com/en/ScriptingEngine/ScriptIecLanguageObjectContainer.html)、[`rebuild()`](https://content.helpme-codesys.com/en/ScriptingEngine/ScriptApplication.html)及[消息接口](https://content.helpme-codesys.com/en/ScriptingEngine/ScriptSystem.html)。

每个导入 POU 的声明首行插入 [`{attribute 'linkalways'}`](https://content.helpme-codesys.com/en/CODESYS%20Development%20System/_cds_pragma_attribute_linkalways.html)，使未被任务调用的 POU 也进入编译，避免只编译到模板空工程。

权威通道必须写如下 JSON。`pass` 同时要求外层进程退出码为0、错误列表中没有 error/fatal 级诊断；仅看到 stdout 的“0 errors”不接受为通过。

```json
{
  "status": "fail",
  "errors": [
    {"code": "E_UNDECLARED", "severity": "error", "line": 12,
     "message": "Unknown identifier Motor", "raw": "原始诊断完整文本"}
  ]
}
```

允许 `status=pass/fail/timeout/tool_error`。诊断固定包含 `code/severity/line/message/raw`；没有可靠行号时 `line=null`。未知变量、类型错误、缺库、语法错误、死代码分别归并到 `E_UNDECLARED/E_TYPE/E_LIBRARY/E_SYNTAX/W_DEAD_CODE`。死代码是 warning，不能单独判编译失败。当前代码对常见文本格式做归一化；当前安装已通过中文原生诊断校准所属对象的Decl/Impl位置；未知对象或格式保持line=null。

该导入桥接受多个顶层 `TYPE` 和一个 `PROGRAM/FUNCTION_BLOCK/FUNCTION`；会识别注释与字符串中的伪关键字。多 POU、METHOD、ACTION、INTERFACE、CLASS 等成员/面向对象结构拒绝导入并记工具适配失败。模板、设备、库及引擎版本未满足时也记 `tool_error`，不能拿来计算模型编译失败率。桥接脚本通过 Python 语法检查及受控拆分测试，已在CODESYS Scripting 4.2.0.0中实测，重建与目标代码生成分别留证。

## 4. 成员4的逐周期测试接口

功能测试不由文本关键字判断。成员4将自己的执行器命令接入 `test.command`，并接收 `{source}`、`{task_card}`、`{cases_dir}`、`{result}`。用例 CSV 的具体列由成员4定义；本层只约束判定结果 JSON：

```json
{
  "status": "fail",
  "total": 3,
  "passed": 2,
  "passed_ids": ["safe_stop", "lower_boundary"],
  "failures": [
    {"case_id": "restart", "cycle": 12, "signal": "Motor",
     "expected": false, "actual": true}
  ]
}
```

`passed_ids` 必须是通过用例的稳定唯一标识，长度等于 `passed`；修复回归以 ID 集合比较，不能只比较通过数量。`total/passed` 必须是非负整数且 `passed<=total`；`pass` 要求至少1条用例、全部通过且进程退出码0。用例缺失记 `skipped`，协议错记 `tool_error`。`failures` 应给出 case_id、周期号、信号、期望与实测，供下一轮逻辑修复和缺陷定位。

可选的 `verify.command` 写 `{ "status": "pass|violated|timeout|skipped", "reason": "..." }`。未接验证器记 `skipped`；fixture 永远不提供形式化验证通过记录。

## 5. 联调与证据边界

本地工具单测覆盖了五类已知诊断、子进程超时、缺工具、权威返回缺失或矛盾、空测试拒绝、部分通过用例 ID 保留、fixture 标识以及 ST 导入边界。运行：

```bash
python -m unittest tests_unit.test_tools -v
```

这些是 Python 适配器测试，不能替代 T2.1 的快检≤3秒、权威编译≤90秒实测。上机时以5个已知错误样本分别运行两通道，保存原始日志、实际耗时、profile及库版本；随后编译全部空骨架，再连接成员4用例与真实模型运行至少5题（含失败题）。完成后才将验收表中的相关待联调项改为完成。

fixture 支持 `FIXTURE_COMPILE_FAIL/FIXTURE_TEST_FAIL/FIXTURE_TIMEOUT/FIXTURE_TOOL_ERROR` 标记来驱动分支；所有结果均带 `evidence_kind=fixture`，`authoritative_available=false`。这些标记只用于框架测试，不是模型输出的判题规则。

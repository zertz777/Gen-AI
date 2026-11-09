# 编译环境真实验收记录

日期：2026-10-31。范围仅为编译环境、骨架兼容性和框架工具接口；没有调用模型，没有运行成员4功能用例，也未连接/下载/启动PLC。

## 已安装并核实

CODESYS Development System x64 3.5.22.40（SP22 Patch 4）、安装实例GenAI、CODESYS Scripting 4.2.0.0。官方安装管理器2.6.1.0及完整IDE安装包均通过Windows Valid签名校验，发布者CODESYS Development GmbH。

真实枚举1559条设备描述和528个库条目后，选取Control Win V3 x64（type4096，id 0000 0004，version3.5.22.40），固定Standard和IoStandard 3.5.22.0（System）。模板MainTask为20ms。agent/templates/compile_template.project由自带标准工程克隆、更新设备和旧库引用后重建，0错误、0警告；原厂模板未覆写。模板占位逻辑不代表题目实现。

MATIEC来自官方固定commit 3a41303bcb4e50403417bc39c63f88981d7d961e，本机构建静态程序；源码归档SHA256为21d249d9c65ff1a26404cfe0969a14a0c12d05e53871e26d77bdd4e8fd0a89a2。版本输出0.1，准确版本以commit为准。

## 权威编译证据

validation/codesys_release_v1.1/含一次IDE启动中的40案例，每例单独复制工程，保存源码、原始诊断、build/generate阶段、源SHA256和生成代码状态。

| 范围 | 实测 | 证明范围 |
|---|---|---|
| 正确小程序 | pass，code_generated=true | 导入、重建及目标代码生成可用 |
| 未声明、类型错、语法错、未定义依赖 | 4个负例均被拒绝 | 没有只编译空模板而误判通过 |
| 常量死分支 | pass，无警告 | 不强制编译器对所有死代码发warning |
| 34题声明骨架 | 33通过并生成目标代码，P18失败 | 接口/声明兼容，不是功能或模型通过率 |

全批实测约121.4秒，含一次IDE启动。每例耗时见cases.csv；不能把它当作每题独立冷启动时间或模型端到端时长。完整单题工具链证据见validation/toolchain_smoke_v1.1/。

P18原题的VARIANT在本profile中被拒绝为未知类型。没有擅自替换成整数、BOOL、指针或自造结构体。需成员1与成员4约定可接受载荷类型后重新冻结，或另选确认兼容的profile。本机配置登记unsupported_types=[VARIANT]，真实Agent在付费请求前退出abandoned:unsupported_type，不计为模型失败。

## 快检与修复

validation/matiec_live_r2/记录6探针和34骨架的真实MATIEC调用。骨架27通过、4失败、3超时；完成的案例最高约0.203秒。P07/P08/P14/P17有方言差异，P04/P12/P18涉及LTIME/VARIANT；快检不替代权威判定。

联调修正了Windows原始命令行引号、CRLF/BOM原始字节校验、Python2编码声明、非英文名称Unicode序列化、空骨架RETURN占位、同名任务调用识别及旧库引用。权威成功必须同时有rebuild和generate_code证据。原生错误所属对象、Decl/Impl位置和源码映射依据均保留，无法可靠映射时line=null。

## 仍待完成的外部条件

真实DMXAPI Key、准确模型ID和成员4执行器/用例尚未提供。D2.5至少5题真实Agent完整日志、模型同seed复跑和跨机复现，不能由本次编译检查替代。agent/logs中的fixture记录始终不进入正式统计。

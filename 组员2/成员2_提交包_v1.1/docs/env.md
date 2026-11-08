# 环境与编译profile登记

登记日期：2026-10-31。本机已完成CODESYS安装、脚本启动、设备/库枚举、模板重建及真实批量编译。原始证据见validation/codesys_release_v1.1/。

| 项目 | 已核实内容 |
|---|---|
| 系统 | Windows 64位，系统版本10.0.26200 |
| Python | 标准库框架，Python3.10+；本次检查使用3.12.14，默认3.14.4也已验证离线入口 |
| CODESYS IDE | x64 3.5.22.40，profile为CODESYS V3.5 SP22 Patch 4 |
| 安装实例 | GenAI；启动固定该实例additionalfolder |
| 脚本引擎 | CODESYS Scripting 4.2.0.0，内置IronPython2.7 |
| 目标设备 | CODESYS Control Win V3 x64，type4096、id 0000 0004、version3.5.22.40 |
| 模板 | agent/templates/compile_template.project；Application、MainTask、20ms；真实重建0错0警告 |
| 核心库 | Standard 3.5.22.0、IoStandard 3.5.22.0（System）；其余依赖见模板和枚举记录 |
| MATIEC | 官方commit 3a41303bcb4e50403417bc39c63f88981d7d961e本机构建，静态链接；版本输出0.1 |
| 权威检查 | 6个诊断探针符合预期；34骨架33通过并生成目标代码，P18因VARIANT不支持失败 |
| 快检 | 34骨架27通过、4方言失败、3超时；不替代权威判定 |
| 模型与测试 | DMXAPI格式已接入；真实Key、准确model ID和成员4执行器/用例尚缺 |
| 基线 | Aider适配器已交，CLI尚未安装实跑，不作为已完成基线实验 |

IDE和Python实际安装路径保存在本机local/codesys_environment.json；公开编译证据也保留模板与二进制哈希，文本中的本机路径已重定位。移交后重新执行tools/configure_codesys.py，并核对同版设备和库。

Key仅从DMXAPI_API_KEY读取，不进入源码或配置。temperature/seed默认不发送；远端usage缺失记null；同seed不承诺服务端逐字一致。

本包不附带CODESYS安装程序、许可证或第三方库二进制。IDE离线编译和生产运行时授权不同，本次未连接、下载或启动PLC。MATIEC官方源码构建记录和GPL许可保存在本机工具目录。

# 环境与复现登记

登记日期：2026-11-09。本文件合并成员2的本机编译验收记录和成员3的正式实验配置，供成员5在提交前复核。任何换机实验都必须重新登记实际版本，不能直接沿用本表声称已复现。

## 1 软件与模型

| 项目 | 已核实内容 |
| --- | --- |
| 操作系统 | Windows 64位，10.0.26200 |
| Python | Agent 核心支持 Python 3.10+；成员2验收使用 3.12.14，打包环境使用 Python 3.13.9 |
| CODESYS | x64 3.5.22.40，profile 为 CODESYS V3.5 SP22 Patch 4 |
| CODESYS 脚本引擎 | 4.2.0.0，内置 IronPython 2.7 |
| 目标设备 | CODESYS Control Win V3 x64，type 4096，id 0000 0004，version 3.5.22.40 |
| 核心库 | Standard 3.5.22.0、IoStandard 3.5.22.0 |
| 编译模板 | `agent/templates/compile_template.project`，Application、MainTask、20 ms；真实重建为 0 错误、0 警告 |
| MATIEC | 官方 commit `3a41303bcb4e50403417bc39c63f88981d7d961e` 的本机构建，版本输出 0.1 |
| 基线框架 | Aider 0.86.2 |
| 模型 A | `deepseek-v4.1-flash` |
| 模型 B | `gpt-6.1-sol` |
| 模型网关 | DMXAPI Chat Completions，base URL `https://www.dmxapi.cn/v1` |
| 扫描周期 | 20 ms |
| 单题硬超时 | 900 s；权威编译 90 s，快检目标 3 s |

硬件型号、CPU、内存和磁盘型号未出现在成员2/3的交接记录中，因此本报告不补猜。正式实验矩阵截至 2026-11-01，使用同一台实验机；换机实验尚未完成。

## 2 编译验收

成员2已真实启动 CODESYS，完成 6 个诊断探针和 34 题声明骨架检查：33 题通过并生成目标代码，P18 因当前 profile 不支持 `VARIANT` 失败。完整双通道在并发 2 时，正确例约 33.8 s，错误例约 32.2 s，均低于 90 s 上限。MATIEC 对声明骨架为 27 通过、4 个方言失败、3 超时，只作快通道，不替代 CODESYS 权威结果。

上述结果只证明接口和编译环境，不证明模型生成程序的功能正确性，也不计入模型编译通过率。

## 3 正式实验配置

四组设置均覆盖 P01-P20 与 S01-S14，共 34 题：

| 组别 | 框架 | 模型 | 题数 |
| --- | --- | --- | ---: |
| E1 | Aider | `deepseek-v4.1-flash` | 34 |
| E2 | Aider | `gpt-6.1-sol` | 34 |
| E3 | 自研 Agent | `deepseek-v4.1-flash` | 34 |
| E4 | 自研 Agent | `gpt-6.1-sol` | 34 |

本地 seed 统一为 42，但 API 请求默认不发送 seed，因此它只是运行标识，不保证模型输出逐字复现。正式实验共 136 个最终 run；P01、P08、P13、P14、P17、P18、P19、S11 判据修订后，四组各补跑一次，共 32 个替换 run，未与旧记录相加。

## 4 凭据与限制

API Key 只从 `DMXAPI_API_KEY` 环境变量读取，不进入源码、配置、日志或提交包。`local/codesys.local.yaml`、CODESYS 安装程序、许可证和第三方二进制不进入仓库。Aider 需在独立环境安装，命令和版本须在换机后重新登记。

正式实验仍有以下限制：模型 usage 不完整时 token 记为未知；E3 原版框架的 token 预算实现存在字节长度误当 token 的问题；P19、S11、S05-06 等判据争议未全部消除；精简实验包不包含完整逐拍 actual 中间文件。详细口径见 `experiments/statistics_notes.txt`、`docs/判据待核查.md` 和 `docs/统稿前审查说明.md`。

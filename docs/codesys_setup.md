# CODESYS本机环境接通

本机已完成CODESYS 3.5.22.40安装与真实编译联调，详见docs/codesys_validation.md。本文也供其他机器按同版环境接通。配置工具为`tools/configure_codesys.py`；它不安装软件、不启动IDE、不联网，不改PATH或注册表，也不写入持久环境变量。软件安装、设备/库就绪、生成工程模板和真实编译是独立步骤。部署实际状态由本机部署记录及真实编译产物确认，不能仅凭本说明或配置文件判为完成。

## 1. 安装与模板的准备条件

先使用官方安装程序完成CODESYS Development System及Scripting所需组件的安装。下载了CODESYS Installer并不表示IDE本体已经安装。安装过程如果要求管理员权限或系统确认，应由当前用户在系统界面完成。项目不附带第三方许可，也不伪造设备包、许可证或库。

安装后在IDE核实精确版本及profile名称。本包已提供经真实编译验证的`agent/templates/compile_template.project`，可在同版设备和库环境下使用。若另建模板，其中应有目标设备、Application、任务与题目需要的库，并确认模板本身能够在IDE内编译。默认应用名为`Application`；如工程采用其他名称，配置工具的`--application`必须完全一致。模板中不要预建与题目同名的POU或TYPE。框架会复制模板到每次编译目录，不修改原模板。

如果工程只在另一台机器能打开，或者依赖未安装设备/库，先补齐这些依赖。创建一个空的`.project`文件不能替代真实工程；配置工具只核对非空文件、路径、版本资源和哈希，不解释CODESYS工程格式。

## 2. 只读发现已安装路径

在本项目根目录运行：

```powershell
python tools/configure_codesys.py --probe
```

默认搜索Program Files、Program Files (x86)、ProgramData及常用CODESYS目录，最多6层，不跟随符号链接。想缩小范围时指定实际安装根目录，可重复传入`--search-root`：

```powershell
python tools/configure_codesys.py --probe --search-root "C:/Program Files/CODESYS" --max-depth 6
```

根目录不存在会列入missing_roots，不会创建目录；访问受限路径会单独报告。输出中的executables只包含名为CODESYS.exe的候选，Installer不会被当成IDE；profiles列出发现的`.profile`或`.profile.xml`文件名及可能名称，没有读取其中的环境秘密，也没有宣称该profile已适用。请在IDE“帮助/关于”核实后采用。增加`--check`可对发现的IDE文件附加只读Authenticode签名检查；查询不可用会显示not_checked，不会冒充Valid。

## 3. 生成仅供本机使用的配置

需提供三个真实值：已安装CODESYS.exe、核实过的完整profile名称、已有非空`.project`模板。以下命令展示参数形态；引号中说明文字应替换成当前机器的实际值后执行：

```powershell
python tools/configure_codesys.py --exe "实际安装目录/CODESYS.exe" --profile "实际完整profile名称" --template "agent/templates/compile_template.project" --check
```

可选参数：`--application`指定模板内应用名称；`--additionalfolder`指定实际存在的安装实例附加目录；`--out local/另一配置名.yaml`改变本机配置文件名。配置输出仅允许在项目`local/`目录内，避免安装绝对路径进入公共默认配置。缺文件、Installer路径、非PE可执行文件、空模板、错误扩展名、明显占位符会拒绝；脚本不会为缺失路径伪造文件。

生成两份文件：

- `local/codesys.local.yaml`：读取公共default.yaml后复制并设置`tools.authoritative.command`。命令使用当前Python解释器和项目中的真实编译桥，项目内文件用相对路径，外部安装路径只保存在local副本；公共默认配置不改。
- `local/codesys_environment.json`：IDE文件版本/哈希、profile、模板哈希、Python与OS信息，以及可选签名。配置器没有打开工程、核实profile或运行编译，因此这些状态明确为false/not_run。

两者不包含API key或调用者环境变量。`local/`包含本机安装路径和工程模板，应保留在编译机，不并入面向其他成员的通用源码包。改动IDE/profile/模板后重新生成配置，并使用新的正式实验输出目录。

配置器从公共default.yaml重新生成文件，只设置权威编译命令，会覆盖已有本机配置。使用本包已实测的SP22 Patch 4环境时，生成后还须在local/codesys.local.yaml的tools中登记`"unsupported_types": ["VARIANT"]`，保证P18在付费请求前被拦截。其他profile应先验证类型兼容性再登记，不能沿用未经核实的通过结论。

恢复MATIEC快检时，将同一个tools对象中的fast设为以下内容，两个“实际”路径替换为本机安装位置。超时仍为3秒，-I必须指向含标准ST库的lib目录：

```json
"fast": {
  "command": ["实际MATIEC目录/iec2c.exe", "-f", "-I", "实际MATIEC目录/lib", "-T", "{artifact_dir}", "{source}"],
  "timeout_s": 3,
  "kind": "matiec"
}
```

本机交付目录的local配置已包含这两项；通用zip不包含local。生成或修改后分别运行tools/check_fast_compiler.py和tools/check_codesys_compiler.py复核，不把路径检查当作编译完成。

## 4. 先验证编译桥，再接模型

接通编译器不要求先获得模型Key。真实编译联调应使用已知正确的小型ST和已知错误样本，明确检查新工程确实导入了题目POU，而不是只编译空模板。桥接参数和结果协议详见`docs/toolchain.md`；真实证据应包含CODESYS产生的诊断、实际耗时、源文件哈希及工程快照。

单题正式Agent运行时追加本机配置：

```powershell
python agent/run.py --framework self --model "准确模型ID" --tasks data/tasks/S01.yaml --out runs/E3_codesys --setting-id E3 --config local/codesys.local.yaml
```

该命令还需要DMXAPI密钥、准确model ID，以及成员4测试桥。仅接通CODESYS时，不能声明已经完成模型生成和逐周期功能判定。没有功能用例时只能保留可编译产物并记tests_missing；不能以0/0作为passed。

快检MATIEC/RuSTy需另行安装并配置`tools.fast`。CODESYS权威通道通过也不等于双通道、时限、全题骨架、真实5题日志、跨机复现全部完成。不同目标设备、库或编译器版本不能直接混入同一组编译通过率。

## 5. 配置工具的检查范围

运行配置器自身测试：

```powershell
Set-Location "release/member2-v1.1/成员2_提交包_v1.1"
python -m unittest tests_unit.test_configure_codesys -v
```

测试覆盖相对路径、原配置不变、哈希登记、占位符/Installer/空文件拒绝、输出目录边界、只读probe、签名路径作为数据处理以及不复制凭证。测试创建的文件明确为受控样例，不是CODESYS程序、真实工程或编译证据。

正式验收至少还需记录：

| 项目 | 应提供的证据 |
| --- | --- |
| IDE、profile、设备及库 | IDE版本、profile、编译器版本、设备描述和库清单 |
| 模板 | 真实可打开的.project、哈希及空模板编译记录 |
| 脚本化编译 | 正确程序通过、5类已知错误/警告样本、原始诊断和耗时 |
| 接入Agent | 真实模型来源、至少5题含失败题的完整日志 |
| 功能与复现 | 成员4逐周期测试、固定用例ID、另一台机器的独立复跑 |

官方接口依据：[CODESYS命令行参数](https://content.helpme-codesys.com/en/CODESYS%20Development%20System/_cds_commandline.html)、[CODESYS脚本Application接口](https://content.helpme-codesys.com/en/ScriptingEngine/ScriptApplication.html)。实际安装版本的组件、设备与profile以本机IDE为准。


本机已有local/codesys.local.yaml；新目录需使用本目录agent/templates/compile_template.project重新生成配置，不复制他人机器绝对路径。

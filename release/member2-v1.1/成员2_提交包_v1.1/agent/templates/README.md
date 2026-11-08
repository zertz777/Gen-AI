# 真实编译模板

`compile_template.project`由CODESYS自带Standard.project克隆得到，原厂文件未覆写。

- IDE/profile：CODESYS V3.5 SP22 Patch 4，3.5.22.40。
- 目标：CODESYS Control Win V3 x64，type4096，id 0000 0004，version3.5.22.40。
- 库：Standard和IoStandard 3.5.22.0（System），其余设备占位库由同版设备解析。
- 应用Application，MainTask为20ms；PLC_PRG仅写一个内部存活标志供编译。
- 真实模板重建0错误、0警告，后续33题骨架完成目标代码生成。

这份模板不实现题目逻辑，不连接/下载/启动PLC。不要将空骨架或模板的编译通过当作功能通过。另一台机器须安装同版设备和库，并重新验证模板；已知P18的VARIANT仍不受本profile支持。

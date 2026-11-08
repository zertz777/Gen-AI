# 实测与演示边界

- codesys_release_v1.1/：真实40案例，121.421秒；6探针符合预期，34题骨架33通过并生成目标代码，P18 VARIANT失败。因此批次acceptance_status=fail，不能改成全通过。
- toolchain_smoke_v1.1/：并发2，完整MATIEC→CODESYS工具桥；正确例通过33.828秒，错误例拒绝32.235秒，均在90秒上限内。
- matiec_live_r2/：真实6探针及34骨架；骨架27通过、4失败、3超时。快检不替代CODESYS结果。
- environment/：设备/库枚举、模板实测、安装结束状态和MATIEC构建来源。
- unit_tests_v1.1.txt：78项框架检查；upstream_*为原数据校验输出。
- delivery_check.json：数据哈希、日志schema及原生编译源哈希关联检查。

这些记录没有模型调用、成员4逐周期功能测试或PLC在线运行。agent/logs另存fixture演示，不进入实验通过率。公开文本证据中的本机路径已重定位，原文文件哈希见path_rebase.json；源码字节、源SHA256、工程二进制、原生消息和实测结果未改。过程中的config_sha256指编译机当时的本地配置，通用包不分发该配置。

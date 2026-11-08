# CODESYS真实编译验收

本文件只汇总本次IDE产生的编译结果；未调用模型，未运行功能测试。

验收：fail；案例：40；进程：pass；总耗时：121.421 s。

|案例|编译状态|目标代码生成|预期核对|警告数|耗时(s)|
|---|---|---|---|---|---|
|C00_good|pass|True|matched|0|10.60321044921875|
|C01_undeclared|fail|False|matched|0|2.0949630737304688|
|C02_type|fail|False|matched|0|1.9670028686523438|
|C03_syntax|fail|False|matched|0|1.9687271118164062|
|C04_missing_dependency|fail|False|matched|0|2.026458740234375|
|C05_dead_code|pass|True|matched|0|2.2057571411132812|
|task_P01_skeleton|pass|True|matched|0|2.2461166381835938|
|task_P02_skeleton|pass|True|matched|0|2.1984176635742188|
|task_P03_skeleton|pass|True|matched|0|2.5209121704101562|
|task_P04_skeleton|pass|True|matched|0|2.2629623413085938|
|task_P05_skeleton|pass|True|matched|0|2.1320648193359375|
|task_P06_skeleton|pass|True|matched|0|2.3458175659179688|
|task_P07_skeleton|pass|True|matched|0|3.6904754638671875|
|task_P08_skeleton|pass|True|matched|0|2.828460693359375|
|task_P09_skeleton|pass|True|matched|0|2.5039901733398438|
|task_P10_skeleton|pass|True|matched|0|2.5531158447265625|
|task_P11_skeleton|pass|True|matched|0|2.3378829956054688|
|task_P12_skeleton|pass|True|matched|0|2.25006103515625|
|task_P13_skeleton|pass|True|matched|0|2.5611419677734375|
|task_P14_skeleton|pass|True|matched|0|2.77154541015625|
|task_P15_skeleton|pass|True|matched|0|2.911163330078125|
|task_P16_skeleton|pass|True|matched|0|2.83343505859375|
|task_P17_skeleton|pass|True|matched|0|2.7720184326171875|
|task_P18_skeleton|fail|False|mismatch|0|2.2980117797851562|
|task_P19_skeleton|pass|True|matched|0|2.2149887084960938|
|task_P20_skeleton|pass|True|matched|0|2.3961639404296875|
|task_S01_skeleton|pass|True|matched|0|2.3539199829101562|
|task_S02_skeleton|pass|True|matched|0|2.4651641845703125|
|task_S03_skeleton|pass|True|matched|0|2.4250259399414062|
|task_S04_skeleton|pass|True|matched|0|2.3179397583007812|
|task_S05_skeleton|pass|True|matched|0|2.217010498046875|
|task_S06_skeleton|pass|True|matched|0|2.344757080078125|
|task_S07_skeleton|pass|True|matched|0|2.2947463989257812|
|task_S08_skeleton|pass|True|matched|0|2.3264694213867188|
|task_S09_skeleton|pass|True|matched|0|2.2880706787109375|
|task_S10_skeleton|pass|True|matched|0|2.6641769409179688|
|task_S11_skeleton|pass|True|matched|0|2.7012252807617188|
|task_S12_skeleton|pass|True|matched|0|2.5824203491210938|
|task_S13_skeleton|pass|True|matched|0|3.9632644653320312|
|task_S14_skeleton|pass|True|matched|0|3.1519012451171875|

缺依赖探针仅检查真实编译器拒绝未定义依赖，错误可以被归类为未知类型/未声明。死代码可以被静默优化。

完整原生诊断、源哈希和每例产物索引见summary.json与案例子目录。

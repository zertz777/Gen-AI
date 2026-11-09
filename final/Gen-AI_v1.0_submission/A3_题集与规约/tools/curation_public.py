# -*- coding: utf-8 -*-
"""curation_public.py -- 20 道公共题的人工校对字段

`tools/import_bank.py` 只负责机器搬运：从官方题库 JSON 里取出标题、难度、
需求原文、I/O 表。下面这些字段机器给不出来，逐题人工补齐：

  category        场景类别（A 开关量联锁 / B 模拟量处理 / C 状态机与节拍 / D 故障与安全）
  zh_summary      需求的中文一句话摘要（评委 10 秒看懂这题在干什么）
  initial_state   上电初值（PLC 程序必须声明，否则逐周期测试没有基准）
  constraints     约束 K1…，供规约引用；只写题目里确有依据的，不臆造工艺
  error_examples  典型错误实现及其症状（负向测试用；写不出这题的就不该收）
  notes           冻结前必须清空；公共题仅在 I/O 过多时写不适配条款及原因

数值口径：扫描周期 20 ms；错误码 16#8xxx（题库已给出的沿用题库原值）。
"""

COMMON_SCAN = '20 ms（全组统一，见 docs/tasks_note.md）'

PUBLIC = {
    'P01': {
        'category': 'C',
        'zh_summary': '灌装线四步顺序控制：瓶子到位启清洗泵，操作员逐工步确认后依次进入灌装、封盖、包装，最后点亮完成灯等待取瓶。',
        'initial_state': '全部输出 FALSE（Pump_Motor/Filling_Valve/Capping_Machine/Packing_Machine/Completion_Light），工步状态 = 0（等待瓶子），不保留上一瓶的完成标记。',
        'constraints': [
            'K1 四道工序只能按 清洗→灌装→封盖→包装 的顺序推进，前一步的完成确认是后一步启动的必要条件。',
            'K2 同一时刻只允许一个执行器输出为 TRUE（Pump_Motor/Filling_Valve/Capping_Machine/Packing_Machine 两两互斥）。',
            'K3 清洗泵只在 bottleSensor 检测到瓶子且当前工步为 0 时启动；泵运行期间再次检测到瓶子不得重复触发。',
            'K4 finishedButton 有效后回到工步 0，并熄灭 Completion_Light。',
        ],
        'error_examples': [
            '错误实现：用一堆与门直接驱动四个执行器，未记录工步。症状——操作员连按两次 fillingConfirmButton，灌装阀与封盖机同时为 TRUE，瓶子未灌满就被封盖。',
            '错误实现：finishedButton 只清 Completion_Light 不清工步号。症状——下一只瓶子进站时程序仍停在工步 4，清洗泵不启动。',
        ],
        'notes': '',
    },
    'P02': {
        'category': 'B',
        'zh_summary': '双字（DWORD）逐位边沿检测：每周期比较本期与上期值，输出变化位、上升沿位、下降沿位及其个数。',
        'initial_state': '内部 lastValue = 16#00000000；hasChanged/hasRisingEdges/hasFallingEdges = FALSE；risingBits/fallingBits = 16#00000000；noOfRisingBits/noOfFallingBits = 0。',
        'constraints': [
            'K1 每个扫描周期只做一次比较，比较对象是本周期的 value 与上一周期保存的 value。',
            'K2 risingBits 只在 0→1 的位上置 1，fallingBits 只在 1→0 的位上置 1，其余位为 0。',
            'K3 noOfRisingBits 必须等于 risingBits 中 1 的个数，noOfFallingBits 同理。',
            'K4 上电后的第一个周期没有「上一周期」，hasChanged/hasRisingEdges/hasFallingEdges 一律为 FALSE，避免上电误报。',
        ],
        'error_examples': [
            '错误实现：hasChanged 写成 value <> 0。症状——value 恒为非零时每周期都报「有变化」。',
            '错误实现：计数用累加器 noOfRisingBits := noOfRisingBits + 1。症状——连续 10 个周期同一位抖动，计数值远大于实际置位数。',
        ],
        'notes': '',
    },
    'P03': {
        'category': 'D',
        'zh_summary': '带滞回的上下限报警：超过 hiLevel 报警，回落到 hiLevel-hystWindow 才复位；参数非法时给出 16#8001/16#8002 并退出程序。',
        'initial_state': 'hiAlarm = FALSE；loAlarm = FALSE；error = FALSE；status = 16#0000。',
        'constraints': [
            'K1 若 loLevel >= hiLevel，置 error=TRUE、status=16#8001，并立即退出程序（不执行后续报警逻辑）。',
            'K2 若 hystWindow >= (hiLevel - loLevel)，置 error=TRUE、status=16#8002，同样退出程序。',
            'K3 高报：Value > hiLevel 时置位；Value < hiLevel - hystWindow 时复位；两者之间保持原状态。',
            'K4 低报：Value < loLevel 时置位；Value > loLevel + hystWindow 时复位；两者之间保持原状态。',
        ],
        'error_examples': [
            '错误实现：进入与退出用同一个阈值。症状——Value 在 hiLevel 附近抖动时 hiAlarm 每周期翻转，报警灯闪烁。',
            '错误实现：先做报警判断再做参数合法性检查。症状——loLevel >= hiLevel 时仍可能置位 hiAlarm，且 status 被覆盖成 16#0000。',
        ],
        'notes': '',
    },
    'P04': {
        'category': 'D',
        'zh_summary': '酱料输送泵控制：粘度信号去抖、急停优先、运行时间累计与 500 小时维护提示。',
        'initial_state': 'VFD_RUN = FALSE；PUMP_RUNTIME_ACC = T#0s；PUMP_MAINT_DUE = FALSE；去抖计时器清零。',
        'constraints': [
            'K1 PASTE_E_STOP_NC = FALSE 时 VFD_RUN 立即变为 FALSE，并清除未完成的去抖计时。',
            'K2 VISCOSITY_OK 必须连续为 TRUE 达 DebounceTime，粘度条件才算有效；输入一旦变 FALSE 立即作废。',
            'K3 VFD_RUN 为 TRUE 的必要条件是 PASTE_E_STOP_NC = TRUE 且粘度条件有效，二者缺一不可。',
            'K4 仅在 VFD_RUN = TRUE 时按 CycleTime 累加 PUMP_RUNTIME_ACC；泵停期间累计值保持不变。',
            'K5 累计到 500 小时后置 PUMP_MAINT_DUE；该提示只作信息输出，不得反过来影响 VFD_RUN 或安全允许。',
        ],
        'error_examples': [
            '错误实现：把 PUMP_MAINT_DUE 串进 VFD_RUN 的使能条件。症状——累计满 500 小时后泵自动停机，产线断料。',
            '错误实现：急停时只把 VFD_RUN 置 FALSE，未清去抖计时器。症状——急停复位后粘度条件被「立即」认为有效，泵无去抖直接启动。',
        ],
        'notes': '',
    },
    'P05': {
        'category': 'A',
        'zh_summary': '焊缝间隙报警：上电后 5 秒抑制期内不报警，抑制结束后间隙超限需去抖才报警，急停优先于一切。',
        'initial_state': 'Operator_Alert = FALSE；Weld_Soft_Start_Active = TRUE（抑制期开始）；去抖计时器清零。',
        'constraints': [
            'K1 上电后进入 5 s 初始化抑制期，期间 Weld_Soft_Start_Active = TRUE、Operator_Alert = FALSE，且去抖计时不累计。',
            'K2 抑制期结束后恢复监视：Gap_Exceeded 连续为 TRUE 达 DebounceTime 才置 Operator_Alert。',
            'K3 Gap_Exceeded 变 FALSE 时立即复位 Operator_Alert 并清去抖计时。',
            'K4 Weld_E_Stop_NC = FALSE 时急停优先于抑制期与正常监视：Operator_Alert 立即 FALSE，未完成的去抖计时清除。',
        ],
        'error_examples': [
            '错误实现：抑制期内照常累计去抖时间。症状——上电 5 s 一到立即报警，抑制形同虚设。',
            '错误实现：急停只清 Operator_Alert，未清去抖计时。症状——急停松开后间隙信号仍超限时报警瞬间重现。',
        ],
        'notes': '',
    },
    'P06': {
        'category': 'A',
        'zh_summary': '曝气风机延时启动：溶解氧偏低且无急停持续 5 秒才启动，条件消失立即停机并复位计时，按启动次数计数。',
        'initial_state': 'BLOWER_RUN = FALSE；AERATION_BLOWER_CYCLE_COUNT = 0；启动延时计时器清零。',
        'constraints': [
            'K1 延时计时只在 DO_LOW = TRUE 且 AERATION_E_STOP_NC = TRUE 时进行。',
            'K2 上述两个条件同时满足并持续满 5 s 后才允许 BLOWER_RUN = TRUE。',
            'K3 DO_LOW 变 FALSE 或急停发生时，BLOWER_RUN 立即 FALSE、启动计时复位；下次需求须重新计满 5 s。',
            'K4 AERATION_BLOWER_CYCLE_COUNT 只在 BLOWER_RUN 的 FALSE→TRUE 沿加 1，连续运行期间不得重复计数。',
        ],
        'error_examples': [
            '错误实现：用 TON 但条件失效时不复位。症状——DO_LOW 抖动两次后累计「凑够」5 秒，风机提前启动。',
            '错误实现：在 BLOWER_RUN 为 TRUE 的每个周期都加计数。症状——运行 10 分钟计数涨到几万。',
        ],
        'notes': '',
    },
    'P07': {
        'category': 'A',
        'zh_summary': '五泵切换控制：手动模式按选择开关单泵启停，自动模式按优先级选出 3 台运行、2 台备用（三用两备）。',
        'initial_state': '5 台泵输出全 FALSE；pumpGroup[1..5].selection 全 FALSE；自动模式下运行台数目标 = 3。',
        'constraints': [
            'K1 mode 决定工作模式，手动与自动互斥，同一时刻只有一种模式的动作生效。',
            'K2 自动模式下同时运行的泵数恰为 3 台，其余 2 台作为备用。',
            'K3 自动模式下按优先级选出运行泵：优先级高者先启，优先级相同时按泵号升序，保证结果确定。',
            'K4 stop 信号优先于 start：停止请求有效时不得因 start 或自动需求而启动任何泵。',
        ],
        'error_examples': [
            '错误实现：自动模式把所有 selection 为 TRUE 的泵一起启动。症状——5 台泵同时运行，超出「三用两备」的供水策略。',
            '错误实现：优先级比较没有打破平局的规则。症状——两台泵优先级相同，每个周期轮流被选中，输出抖动。',
        ],
        'notes': '',
    },
    'P08': {
        'category': 'B',
        'zh_summary': '模拟量批量转换：按 count 逐通道把原始值换算为工程量，支持非温度线性标定、标准温度与气候温度三种模式。',
        'initial_state': '不保留上次结果：每次调用按当前输入重算 retVal 与 outputValue；count = 0 时不做任何通道。',
        'constraints': [
            'K1 只处理从两个数组各自下界开始的前 count 个通道；count 必须落在 0 到两数组长度较小者之间。',
            'K2 只读 analogValues 与配置字段，仅写 retVal 与 outputValue，不得就地修改输入数组。',
            'K3 measuringMode = 0 时做线性标定：bipolar = FALSE 把 0..27648 映射到 loLIM..hiLIM，bipolar = TRUE 把 -27648..27648 映射到同一区间。',
            'K4 measuringMode = 1 时输出为原始值的 1/10，measuringMode = 2 时输出为原始值的 1/100。',
            'K5 count 越界、通道模式非法或量程非法（hiLIM ≤ loLIM）时，该通道置对应错误码并跳过换算，其余通道继续处理，已处理的通道结果保持有效。',
        ],
        'error_examples': [
            '错误实现：直接在 analogValues 上做原地换算。症状——同一通道在第二个扫描周期被重复换算，工程量越算越小。',
            '错误实现：单双极性判断写反。症状——单极性输入算出负的工程量，输出值整体偏移满量程。',
        ],
        'notes': '',
    },
    'P09': {
        'category': 'B',
        'zh_summary': '滑动平均：按周期或触发沿读入新值并更新窗口平均，窗口长度非法时报 16#8200，reset 清空窗口。',
        'initial_state': '窗口为空：average = 0.0；windowSizeReached = FALSE；error = FALSE；status = 16#0000；写入指针 = 0。',
        'constraints': [
            'K1 cyclicExecution = TRUE 时每个扫描周期读入一个新数据并更新 average。',
            'K2 trigger 的每个上升沿读入一个新数据并更新 average（与周期模式二选一，不重复计数）。',
            'K3 windowSize 不在 1..100 时置 error = TRUE、status = 16#8200，且不更新 average。',
            'K4 reset = TRUE 时清空窗口、把 windowSizeReached 置 FALSE，其优先级高于 cyclicExecution 与 trigger；windowSizeReached 表示窗口已累计满 windowSize 个样本（官方题面未定义该输出，为本组口径），窗口未满时 average 按已累计样本数求平均。',
        ],
        'error_examples': [
            '错误实现：窗口未填满就按 windowSize 做除数。症状——上电前几个周期的 average 明显偏小。',
            '错误实现：windowSize 越界时仍继续累加。症状——报告里 status 是 16#8200，但 average 仍在变化，测试无法判定。',
        ],
        'notes': '',
    },
    'P10': {
        'category': 'B',
        'zh_summary': '温度逻辑控制：低于设定值加热、高于设定值停止，连续加热超 5 秒触发过热保护并需等 3 秒才能解除，传感器越界判故障。',
        'initial_state': 'HeaterOutput = FALSE；OverheatProtection = FALSE；传感器故障标志 = FALSE；加热计时与保护计时清零。',
        'constraints': [
            'K1 TemperatureSensorInput < SetTemperature 时 HeaterOutput = TRUE，> SetTemperature 时 HeaterOutput = FALSE。',
            'K2 加热连续运行超过 5 s 触发 OverheatProtection，并强制 HeaterOutput = FALSE。',
            'K3 过热保护触发后必须保持至少 3 s 才能解除，解除前不得重新加热。',
            'K4 TemperatureSensorInput < 0 或 > 100 判为传感器故障，此时不得继续加热。',
        ],
        'error_examples': [
            '错误实现：过热保护到点自动恢复且无 3 s 保持。症状——加热器在 5 s 边界上高频通断，接触器打火。',
            '错误实现：传感器故障时不封锁加热。症状——断线时读数为 0，程序认为温度过低而持续加热，是最危险的一类缺陷。',
        ],
        'notes': '',
    },
    'P11': {
        'category': 'C',
        'zh_summary': '三工位生产线：手动模式正反转互锁，自动模式按 A→B→C 顺序推进，每站需到位信号与完成按钮，C 站完成后点亮完成灯。',
        'initial_state': 'MotorForward = FALSE；MotorReverse = FALSE；CompletionLight = FALSE；工位状态 = IDLE；当前站 = A。',
        'constraints': [
            'K1 手动模式下 MotorForward 与 MotorReverse 互斥，任一为 TRUE 时另一个必须为 FALSE。',
            'K2 自动模式下产品必须依次经过 A、B、C 三站，不得跳站或回流。',
            'K3 每站推进的条件是「该站到位（SensorX）+ 该站完成按钮（ButtonX）」，缺一不可。',
            'K4 产品在 C 站完成加工后置 CompletionLight = TRUE。',
        ],
        'error_examples': [
            '错误实现：自动模式只看完成按钮不看到位信号。症状——产品未到站就被判加工完成，三站节拍错位。',
            '错误实现：正反转互锁只在手动模式下做。症状——模式切换瞬间两个接触器同时吸合。',
        ],
        'notes': '',
    },
    'P12': {
        'category': 'D',
        'zh_summary': '板坯厚度故障：信号有效时判故障、报警至少保持 500 ms、故障上升沿计数并保留最近 5 条历史，正常运行时间按周期累计。',
        'initial_state': 'THICKNESS_ALARM = FALSE；Slab_Fault_Counter = 0；Slab_Runtime_Accumulator = T#0s；Slab_Fault_History[0..4] 全为 0；保持计时器清零。',
        'constraints': [
            'K1 只在 THICKNESS_SIGNAL_VALID = TRUE 时判定 THICKNESS_FAULT，信号无效期间不报警、不计数、不累计运行时间。',
            'K2 故障上升沿时 Slab_Fault_Counter 加 1，并把 FaultTimestamp 写入历史元素 0，原有记录向高索引移位，只保留最近 5 条。',
            'K3 THICKNESS_ALARM 一旦置位至少保持 500 ms；故障持续期间保持为 TRUE。',
            'K4 仅当 CUTTING_RUN = TRUE、信号有效且无厚度故障时，按 CycleTime 累加 Slab_Runtime_Accumulator；否则保持不变。',
        ],
        'error_examples': [
            '错误实现：信号无效时仍把故障信号当有效处理。症状——传感器掉线一次就在历史里记一条假故障。',
            '错误实现：历史数组从索引 0 往后顺序写。症状——第 6 次故障覆盖掉第 1 条，最近 5 条变成最早 5 条。',
        ],
        'notes': '',
    },
    'P13': {
        'category': 'B',
        'zh_summary': '办公楼 HVAC 节能控制：按占用与模式（自动/舒适/经济/夜间）决定送风机启停与温度设定值修正，风机启动需 30 秒延时。',
        'initial_state': 'SUPPLY_FAN_RUN = FALSE；TEMP_SETPOINT_ADJUST = 0；启动延时计时器清零。',
        'constraints': [
            'K1 只有「检测到占用且未选夜间模式」时才开始 30 s 启动延时；条件保持满 30 s 后 SUPPLY_FAN_RUN 才为 TRUE。',
            'K2 占用丢失或切到夜间模式时立即停风机并复位延时；条件恢复后必须重新计满 30 s。',
            'K3 温度修正按模式取值：自动 0/+3（节能）/+2（标准）、舒适 0/+1、经济 0/+4、夜间恒 +4；节能开关只影响自动模式。',
            'K4 TEMP_SETPOINT_ADJUST 必须限制在 ±4 °C 之内。',
        ],
        'error_examples': [
            '错误实现：夜间模式仍按占用情况取修正值。症状——夜间有人加班时设定值不升高，节能策略失效。',
            '错误实现：延时用 TON 但占用丢失时未复位。症状——人来了又走再回来，风机比预定时间早启动。',
        ],
        'notes': '',
    },
    'P14': {
        'category': 'B',
        'zh_summary': 'IPv4 点分十进制解析：校验四段、纯数字与 0—255 范围，按网络字节序组装为 32 位无符号整数，非法输入输出 0。',
        'initial_state': 'ipValue = 0；解析状态机处于等待第 1 段。',
        'constraints': [
            'K1 输入必须是四段、段间以点分隔、每段非空且全部为十进制数字。',
            'K2 每段数值必须在 0—255 之间（含端点）。',
            'K3 按网络字节序组装：第 1 段占最高 8 位，第 4 段占最低 8 位。',
            'K4 段数不对、含非数字字符、任一段越界时一律输出 ipValue = 0；本接口没有状态输出，合法地址 0.0.0.0 与非法输入的输出值相同，用例不据此判错。',
        ],
        'error_examples': [
            '错误实现：允许空段（如 192.168..1）。症状——空段被当 0，非法地址被解析成合法值。',
            '错误实现：按小端组装。症状——10.0.0.1 解析成 16#0100000A，与网络字节序相反。',
        ],
        'notes': '',
    },
    'P15': {
        'category': 'C',
        'zh_summary': '物料配比控制：手动模式按按钮边沿切换各阀门与搅拌电机，自动模式按工艺顺序配料，急停时立即停全部设备。',
        'initial_state': 'valveARun/BRun/CRun/DRun、mixMotorRun 全为 FALSE；急停信号 estop = TRUE（正常态）；模式由 opeMode 决定，上电按手动处理。',
        'constraints': [
            'K1 estop = FALSE 时立即停止全部设备（四个阀门与搅拌电机输出全为 FALSE），其优先级高于手动与自动模式。',
            'K2 手动模式下各启动按钮按上升沿切换对应设备（按一次启动，再按一次停止），不得按电平持续翻转。',
            'K3 自动模式按工艺顺序执行：先按配比开启 A/B/C 阀门，达到设定后停阀并启动搅拌，搅拌完成后开 D 阀出料。',
            'K4 急停期间所有自动步序被冻结；急停恢复后从安全步重新开始，不得从中断处直接续跑。',
        ],
        'error_examples': [
            '错误实现：急停只停搅拌电机不停阀门。症状——急停后物料继续流入，配比罐溢出。',
            '错误实现：按钮用电平而不是上升沿。症状——按住按钮期间阀门每周期翻转，接触器反复吸合。',
        ],
        'notes': '',
    },
    'P16': {
        'category': 'C',
        'zh_summary': '柔性加工线：按工艺序列 processSequence 把工件依次送到指定工位加工，5 个工位、输送机左右互斥。',
        'initial_state': 'conveyorLeft = FALSE；conveyorRight = FALSE；工步索引 = 0；各工位空闲。',
        'constraints': [
            'K1 每件工件的前 processLength 个工位号来自 processSequence，按数组顺序依次加工，不得跳过或乱序。',
            'K2 conveyorLeft 与 conveyorRight 互斥，任何时刻不得同时为 TRUE。',
            'K3 只有目标工位的到位传感器为 TRUE 且该工位加工完成信号有效时，才允许启动下一段输送。',
            'K4 processLength 超出数组范围或工位号不在 1—5 时置错误状态并停止输送。',
        ],
        'error_examples': [
            '错误实现：忽略 processLength，把 8 个元素全部执行。症状——数组尾部残留的 0 被当作工位号，输送机空转到不存在的工位。',
            '错误实现：左右输送不互斥。症状——切换瞬间两个方向同时输出，机械卡死。',
        ],
        'notes': '',
    },
    'P17': {
        'category': 'C',
        'zh_summary': '配方管理：配方库最多 10 条（编号 0 表示空位），支持增删改查；新增时编号重复报 16#8002、无空位报 16#8003，查询/删除/修改时编号不存在分别报 16#8001 / 16#8004 / 16#8005。',
        'initial_state': '配方库 ARRAY[1..10] OF ST_Recipe 全部 recipeID = 0（空）；error = FALSE；status = 16#0000。',
        'constraints': [
            'K1 配方库容量 10 条，recipeID = 0 表示空位；写入时只能落到空位。',
            'K2 新增时若库中已存在相同 recipeID，拒绝写入并置 status = 16#8002（编号重复）。',
            'K3 查询、删除、修改时若 recipeID 不存在，分别置 status = 16#8001 / 16#8004 / 16#8005（配方不存在），库内容保持不变。',
            'K4 新增时若库已满（无 recipeID = 0 的空位），置 status = 16#8003（无空位）。',
        ],
        'error_examples': [
            '错误实现：新增时不查重。症状——同一个编号出现两条记录，查询永远返回先写的那条。',
            '错误实现：查询失败时把上一次的结果留在 recipeQueryResult 里。症状——上位机读到过期配方并据此投料。',
        ],
        'notes': '',
    },
    'P18': {
        'category': 'B',
        'zh_summary': 'FIFO 环形队列：入队/出队按上升沿各触发一次，reset 优先清空，空队出队或满队入队被拒绝并给出状态码。',
        'initial_state': '队列为空：head = tail = 0；elementCount = 0；status = 16#0000；首次调用视为空队列。',
        'constraints': [
            'K1 reset = TRUE 时清空队列并把 elementCount 置 0，其优先级高于同一周期的入队与出队请求。',
            'K2 enqueue 的每个上升沿在队列未满时把 item 追加到队尾；dequeue 的每个上升沿在队列非空时取出队首并写回 item。',
            'K3 队列满时入队被拒绝、队列空时出队被拒绝，队列内容与 item 均保持不变，并通过 status 报告原因。',
            'K4 elementCount 必须等于当前有效元素数：0 表示空，等于缓冲区长度表示满。',
        ],
        'error_examples': [
            '错误实现：满队时仍写入并前移尾指针。症状——队首元素被悄悄覆盖，出队顺序错乱。',
            '错误实现：reset 只清 elementCount 不清 head/tail。症状——复位后第一次入队写到了旧位置，读出的元素是上一次的残留值。',
        ],
        'notes': 'item/buffer 在官方接口里声明为 VARIANT；本机 CODESYS 3.5.22.40 不识别该类型、无法直接编译，实验时按 INT 等价实例化（item: INT、buffer: ARRAY[*] OF INT），语义与判据不变。',
    },
    'P19': {
        'category': 'C',
        'zh_summary': '机械臂六动作四模式控制：手动逐动作按限位停、单步逐步确认、单周期走一遍、连续循环，急停停止一切动作。',
        'initial_state': '初始位置在左上：UpLimitSwitch = TRUE、LeftLimitSwitch = TRUE；六路动作输出全为 FALSE；模式为手动。',
        'constraints': [
            'K1 手动模式下只有「按下了该方向按钮且尚未到达该方向限位」时才输出该动作；松开按钮或到达限位立即停止该动作。',
            'K2 四种模式（Manual/SingleStep/SingleCycle/Continuous）互斥，同一时刻只有一种模式的动作生效。',
            'K3 单步模式每完成一个动作必须等待操作员确认后才执行下一个动作。',
            'K4 EmergencyStop = FALSE（急停触发）时六路动作输出全部为 FALSE，且不允许任何模式继续推进；EmergencyStop = TRUE 表示无急停、可正常运行。',
            'K5 抓取/释放动作必须以 GripLimitSwitch/ReleaseLimitSwitch 为到位判据，到位后不得持续输出。',
        ],
        'error_examples': [
            '错误实现：手动模式到位后不停止。症状——机械臂顶住下限位继续输出 MoveDown，电机堵转。',
            '错误实现：模式判断用 if/elsif 但缺少互斥。症状——同时按下两个模式按钮时两种模式的动作叠加。',
        ],
        'notes': '24 个 I/O，按课程要求只取 6 条最高价值规约（见 data/specs/P19.ltl）；K2/K5 与 C4/C9 的不适配说明见 data/specs/PROPOSITIONS.md。',
    },
    'P20': {
        'category': 'C',
        'zh_summary': '五工位生产线：手动正反转互斥，自动按上料→清洗→称重→烧成→成品顺序推进，各工位完成信号触发推进，成品站执行 kick 动作。',
        'initial_state': 'MotorForward = FALSE；MotorReverse = FALSE；kick = FALSE；CompletionLight = FALSE；工位状态 = IDLE。',
        'constraints': [
            'K1 手动模式下 MotorForward 与 MotorReverse 互斥。',
            'K2 自动模式下产品依次经过上料、清洗、称重、烧成、成品 5 个工位，不得跳站。',
            'K3 每个工位的完成信号（washComplete/weightComplete/firingComplete）是推进的必要条件，且必须与对应到位传感器一致。',
            'K4 成品站完成出料动作（kick）后点亮 CompletionLight。',
        ],
        'error_examples': [
            '错误实现：只看完成信号不看到位传感器。症状——产品还在清洗站，称重完成信号一到就推进。',
            '错误实现：kick 与输送电机同时输出。症状——出料瞬间产品被推回输送线，卡在成品站入口。',
        ],
        'notes': '17 个 I/O，按课程要求只取 6 条最高价值规约（见 data/specs/P20.ltl）。',
    },
}

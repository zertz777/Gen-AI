# -*- coding: utf-8 -*-
"""curation_self.py -- 12 道自编题的完整内容（S01—S12）

自编题不是凭空造，而是「在真实场景里找一道能判对错的题」。四类场景
（A 开关量联锁 / B 模拟量处理 / C 状态机与节拍 / D 故障与安全）各 3 道，
难度 3 易 / 5 中 / 4 难。

每题都先写 error_examples（什么样的实现算错），再反推 constraints 与
LTL 规约——写不出错误示例的题，说明它本身就判不了对错，应当换掉。

字段口径与公共题完全一致（见 docs/tasks_note.md），变量名统一用英文
大驼峰或题目惯用的下划线风格，全程不翻译、不改大小写。
"""

SELF = {}

SELF['S01'] = {
    'title': '双工位气动夹具互锁',
    'difficulty': 'easy',
    'category': 'A',
    'zh_summary': '两个工位共用一路气源，同一时刻只允许一个夹具夹紧；无零件不允许夹紧，急停立即松开两侧。',
    'requirement': """双工位气动夹具用于同时定位两个零件，但气源只有一路，因此两个夹具不能同时动作。

控制要求：
1. StartBtn 为上升沿触发：若左工位有零件（LeftPartPresent = TRUE）而右夹具未在夹紧，则左夹具 ClampLeft 夹紧；右侧对称。
2. 夹紧动作只做一次保持，不随 StartBtn 电平反复动作；要松开必须由同一按钮在另一工位动作时自动让位（即后启动的工位会等待）。
3. 任一工位没有零件（对应 PartPresent = FALSE）时，该侧不允许夹紧。
4. EStop_NC = FALSE（急停）时两侧夹具立即松开，ClampLeft 与 ClampRight 同时为 FALSE，并清空忙标志。
5. 任一时刻 ClampLeft 与 ClampRight 不得同时为 TRUE。
6. Busy 表示当前已有工位在夹紧过程中；Status 输出 16#0000 正常、16#8101 两侧同时请求、16#8102 急停中。""",
    'io_table': [
        ('IN', 'StartBtn', 'BOOL', '启动按钮（上升沿有效）'),
        ('IN', 'LeftPartPresent', 'BOOL', '左工位零件到位'),
        ('IN', 'RightPartPresent', 'BOOL', '右工位零件到位'),
        ('IN', 'EStop_NC', 'BOOL', '急停常闭触点，TRUE = 正常'),
        ('OUT', 'ClampLeft', 'BOOL', '左夹具夹紧输出'),
        ('OUT', 'ClampRight', 'BOOL', '右夹具夹紧输出'),
        ('OUT', 'Busy', 'BOOL', '有工位正在夹紧'),
        ('OUT', 'Status', 'WORD', '状态码'),
    ],
    'initial_state': 'ClampLeft = FALSE；ClampRight = FALSE；Busy = FALSE；Status = 16#0000；内部上升沿寄存器 StartBtnLast = FALSE。',
    'constraints': [
        'K1 ClampLeft 与 ClampRight 不得同时为 TRUE（互斥）。',
        'K2 只有在对应工位零件到位且急停正常时，才允许该侧夹紧。',
        'K3 夹紧由 StartBtn 上升沿触发一次，按住不放不得重复触发。',
        'K4 EStop_NC = FALSE 时两侧输出立即清零，忙标志清除。',
    ],
    'error_examples': [
        '错误实现：ClampLeft := StartBtn AND LeftPartPresent；ClampRight := StartBtn AND RightPartPresent。症状——两侧同时夹紧，气源压力跌落，两个夹具都夹不到底。',
        '错误实现：用 StartBtn 的电平而不是上升沿。症状——按住按钮期间夹具每周期翻转，气缸发出连续的排气声。',
    ],
    'source_type': '改编自公开题',
    'source_ref': 'P05 Weld Gap Alarm and Startup Inhibition（课程题库）',
    'adaptation_what': '把「间隙超限才允许报警」的启动抑制结构，改造成「两工位互斥夹紧」；去掉焊缝工艺，改为通用气动工位。',
    'adaptation_why': '原始结构证明了「多个使能条件必须同时成立」的写法，而夹具互斥是 PLC 现场最常见的安全约束，适合作为最简变体。',
    'notes': '',
}

SELF['S02'] = {
    'title': '输送线正反转与检修锁',
    'difficulty': 'easy',
    'category': 'A',
    'zh_summary': '输送电机正反转互斥，换向必须经过 200 ms 死区；检修钥匙插入时禁止一切启动。',
    'requirement': """输送线由一台可正反转的电机驱动，用于把工件送进和送出工位。

控制要求：
1. FwdBtn 有效且无反转输出时，MotorFwd = TRUE；RevBtn 有效且无正转输出时，MotorRev = TRUE。
2. 正转切换到反转（或反之）时，必须先关断当前方向，等待 200 ms 死区后才能启动另一方向。
3. MaintKey = TRUE（检修钥匙插入）时，MotorFwd 与 MotorRev 均不得为 TRUE；RunLamp 以 1 Hz 闪烁提示检修态。
4. EStop_NC = FALSE 时立即停止两个方向，并清空死区计时。
5. 任何时刻 MotorFwd 与 MotorRev 不得同时为 TRUE。
6. Status：16#0000 正常、16#8201 检修锁定、16#8202 急停、16#8203 换向死区中。""",
    'io_table': [
        ('IN', 'FwdBtn', 'BOOL', '正转按钮'),
        ('IN', 'RevBtn', 'BOOL', '反转按钮'),
        ('IN', 'MaintKey', 'BOOL', '检修钥匙，TRUE = 检修态'),
        ('IN', 'EStop_NC', 'BOOL', '急停常闭触点，TRUE = 正常'),
        ('OUT', 'MotorFwd', 'BOOL', '电机正转'),
        ('OUT', 'MotorRev', 'BOOL', '电机反转'),
        ('OUT', 'RunLamp', 'BOOL', '运行指示灯（检修态闪烁）'),
        ('OUT', 'Status', 'WORD', '状态码'),
    ],
    'initial_state': 'MotorFwd = FALSE；MotorRev = FALSE；RunLamp = FALSE；Status = 16#0000；死区计时器 = 0。',
    'constraints': [
        'K1 MotorFwd 与 MotorRev 不得同时为 TRUE。',
        'K2 换向必须先两侧全 FALSE 并经过 200 ms 死区，才允许另一方向启动。',
        'K3 MaintKey = TRUE 时两个方向输出恒为 FALSE。',
        'K4 EStop_NC = FALSE 时立即停机并清死区计时。',
    ],
    'error_examples': [
        '错误实现：MotorFwd := FwdBtn AND NOT MotorRev；MotorRev := RevBtn AND NOT MotorFwd。症状——两个按钮同时按下时互锁互相否决，电机反复启停。',
        '错误实现：换向时直接反接（无死区）。症状——接触器在换向瞬间同时拉弧，机械传动受冲击。',
    ],
    'source_type': '自拟',
    'source_ref': '参照 P11 Automated Production Line Control 的手动正反转段落',
    'adaptation_what': '把 P11 的手动模式单独抽出成一道题，加入换向死区与检修钥匙两个真实约束。',
    'adaptation_why': '原题的手动部分只要求互锁，未涉及换向死区与检修态，这两条是现场调试中最容易漏写的安全逻辑。',
    'notes': '',
}

SELF['S03'] = {
    'title': '安全门分级停机',
    'difficulty': 'medium',
    'category': 'A',
    'zh_summary': '安全门打开时 A 区立停、B 区延时 500 ms 停机，复位后方可重启；急停优先于分级停机。',
    'requirement': """设备分 A、B 两个危险区，安全门打开时需要分级停机：A 区（靠近门）立即停，B 区（远端）允许走完当前动作再停。

控制要求：
1. DoorSwitch = TRUE（门打开）时，DriveA_Run 立即变为 FALSE；DriveB_Run 继续保持，直到 500 ms 延时到或 B 区动作完成。
2. 门关闭（DoorSwitch = FALSE）后，必须由 ResetBtn 的上升沿确认，才允许重新启动两个区。
3. EStop_NC = FALSE 时 A、B 两区同时立即停止，不受 500 ms 延时影响。
4. 门打开或急停期间 AlarmLamp = TRUE。
5. 未复位前按启动按钮无效（Status 保持 16#8301 待复位）。
6. Status：16#0000 正常、16#8301 待复位、16#8302 门开、16#8303 急停。""",
    'io_table': [
        ('IN', 'DoorSwitch', 'BOOL', '安全门，TRUE = 门开'),
        ('IN', 'ZoneAOccupied', 'BOOL', 'A 区内有人'),
        ('IN', 'ZoneBOccupied', 'BOOL', 'B 区内有人'),
        ('IN', 'ResetBtn', 'BOOL', '复位按钮（上升沿有效）'),
        ('IN', 'EStop_NC', 'BOOL', '急停常闭触点，TRUE = 正常'),
        ('OUT', 'DriveA_Run', 'BOOL', 'A 区驱动运行'),
        ('OUT', 'DriveB_Run', 'BOOL', 'B 区驱动运行'),
        ('OUT', 'AlarmLamp', 'BOOL', '报警灯'),
        ('OUT', 'Status', 'WORD', '状态码'),
    ],
    'initial_state': 'DriveA_Run = FALSE；DriveB_Run = FALSE；AlarmLamp = FALSE；Status = 16#0000；延时计时器 = 0；已复位标志 = TRUE。',
    'constraints': [
        'K1 DoorSwitch 由 FALSE 变 TRUE 时，DriveA_Run 必须在同一周期内变为 FALSE。',
        'K2 DriveB_Run 在门开后最多再保持 500 ms（或提前因动作完成而停）。',
        'K3 门关闭后必须经过 ResetBtn 上升沿，两个区才允许重新启动。',
        'K4 EStop_NC = FALSE 时两个区都立即停止，且优先于 500 ms 延时。',
    ],
    'error_examples': [
        '错误实现：两个区都用同一个 500 ms 延时。症状——A 区在门开后 500 ms 才停，靠近门的人员已经进入危险区。',
        '错误实现：门关闭后自动恢复运行，不需要复位。症状——操作员还在门内，设备自行启动。',
    ],
    'source_type': '自拟',
    'source_ref': '课程作业说明 §示例（电机启停：P1 停止安全性、P2 正常启动）的分级停机思路',
    'source_link': '课程作业说明 PDF（平台下发）',
    'adaptation_what': '把单机停止安全性扩展为两区分级停机，加入「门关 + 复位」的两步重启条件。',
    'adaptation_why': '分级停机是安全等级（PL）降级的典型做法，比一刀切停机更贴近真实产线；复位条件则对应 ISO 13849 的复位要求。',
    'notes': '',
}

SELF['S04'] = {
    'title': '称重零点漂移补偿',
    'difficulty': 'medium',
    'category': 'B',
    'zh_summary': '按按钮采样空秤值作为零点，输出补偿后的重量；漂移超限报警，上电零点为 0。',
    'requirement': """称重传感器长时间运行会出现零点漂移，需要在空秤时重新标定零点。

控制要求：
1. ZeroBtn 的上升沿把当前 RawWeight 采样为零点 ZeroOffset，同时清 DriftAlarm。
2. CompensatedWeight = (RawWeight - ZeroOffset) * 0.01（单位 kg，0.01 为标定系数），每个扫描周期更新。
3. 当 (RawWeight - ZeroOffset) 的绝对值超过 200（即 2 kg）时置 DriftAlarm = TRUE；回到 ±150 以内才复位（滞回）。
4. 上电时 ZeroOffset = 0，DriftAlarm = FALSE。
5. Status：16#0000 正常、16#8401 零点漂移、16#8402 采样值超量程（RawWeight 超出 -32768..32767 的可用段）。""",
    'io_table': [
        ('IN', 'RawWeight', 'INT', '称重传感器原始值'),
        ('IN', 'ZeroBtn', 'BOOL', '零点标定按钮（上升沿有效）'),
        ('IN', 'CalibWeight', 'REAL', '标准砝码重量（kg），仅作显示'),
        ('OUT', 'CompensatedWeight', 'REAL', '补偿后的重量（kg）'),
        ('OUT', 'ZeroOffset', 'INT', '当前零点原始值'),
        ('OUT', 'DriftAlarm', 'BOOL', '零点漂移报警'),
        ('OUT', 'Status', 'WORD', '状态码'),
    ],
    'initial_state': 'ZeroOffset = 0；CompensatedWeight = 0.0；DriftAlarm = FALSE；Status = 16#0000；ZeroBtnLast = FALSE。',
    'constraints': [
        'K1 ZeroOffset 只在 ZeroBtn 上升沿更新，按住或松开时保持不变。',
        'K2 CompensatedWeight 每周期按 (RawWeight - ZeroOffset) * 0.01 计算，不使用上一周期的结果。',
        'K3 漂移判据带 50 单位滞回：超过 ±200 置位，回到 ±150 内复位。',
        'K4 上电后未标定前 ZeroOffset 必须为 0，不得沿用断电前的值。',
    ],
    'error_examples': [
        '错误实现：ZeroOffset 在 ZeroBtn 为 TRUE 的每个周期都采样。症状——操作员按住按钮时，秤上已放砝码，零点被标成砝码重量。',
        '错误实现：没有滞回。症状——RawWeight 在 200 边界抖动时 DriftAlarm 每周期翻转。',
    ],
    'source_type': '改编自公开题',
    'source_ref': 'P08 Analog Batch Processing（课程题库）',
    'adaptation_what': '借用其「原始值 → 工程量」的线性换算，加入零点标定与漂移报警，去掉多通道批量处理。',
    'adaptation_why': '单通道的标定问题更接近现场调试场景，且能把「边沿触发 + 滞回」两种时序约束同时考出来。',
    'notes': '',
}

SELF['S05'] = {
    'title': '泵站流量累计与班次清零',
    'difficulty': 'hard',
    'category': 'B',
    'zh_summary': '按脉冲累计流量，班次清零只清班次量不清总量；累计溢出时置标志并保持最大值。',
    'requirement': """泵站出口装有脉冲流量计，每个脉冲代表 0.5 L。需要同时维护累计总量与当班流量。

控制要求：
1. FlowPulse 的每个上升沿使 PulseCount 加 1，TotalVolume 与 ShiftVolume 各加 0.5 L。
2. ShiftReset 的上升沿把 ShiftVolume 清 0、PulseCount 清 0，但 TotalVolume 必须保持不变。
3. TotalVolume 达到 1000000.0 L 时不再增加，置 OverflowFlag = TRUE；清零只能由维护流程完成（本题不提供入口，仅置位）。
4. FlowPulse 为高频脉冲，同一扫描周期内最多计一个脉冲（20 ms 周期内不允许丢脉冲的假设不成立时，以 Status 报 16#8501）。
5. 上电时 PulseCount = 0、TotalVolume = 0.0、ShiftVolume = 0.0、OverflowFlag = FALSE。
6. Status：16#0000 正常、16#8501 脉冲过快、16#8502 总量溢出。""",
    'io_table': [
        ('IN', 'FlowPulse', 'BOOL', '流量计脉冲'),
        ('IN', 'ShiftReset', 'BOOL', '班次清零（上升沿有效）'),
        ('IN', 'CycleTime', 'TIME', '扫描周期，用于判断脉冲频率'),
        ('OUT', 'TotalVolume', 'LREAL', '累计总量（L）'),
        ('OUT', 'ShiftVolume', 'LREAL', '当班流量（L）'),
        ('OUT', 'PulseCount', 'UDINT', '当班脉冲数'),
        ('OUT', 'OverflowFlag', 'BOOL', '总量溢出标志'),
        ('OUT', 'Status', 'WORD', '状态码'),
    ],
    'initial_state': 'PulseCount = 0；TotalVolume = 0.0；ShiftVolume = 0.0；OverflowFlag = FALSE；Status = 16#0000；FlowPulseLast = FALSE；ShiftResetLast = FALSE。',
    'constraints': [
        'K1 只在 FlowPulse 的上升沿累加，不得按电平累加。',
        'K2 ShiftReset 上升沿清 ShiftVolume 与 PulseCount，TotalVolume 严格不减。',
        'K3 TotalVolume 达到 1000000.0 后保持不再增长，并置 OverflowFlag。',
        'K4 单个扫描周期内检测到两次以上脉冲上升沿时置 Status = 16#8501，本周期只计 1 个。',
    ],
    'error_examples': [
        '错误实现：班次清零时把 TotalVolume 也清 0。症状——交接班后累计总量归零，无法用于结算与能耗分析。',
        '错误实现：TotalVolume 溢出后回绕（LREAL 不会回绕，但用 UDINT 计数会）。症状——总量从 999999.5 跳到 0.0，报表出现负流量。',
    ],
    'source_type': '改编自公开题',
    'source_ref': 'P04 Jam Pump Debouncing and Runtime Maintenance（课程题库）',
    'adaptation_what': '把「运行时间累加 + 500 h 维护提示」换成「脉冲流量累计 + 班次清零」，保留累计量与提示量的分离结构。',
    'adaptation_why': '累计类逻辑（单调、清零范围、溢出）是模拟量题型里最容易写出边界缺陷的一类，且能直接对应 C8 计数单调条款。',
    'notes': '',
}

SELF['S06'] = {
    'title': '烘箱分段升温与超温降载',
    'difficulty': 'medium',
    'category': 'B',
    'zh_summary': '三段升温带 ±5 ℃ 死区，超温 10 ℃ 降载、回到设定值以下 3 ℃ 才恢复，风机与加热联锁。',
    'requirement': """烘箱按三段升温曲线工作，超温时必须先降载而不是直接断电。

控制要求：
1. Segment 取值 0/1/2，分别对应目标温度 SetTemp 的 50%/80%/100%；段号非法时按 0 段处理并置 Status = 16#8601。
2. 当前温度 TempPV 低于目标值 -5 ℃ 时 HeatOn = TRUE，高于目标值 +5 ℃ 时 HeatOn = FALSE，两者之间保持（死区）。
3. TempPV 超过目标值 +10 ℃ 时置 OverTempAlarm = TRUE 并置 LoadReduce = TRUE；TempPV 回落到目标值 -3 ℃ 以下才撤销 LoadReduce。
4. HeatOn = TRUE 期间 FanOn 必须为 TRUE（先开风机后加热，禁止干烧）。
5. Status：16#0000 正常、16#8601 段号非法、16#8602 超温降载。""",
    'io_table': [
        ('IN', 'TempPV', 'REAL', '当前温度（℃）'),
        ('IN', 'SetTemp', 'REAL', '本段目标温度（℃）'),
        ('IN', 'Segment', 'INT', '升温段号 0—2'),
        ('IN', 'LoadReduceReq', 'BOOL', '上位机请求降载'),
        ('OUT', 'HeatOn', 'BOOL', '加热输出'),
        ('OUT', 'FanOn', 'BOOL', '风机输出'),
        ('OUT', 'OverTempAlarm', 'BOOL', '超温报警'),
        ('OUT', 'LoadReduce', 'BOOL', '降载输出'),
        ('OUT', 'Status', 'WORD', '状态码'),
    ],
    'initial_state': 'HeatOn = FALSE；FanOn = FALSE；OverTempAlarm = FALSE；LoadReduce = FALSE；Status = 16#0000。',
    'constraints': [
        'K1 目标温度 = SetTemp × (0.5 / 0.8 / 1.0)，随 Segment 切换。',
        'K2 加热判据带 ±5 ℃ 死区，避免在目标值附近高频通断。',
        'K3 超温 +10 ℃ 置降载，回落 -3 ℃ 才撤销（迟滞不小于 13 ℃）。',
        'K4 HeatOn 为 TRUE 时 FanOn 必须为 TRUE（联锁）。',
    ],
    'error_examples': [
        '错误实现：无死区，TempPV < 目标值就加热。症状——加热器在目标值附近以扫描周期频率通断，接触器寿命骤降。',
        '错误实现：超温时直接断加热、不断风机。症状——加热器余热无法带走，箱内温度继续上升。',
    ],
    'source_type': '改编自公开题',
    'source_ref': 'P10 Temperature Logic Control（课程题库）',
    'adaptation_what': '把单段设定值改为三段升温曲线，把「过热保护」改为「降载 + 迟滞恢复」，并补上风机联锁。',
    'adaptation_why': '原题只考一个设定值比较，工艺性偏弱；分段升温与降载更接近热处理现场，且能同时考死区与联锁两条规约。',
    'notes': '',
}

SELF['S07'] = {
    'title': '灌装四工位节拍控制',
    'difficulty': 'hard',
    'category': 'C',
    'zh_summary': '四工位按节拍顺序推进，每步 5 s 超时报警并停在当前步，完成一瓶计数一次。',
    'requirement': """灌装线由进瓶、灌装、封盖、包装四个工位组成，按固定节拍顺序推进。

控制要求：
1. StartBtn 上升沿启动整线，Conveyor = TRUE 进入进瓶工位；EStop_NC = FALSE 时立即停止全部输出并回到 Step 0。
2. 工步顺序：0 进瓶（等 BottleIn）→ 1 灌装（FillValve 开，等 FillDone）→ 2 封盖（CapMotor 开，等 CapDone）→ 3 包装（PackCyl 开，等 PackDone）→ 回到 0。
3. 每一步自进入起计时，超过 5 s 未收到完成信号则置 Status = 16#8701、保持当前步不动、关闭该步输出（等待人工处理）。
4. 每完成一瓶（PackDone 且回到 Step 0）CycleCount 加 1。
5. 同一时刻四个执行器输出中最多一个为 TRUE。
6. Status：16#0000 正常、16#8701 工步超时、16#8702 急停。""",
    'io_table': [
        ('IN', 'BottleIn', 'BOOL', '进瓶到位'),
        ('IN', 'FillDone', 'BOOL', '灌装完成'),
        ('IN', 'CapDone', 'BOOL', '封盖完成'),
        ('IN', 'PackDone', 'BOOL', '包装完成'),
        ('IN', 'StartBtn', 'BOOL', '启动按钮（上升沿有效）'),
        ('IN', 'EStop_NC', 'BOOL', '急停常闭触点，TRUE = 正常'),
        ('OUT', 'Conveyor', 'BOOL', '输送电机'),
        ('OUT', 'FillValve', 'BOOL', '灌装阀'),
        ('OUT', 'CapMotor', 'BOOL', '封盖电机'),
        ('OUT', 'PackCyl', 'BOOL', '包装气缸'),
        ('OUT', 'CycleCount', 'UINT', '完成瓶数'),
        ('OUT', 'Status', 'WORD', '状态码'),
    ],
    'initial_state': '四个执行器输出全 FALSE；CycleCount = 0；Step = 0；Status = 16#0000；步计时器 = 0；StartBtnLast = FALSE。',
    'constraints': [
        'K1 工步只能按 0→1→2→3→0 推进，不得跳步或回退（除急停复位）。',
        'K2 每一步必须在收到对应完成信号后才推进到下一步。',
        'K3 单步超过 5 s 未完成时置 16#8701、关闭该步输出、保持步号不变。',
        'K4 Conveyor/FillValve/CapMotor/PackCyl 同一时刻最多一个为 TRUE。',
        'K5 EStop_NC = FALSE 时全部输出 FALSE、Step 归 0、立即返回。',
    ],
    'error_examples': [
        '错误实现：用延时替代完成信号推进。症状——瓶子没到位就开灌装阀，物料喷到输送带上。',
        '错误实现：超时后自动跳到下一步。症状——未灌满的瓶子进入封盖，缺陷被下游工位掩盖。',
    ],
    'source_type': '改编自公开题',
    'source_ref': 'P01 Automated Filling Line Control（课程题库）',
    'adaptation_what': '把「操作员逐工步按确认按钮」改为「传感器完成信号」，并补上 5 s 工步超时与瓶数计数。',
    'adaptation_why': '人工确认版本无法自动化评测；换成传感器信号后每一步都有客观判据，且超时处理是节拍控制的核心缺陷来源。',
    'notes': '',
}

SELF['S08'] = {
    'title': '分拣线配方切换',
    'difficulty': 'hard',
    'category': 'C',
    'zh_summary': '三组按高度分拣的配方，切换需在无料时请求并确认，切换期间禁止分拣，非法配方保持原配方。',
    'requirement': """分拣线按产品高度分到左右两条支线，阈值来自配方。切换配方必须在线上无料时进行。

控制要求：
1. RecipeSelect 为 1—3 时对应三组配方：1 = 左 30 mm / 右 60 mm；2 = 左 50 mm / 右 90 mm；3 = 左 70 mm / 右 120 mm（阈值为分界高度）。
2. ChangeoverReq 上升沿时，若 Busy = FALSE 且当前无料（PartHeight = 0.0），则 ActiveRecipe 切换为 RecipeSelect，Busy 置 TRUE 并保持 2 s 后自动清除。
3. Busy = TRUE 期间 SortLeft 与 SortRight 必须都为 FALSE。
4. RecipeSelect 不在 1—3 时拒绝切换，ActiveRecipe 保持不变，Status = 16#8801。
5. 正常分拣：PartHeight 小于左阈值时 SortLeft = TRUE；大于等于左阈值且小于右阈值时 SortRight = TRUE；超过右阈值时不动作并置 Status = 16#8802（超规格）。
6. 上电时 ActiveRecipe = 1，Busy = FALSE。""",
    'io_table': [
        ('IN', 'RecipeSelect', 'INT', '请求的配方号 1—3'),
        ('IN', 'ChangeoverReq', 'BOOL', '切换请求（上升沿有效）'),
        ('IN', 'PartHeight', 'REAL', '当前产品高度（mm），0 表示无料'),
        ('IN', 'EStop_NC', 'BOOL', '急停常闭触点，TRUE = 正常'),
        ('OUT', 'ActiveRecipe', 'INT', '当前生效配方号'),
        ('OUT', 'SortLeft', 'BOOL', '分到左支线'),
        ('OUT', 'SortRight', 'BOOL', '分到右支线'),
        ('OUT', 'Busy', 'BOOL', '切换进行中'),
        ('OUT', 'Status', 'WORD', '状态码'),
    ],
    'initial_state': 'ActiveRecipe = 1；SortLeft = FALSE；SortRight = FALSE；Busy = FALSE；Status = 16#0000；ChangeoverReqLast = FALSE。',
    'constraints': [
        'K1 Busy = TRUE 期间 SortLeft 与 SortRight 均为 FALSE。',
        'K2 只有在无料且非忙时才允许切换配方。',
        'K3 RecipeSelect 非法（不在 1—3）时 ActiveRecipe 不变，仅置错误码。',
        'K4 分拣两路互斥，且同一产品只能分到一条支线。',
    ],
    'error_examples': [
        '错误实现：切换配方时不清分拣输出。症状——切换瞬间零件被旧阈值分到错误支线。',
        '错误实现：RecipeSelect 非法时把 ActiveRecipe 置 0。症状——所有产品都判超规格，整线停摆且无人知道原因。',
    ],
    'source_type': '改编自公开题',
    'source_ref': 'P17 Recipe Management System（课程题库）',
    'adaptation_what': '把「配方增删改查」改为「按配方阈值分拣」，把配方管理压缩成 3 组固定配方 + 切换请求。',
    'adaptation_why': '原题的数据库式增删改查在 ST 里难以自动化评测；改成阈值分拣后，配方切换的互斥与时序都能逐周期判定。',
    'notes': '',
}

SELF['S09'] = {
    'title': 'CIP 三步清洗时序',
    'difficulty': 'medium',
    'category': 'C',
    'zh_summary': '水洗 30 s、碱洗 60 s、清水 30 s 三步顺序执行，同一步只开一个阀，急停回零。',
    'requirement': """CIP（就地清洗）用于食品管路的批次间清洗，必须按固定顺序与时长执行。

控制要求：
1. StartCIP 上升沿启动流程：Step 1 水洗（WaterValve = TRUE，PumpRun = TRUE）持续 30 s。
2. 30 s 到后自动进入 Step 2 碱洗（LyeValve = TRUE，PumpRun = TRUE）持续 60 s；StepDone 可作为提前结束信号，按上升沿生效。
3. Step 2 结束后进入 Step 3 清水（RinseValve = TRUE，PumpRun = TRUE）持续 30 s；结束后关闭全部阀门与泵，StepNo = 0。
4. 任何时刻三个阀门中最多一个为 TRUE；PumpRun 为 TRUE 的前提是至少有一个阀门打开。
5. EStop_NC = FALSE 时立即关闭全部阀门与泵，StepNo 归 0，流程作废，需重新 StartCIP。
6. Status：16#0000 正常、16#8901 步序非法、16#8902 急停中断。""",
    'io_table': [
        ('IN', 'StartCIP', 'BOOL', '启动清洗（上升沿有效）'),
        ('IN', 'StepDone', 'BOOL', '当前步提前完成（上升沿有效）'),
        ('IN', 'EStop_NC', 'BOOL', '急停常闭触点，TRUE = 正常'),
        ('OUT', 'WaterValve', 'BOOL', '水洗阀'),
        ('OUT', 'LyeValve', 'BOOL', '碱洗阀'),
        ('OUT', 'RinseValve', 'BOOL', '清水阀'),
        ('OUT', 'PumpRun', 'BOOL', '循环泵'),
        ('OUT', 'StepNo', 'INT', '当前步号 0—3'),
        ('OUT', 'Status', 'WORD', '状态码'),
    ],
    'initial_state': '三个阀门与泵全 FALSE；StepNo = 0；Status = 16#0000；步计时器 = 0；StartCIPLast = FALSE；StepDoneLast = FALSE。',
    'constraints': [
        'K1 步序只能 0→1→2→3→0，不得跳步。',
        'K2 同一步内三个阀门互斥，最多一个为 TRUE。',
        'K3 PumpRun 为 TRUE 时至少有一个阀门为 TRUE（无空转）。',
        'K4 每步时长 30/60/30 s，StepDone 上升沿可提前结束当前步。',
        'K5 急停时全部输出 FALSE、StepNo 归 0。',
    ],
    'error_examples': [
        '错误实现：三步共用同一个定时器且不复位。症状——碱洗刚开始就把上一段的 30 s 余量算进去，清洗时间不足。',
        '错误实现：StepDone 用电平而不是上升沿。症状——同一个完成信号把连续两步都提前结束。',
    ],
    'source_type': '自拟',
    'source_ref': '食品工厂 CIP 就地清洗工艺卡：预洗—碱洗—漂洗三步，30/60/30 s 取自设备供应商清洗程序手册',
    'source_link': 'GB 14881-2013《食品安全国家标准 食品生产通用卫生规范》（清洗消毒条款）',
    'adaptation_what': '按真实 CIP 流程抽象出三步定时 + 阀门互斥 + 泵联锁。',
    'adaptation_why': '顺序 + 定时 + 互斥三项约束同时出现，是 ST 状态机最典型的形态，且时长参数可直接写成逐周期用例。',
    'notes': '',
}

SELF['S10'] = {
    'title': '变频器故障码分级报警',
    'difficulty': 'easy',
    'category': 'D',
    'zh_summary': '轻故障只报警、重故障跳闸并锁存，复位需按钮上升沿，运行中出故障立即跳闸。',
    'requirement': """变频器通过故障码上报状态，需要按严重程度分级处理。

控制要求：
1. VFDFaultCode = 16#0001 为轻故障：只点亮 AlarmLamp，不跳闸，VFDRun 保持。
2. VFDFaultCode = 16#0002 或 16#0003 为重故障：立即置 TripOutput = TRUE，AlarmLamp = TRUE，并锁存故障码。
3. 重故障锁存后，即使 VFDFaultCode 恢复为 16#0000 也不得自动复位；必须 ResetBtn 上升沿且当前无故障才解除 TripOutput。
4. 运行中（VFDRun = TRUE）出现任何非零故障码时，TripOutput 立即为 TRUE。
5. Status 输出当前生效的故障码（16#0000 表示无故障）。
6. 上电时 TripOutput = FALSE、AlarmLamp = FALSE、Status = 16#0000。""",
    'io_table': [
        ('IN', 'VFDFaultCode', 'WORD', '变频器故障码'),
        ('IN', 'VFDRun', 'BOOL', '变频器运行反馈'),
        ('IN', 'ResetBtn', 'BOOL', '复位按钮（上升沿有效）'),
        ('OUT', 'AlarmLamp', 'BOOL', '报警灯'),
        ('OUT', 'TripOutput', 'BOOL', '跳闸输出'),
        ('OUT', 'Status', 'WORD', '当前生效故障码'),
    ],
    'initial_state': 'AlarmLamp = FALSE；TripOutput = FALSE；Status = 16#0000；ResetBtnLast = FALSE；锁存故障码 = 16#0000。',
    'constraints': [
        'K1 重故障必须在同一周期内置 TripOutput。',
        'K2 重故障锁存，故障码消失后不自动复位。',
        'K3 复位只在 ResetBtn 上升沿且当前无故障时生效。',
        'K4 VFDRun = TRUE 且故障码非零时 TripOutput 立即为 TRUE。',
    ],
    'error_examples': [
        '错误实现：TripOutput := (VFDFaultCode <> 0)。症状——故障码自己消失后跳闸自动复位，设备在无人确认下重新启动。',
        '错误实现：复位用 ResetBtn 电平。症状——按住复位按钮时故障每周期被清掉又重现。',
    ],
    'source_type': '改编自公开题',
    'source_ref': 'P03 Alarm Handling（课程题库）',
    'adaptation_what': '把「模拟量滞回报警」换成「故障码分级 + 锁存 + 复位」，滞回改为分级判据。',
    'adaptation_why': '现场报警管理的核心不是阈值而是「分级 + 锁存 + 复位条件」，原题的滞回结构正好可以平移成三档判据。',
    'notes': '',
}

SELF['S11'] = {
    'title': '传感器断线检测与降级运行',
    'difficulty': 'hard',
    'category': 'D',
    'zh_summary': '4—20 mA 对应 0—100 ℃，断线（<3.6 或 >21 mA）时 2 s 后进入降级用备用值，恢复需 3 s 才退出。',
    'requirement': """温度变送器输出 4—20 mA，需要识别断线并降级运行，避免因单点故障停机。

控制要求：
1. SensorCurrent 在 4—20 mA 内时 SensorValid = TRUE，ControlValue = (SensorCurrent - 4) / 16 × 100（℃）。
2. SensorCurrent < 3.6 或 > 21 时判为断线：SensorValid = FALSE，持续 2 s 后置 DegradedMode = TRUE，ControlValue 切换为 FallbackValue。
3. 断线恢复（重新进入 3.8—20.5 mA）后 SensorValid = TRUE，但必须持续 3 s 才允许退出 DegradedMode（防止接线抖动反复切换）。
4. DegradedMode = TRUE 期间 AlarmLamp = TRUE；SensorValid = FALSE 但尚未满 2 s 时 AlarmLamp 闪烁（1 Hz）。
5. Status：16#0000 正常、16#8A01 断线、16#8A02 降级运行、16#8A03 恢复确认中。""",
    'io_table': [
        ('IN', 'SensorCurrent', 'REAL', '变送器电流（mA）'),
        ('IN', 'FallbackValue', 'REAL', '降级时的备用控制值（℃）'),
        ('OUT', 'SensorValid', 'BOOL', '信号有效'),
        ('OUT', 'DegradedMode', 'BOOL', '降级运行中'),
        ('OUT', 'ControlValue', 'REAL', '参与控制的温度值（℃）'),
        ('OUT', 'AlarmLamp', 'BOOL', '报警灯'),
        ('OUT', 'Status', 'WORD', '状态码'),
    ],
    'initial_state': 'SensorValid = FALSE；DegradedMode = FALSE；ControlValue = 0.0；AlarmLamp = FALSE；Status = 16#0000；断线与恢复计时器均清零。',
    'constraints': [
        'K1 断线判据用 3.6 mA 与 21 mA，恢复判据用 3.8 mA 与 20.5 mA（进出阈值不同，构成滞回）。',
        'K2 断线持续 2 s 才进入降级，避免瞬时干扰导致切换。',
        'K3 恢复持续 3 s 才退出降级，退出前 ControlValue 继续使用 FallbackValue。',
        'K4 DegradedMode = TRUE 期间 ControlValue 必须等于 FallbackValue。',
        'K5 DegradedMode = TRUE 期间 AlarmLamp 必须常亮；SensorValid = FALSE 但尚未满 2 s 时 AlarmLamp 以 1 Hz 闪烁、ControlValue 输出 0（安全默认，本组口径）。',
    ],
    'error_examples': [
        '错误实现：断线判据只有 SensorCurrent < 4。症状——变送器输出 3.9 mA（正常低端）也被判断线，机组频繁降级。',
        '错误实现：断线立即进入降级、恢复立即退出。症状——接线端子松动时 ControlValue 在测量值与备用值之间反复跳变。',
    ],
    'source_type': '自拟',
    'source_ref': 'NAMUR 推荐性规范 NE 43：用 4—20 mA 信号的电流水平表示变送器故障（<=3.6 mA 断线、>=21 mA 短路）',
    'source_link': 'NAMUR NE 43:2003（标准号；NAMUR 官方推荐清单可查）',
    'adaptation_what': '按 NE43 的电流区间判据，构造断线检测 + 双向计时 + 降级切换的完整逻辑。',
    'adaptation_why': '单点故障降级是流程工业的标准做法，且同时包含滞回、双定时器、输出切换三类约束，适合作为难题。',
    'notes': '',
}

SELF['S12'] = {
    'title': '急停后安全重启与班次统计',
    'difficulty': 'medium',
    'category': 'D',
    'zh_summary': '急停后必须门关、复位、启动三步确认才能重启；急停期间计数冻结，重启后班次计数继续累加。',
    'requirement': """设备急停后不允许简单松手就恢复，必须经过一套确认流程。

控制要求：
1. EStop_NC = FALSE 时 MachineRun 立即 FALSE，AlarmLamp = TRUE，Status = 16#8B01。
2. 急停解除后（EStop_NC = TRUE）进入待复位态：必须同时满足 DoorClosed = TRUE，且 ResetBtn 上升沿确认，再出现 StartBtn 上升沿，MachineRun 才允许为 TRUE。
3. 上述三个条件必须按「门关 → 复位 → 启动」的顺序满足；复位后若门再次打开，必须重新复位。
4. 急停期间 ShiftCount 冻结不变；重启后继续累加，不清零。
5. MachineRun = TRUE 时每 60 s 使 ShiftCount 加 1（用于统计本班运行时长，单位分钟）。
6. Status：16#0000 正常、16#8B01 急停、16#8B02 待复位、16#8B03 门未关。""",
    'io_table': [
        ('IN', 'EStop_NC', 'BOOL', '急停常闭触点，TRUE = 正常'),
        ('IN', 'ResetBtn', 'BOOL', '复位按钮（上升沿有效）'),
        ('IN', 'StartBtn', 'BOOL', '启动按钮（上升沿有效）'),
        ('IN', 'DoorClosed', 'BOOL', '安全门关闭'),
        ('OUT', 'MachineRun', 'BOOL', '设备运行'),
        ('OUT', 'ShiftCount', 'UINT', '本班运行分钟数'),
        ('OUT', 'AlarmLamp', 'BOOL', '报警灯'),
        ('OUT', 'Status', 'WORD', '状态码'),
    ],
    'initial_state': 'MachineRun = FALSE；ShiftCount = 0；AlarmLamp = FALSE；Status = 16#0000；已复位标志 = FALSE；ResetBtnLast = StartBtnLast = FALSE。',
    'constraints': [
        'K1 EStop_NC = FALSE 时 MachineRun 必须为 FALSE。',
        'K2 重启必须依次满足「门关 → 复位上升沿 → 启动上升沿」，缺一不可。',
        'K3 门在复位后再次打开时，已复位标志失效，必须重新复位。',
        'K4 急停期间 ShiftCount 保持不变；运行满 60 s 加 1。',
    ],
    'error_examples': [
        '错误实现：急停解除后自动重启。症状——操作员手还在设备里，设备自行启动，这是最严重的一类缺陷。',
        '错误实现：急停时把 ShiftCount 清 0。症状——频繁急停的班次统计永远偏小，无法用于绩效核算。',
    ],
    'source_type': '改编自公开题',
    'source_ref': 'P05 Weld Gap Alarm and Startup Inhibition（课程题库）',
    'adaptation_what': '把「上电抑制期」改造成「急停后三步重启确认」，并加入班次计数冻结/续算。',
    'adaptation_why': '原题的抑制期是单向时间窗，这里换成有序的多条件确认，能把「顺序 + 边沿 + 保持」三类约束同时考出来。',
    'notes': '',
}

SELF['S13'] = {
    'title': '双段输送合流同步与堵料防撞',
    'difficulty': 'hard',
    'category': 'C',
    'zh_summary': '主线段与汇流段协同：合流段有料时汇流段不得送料，堵料 2 s 定位停机，有料 3 s 切高速、无料 5 s 回落低速。',
    'requirement': """两段输送线在合流点汇合，控制系统要同时管住「不撞料」「不堵料」「不频繁换档」三件事。

控制要求：
1. LineRun = FALSE 时 MainMotor、MergeMotor 立即 FALSE，SpeedHigh = FALSE，Status = 16#0000。
2. 启动：LineRun 上升沿且 JamAlarm = FALSE 时 MainMotor = TRUE；MergeMotor 只在 PartAtMerge = FALSE 且 MainMotor = TRUE 时才允许为 TRUE。
3. 防撞互锁：PartAtMerge = TRUE 时 MergeMotor 必须为 FALSE（合流段有料，汇流段不得继续送料）。
4. 堵料：JamSensor = TRUE 连续 2 s（100 个扫描周期）→ 两电机 FALSE、JamAlarm = TRUE、Status = 16#8C01。
5. 复位：JamSensor = FALSE 且 ResetBtn 上升沿才清 JamAlarm 与 Status；复位后必须重新给 LineRun 上升沿才允许启动。
6. 速度档：MainMotor = TRUE 且 PartOnMain 连续 TRUE 3 s（150 周期）→ SpeedHigh = TRUE；PartOnMain 连续 FALSE 5 s（250 周期）→ SpeedHigh = FALSE；两个时限之间保持原档位。
7. ModeAuto = FALSE 时只做联锁与报警，不自动启停（手动模式由操作员点动，本规约不约束）。""",
    'io_table': [
        ('IN', 'LineRun', 'BOOL', '产线运行指令，上升沿启动'),
        ('IN', 'PartAtMerge', 'BOOL', '合流段有料'),
        ('IN', 'PartOnMain', 'BOOL', '主线段有料'),
        ('IN', 'JamSensor', 'BOOL', '堵料检测开关'),
        ('IN', 'ResetBtn', 'BOOL', '复位按钮，上升沿有效'),
        ('IN', 'ModeAuto', 'BOOL', 'TRUE = 自动模式'),
        ('OUT', 'MainMotor', 'BOOL', '主输送电机'),
        ('OUT', 'MergeMotor', 'BOOL', '汇流段输送电机'),
        ('OUT', 'SpeedHigh', 'BOOL', '高速档'),
        ('OUT', 'JamAlarm', 'BOOL', '堵料报警'),
        ('OUT', 'Status', 'WORD', '状态码'),
    ],
    'initial_state': 'MainMotor = MergeMotor = SpeedHigh = JamAlarm = FALSE；Status = 16#0000；LineRunLast = ResetBtnLast = FALSE；堵料计时器 = 0；有料计时器 = 0。',
    'constraints': [
        'K1 LineRun = FALSE 时两台电机必须为 FALSE。',
        'K2 PartAtMerge = TRUE 时 MergeMotor 不得为 TRUE（防撞互锁）。',
        'K3 JamSensor 连续 2 s 为 TRUE 必须在 2 s 内报警并停机，Status = 16#8C01；报警锁存到复位。',
        'K4 复位需要 JamSensor = FALSE 且 ResetBtn 上升沿，复位后需重新 LineRun 上升沿。',
        'K5 有料 3 s 切高速、无料 5 s 回落低速，中间区间保持原档位（不抖动）。',
    ],
    'error_examples': [
        '错误实现：汇流电机只跟随 LineRun，不判断 PartAtMerge。症状——合流段已有料时汇流段继续送料，两件工件在合流点相撞。',
        '错误实现：堵料用即时报警（JamSensor 为 TRUE 就报警）。症状——工件短暂遮挡光电开关就停机，产线每小时停十几次。',
    ],
    'source_type': '自拟',
    'source_ref': '参照 西门子杯中国智能制造挑战赛 离散行业自动化（逻辑算法）赛题中的合流段与防堵工艺',
    'source_link': 'https://www.siemenscup-cimc.org.cn/project/index',
    'adaptation_what': '新增合流防撞互锁、堵料 2 s 定位停机、速度档 3 s/5 s 双时限滞回三组要求。',
    'adaptation_why': '把「多段设备协同」拆成互斥、响应时限、滞回三类可逐周期判定的性质，正好覆盖 C4、C5、C7 三种条款。',
    'notes': '',
}

SELF['S14'] = {
    'title': '液压站压力分级加载与卸荷',
    'difficulty': 'medium',
    'category': 'B',
    'zh_summary': '按压力分级投切两台泵：低于 120 bar 加载、高于 160 bar 卸荷停泵，100—140 bar 之间保持原状态，传感器越界立即停机报警。',
    'requirement': """液压站按系统压力自动投切泵组与卸荷阀，要求不频繁启停、越界立即保护。

控制要求：
1. PumpEnable = TRUE 且 AlarmLamp = FALSE 时按压力分级加载：Pressure < 120.0 bar → LowPump = TRUE。
2. 高压泵投入：Pressure >= 140.0 bar → HighPump = TRUE。
3. 滞回：HighPump 投入后，只有 Pressure < 100.0 bar 才断开；100.0 <= Pressure < 140.0 区间保持原状态，不得反复启停。
4. 卸荷：Pressure > 160.0 bar → ReliefValve = TRUE 且 LowPump、HighPump 同时 FALSE；Pressure < 150.0 bar 后 ReliefValve = FALSE。
5. 卸荷阀与泵互斥：ReliefValve 与 LowPump/HighPump 不得同时为 TRUE。
6. 传感器越界：Pressure < 0.5 bar 或 Pressure > 250.0 bar 视为断线/短路 → 两泵 FALSE、AlarmLamp = TRUE、Status = 16#8D01；故障消失后需 ResetBtn 上升沿复位（复位前 Status = 16#8D02）。
7. Status：16#0000 正常、16#8D01 传感器故障、16#8D02 待复位。""",
    'io_table': [
        ('IN', 'Pressure', 'REAL', '系统压力，单位 bar'),
        ('IN', 'PumpEnable', 'BOOL', '允许加载'),
        ('IN', 'ResetBtn', 'BOOL', '复位按钮，上升沿有效'),
        ('OUT', 'LowPump', 'BOOL', '低压泵'),
        ('OUT', 'HighPump', 'BOOL', '高压泵'),
        ('OUT', 'ReliefValve', 'BOOL', '卸荷阀'),
        ('OUT', 'AlarmLamp', 'BOOL', '报警灯'),
        ('OUT', 'Status', 'WORD', '状态码'),
    ],
    'initial_state': 'LowPump = HighPump = ReliefValve = AlarmLamp = FALSE；Status = 16#0000；ResetBtnLast = FALSE；HighPumpLatched = FALSE。',
    'constraints': [
        'K1 Pressure > 160.0 bar 时必须在同一周期卸荷并停泵。',
        'K2 Pressure < 120.0 bar 且 PumpEnable 时必须加载低压泵（允许一个扫描周期延迟）。',
        'K3 高压泵在 100.0—140.0 bar 之间保持原状态，构成 40 bar 滞回带。',
        'K4 传感器越界（< 0.5 或 > 250.0 bar）必须在 200 ms 内停机报警，Status = 16#8D01。',
        'K5 卸荷阀与任一台泵不得同时为 TRUE。',
    ],
    'error_examples': [
        '错误实现：只要 Pressure < 120 就投高压泵。症状——高低压泵同时运行，压力在 120 bar 附近抖动，两台泵每小时启停上百次。',
        '错误实现：不对 Pressure 做量程检查，直接参与比较。症状——传感器断线时 Pressure 读数为 0，程序判定「压力过低」长期加载，泵干转。',
    ],
    'source_type': '自拟',
    'source_ref': '液压站分级加载与卸荷为通用液压控制惯例（压力继电器 + 卸荷阀组）',
    'source_link': 'ISO 4413:2010《液压传动 系统及其元件的一般规则和安全要求》（压力保护与卸荷条款）',
    'adaptation_what': '新增 40 bar 滞回带、卸荷阀与泵互斥、传感器越界停机三组要求。',
    'adaptation_why': '模拟量题最容易写成「单阈值比较」，加上滞回与量程检查才考得出现场真正会犯的错（抖动、断线干转）。',
    'notes': '',
}

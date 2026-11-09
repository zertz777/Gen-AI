# 附录 A　逐题形式化规约

本附录列出冻结数据中的全部 34 份 LTL 规约。每条公式保留条款号、时序表达式、验收口径与 K 约束引用；完整文件位于 `data/specs/<task_id>.ltl`。

## A.1　公共题 P01-P20

### P01　Automated Filling Line Control

难度：easy；类别：C；I/O：11；规约：`data/specs/P01.ltl`。

```text
C1: G(finishedButton -> X(!Pump_Motor && !Filling_Valve && !Capping_Machine && !Packing_Machine))    -- 完成按钮按下后下一周期四路执行器全部停止（停止优先于继续推进）（K4）
C2: G(cleaningConfirmButton -> X(!Pump_Motor))    -- 清洗确认后下一周期必须停泵（需求 1 的 continues to work 指本工步持续到确认，不是泵必须一直转；原「泵运行时必须有瓶子」的反向约束已删除）（K1）
C3: G(Filling_Valve -> (cleaningConfirmButton W Filling_Valve))    -- 灌装阀打开前，清洗确认必须已成立并保持（顺序推进）（K1）
C4: G(!(Pump_Motor && Filling_Valve) && !(Pump_Motor && Capping_Machine) && !(Pump_Motor && Packing_Machine) && !(Filling_Valve && Capping_Machine) && !(Filling_Valve && Packing_Machine) && !(Capping_Machine && Packing_Machine))    -- 四路执行器两两互斥（同一时刻只有一个动作）（K2）
C6: G(Completion_Light -> (Completion_Light W finishedButton))    -- 完成灯点亮后保持，直到操作员按下 finishedButton（K4）
C9: G[0,1](!Pump_Motor && !Filling_Valve && !Capping_Machine && !Packing_Machine && !Completion_Light)    -- 上电首周期所有输出为 FALSE（初态无动作）（初态）
```

### P02　Dual-Word Edge Detection

难度：easy；类别：B；I/O：8；规约：`data/specs/P02.ltl`。

```text
C2: G(hasChanged -> (hasRisingEdges || hasFallingEdges))    -- 报了变化就必须报出至少一类边沿（三个标志不得自相矛盾）（K1）
C2b: G((hasRisingEdges || hasFallingEdges) -> hasChanged)    -- 报了边沿就必然有变化（防止上电或复位时误报）（K4）
C7: G(!hasChanged -> X(!hasRisingEdges && !hasFallingEdges))    -- 无变化的周期之后不得凭空出现边沿标志（不抖动）（K1）
C8: G(hasChanged == FALSE -> noOfRisingBits == 0 && noOfFallingBits == 0)    -- 无变化时两个计数必须为 0（计数与标志同源）（K3）
C10: G[0,1](!hasChanged && !hasRisingEdges && !hasFallingEdges && noOfRisingBits == 0 && noOfFallingBits == 0)    -- 上电首周期不报变化（没有上一周期可比）（K4）
```

### P03　Alarm Handling

难度：easy；类别：D；I/O：8；规约：`data/specs/P03.ltl`。

```text
C1: G(error -> X(!hiAlarm && !loAlarm))    -- 参数错误时不得输出报警，且下一周期保持关断（错误优先于报警）（K1/K2）
C2: G(hiAlarm || loAlarm -> paramsValid)    -- 任何报警都要求参数合法（无合法参数不得报警）（K1/K2）
C4: G(!(hiAlarm && loAlarm))    -- 高报与低报互斥（同一时刻不可能既高又低）（K3/K4）
C7: G(hiAlarm -> (hiAlarm W Value < hiLevel - hystWindow))    -- 高报只在回落到 hiLevel - hystWindow 以下才允许复位（滞回）（K3）
C7b: G(loAlarm -> (loAlarm W Value > loLevel + hystWindow))    -- 低报只在回升到 loLevel + hystWindow 以上才允许复位（滞回）（K4）
C10: G[0,1](!hiAlarm && !loAlarm && !error && status == 16#0000)    -- 上电首周期无报警、无错误、状态码为 0（初态）
```

### P04　Jam Pump Debouncing and Runtime Maintenance

难度：easy；类别：D；I/O：7；规约：`data/specs/P04.ltl`。

```text
C1: G(!PASTE_E_STOP_NC -> !VFD_RUN)    -- 急停动作当周期泵必须停（急停优先于一切）（K1）
C2: G(VFD_RUN -> (PASTE_E_STOP_NC && VISCOSITY_OK))    -- 泵运行的许可条件：无急停且粘度合格（K3）
C7: G(!VISCOSITY_OK -> X(!VFD_RUN))    -- 粘度条件失效后下一周期必须停泵（去抖计时作废）（K2/K3）
C8: G(PUMP_MAINT_DUE -> X(PUMP_MAINT_DUE))    -- 维护提示置位后不得自行消失（只作信息输出）（K5）
C10: G[0,1](!VFD_RUN && !PUMP_MAINT_DUE)    -- 上电首周期泵不运行、维护提示不亮（初态）
```

### P05　Weld Gap Alarm and Startup Inhibition

难度：easy；类别：A；I/O：5；规约：`data/specs/P05.ltl`。

```text
C1: G(!Weld_E_Stop_NC -> !Operator_Alert)    -- 急停当周期必须清报警（急停优先于抑制期与监视）（K4）
C2: G(Operator_Alert -> Weld_E_Stop_NC)    -- 报警的前提是急停正常（不得在急停状态下报警）（K4）
C6: G(Operator_Alert -> (Operator_Alert W !Gap_Exceeded))    -- 间隙恢复后报警才允许撤销（报警保持）（K3）
C9: G(Operator_Alert -> G[0,25](Operator_Alert))    -- 报警一旦置位至少保持 500 ms（去抖后的最小脉宽）（K2）
C10: G[0,1](!Operator_Alert && Weld_Soft_Start_Active)    -- 上电首周期处于抑制期：不报警、软启动有效（K1）
```

### P06　Aeration Blower Delayed Start

难度：easy；类别：A；I/O：4；规约：`data/specs/P06.ltl`。

```text
C1: G(!AERATION_E_STOP_NC -> !BLOWER_RUN)    -- 急停当周期风机必须停（K1/K3）
C2: G(BLOWER_RUN -> (DO_LOW && AERATION_E_STOP_NC))    -- 风机运行的双许可：溶解氧偏低且无急停（K2）
C3: G(!DO_LOW -> X(!BLOWER_RUN))    -- 溶解氧恢复后下一周期必须停机并复位启动计时（K3）
C6: G(BLOWER_RUN -> (BLOWER_RUN W !DO_LOW))    -- 需求持续期间风机保持运行，不因单周期抖动反复启停（K2/K3）
C10: G[0,1](!BLOWER_RUN)    -- 上电首周期风机不运行（需先计满 5 s）（K1）
```

### P07　Multi-Pump Switching Control System

难度：medium；类别：A；I/O：7；规约：`data/specs/P07.ltl`。

```text
C1: G(stop -> !RunComd)    -- 停止请求当周期必须清除运行命令（stop 优先于 start）（K4）
C2: G(RunComd -> !stop)    -- 运行命令的前提是没有停止请求（互斥的许可形式）（K4）
C4: G(!(start && stop))    -- 启动与停止同时有效属于非法请求，不得出现（K4）
C6: G(RunComd -> (RunComd W stop))    -- 运行命令保持到停止请求出现为止（不自行掉线）（K1）
C10: G[0,1](!RunComd)    -- 上电首周期无运行命令（初态）
```

### P08　Analog Batch Processing

难度：medium；类别：B；I/O：10；规约：`data/specs/P08.ltl`。

```text
C1: G(!chEn -> chOut == 0.0)    -- 未使能的通道不得输出非零工程量（安全默认）（K1/K5）
C2: G(count < 0 -> !chEn)    -- 通道计数为负时不得使能任何通道（越界不处理）（K1/K5）
C2b: G(count == 0 -> !chEn)    -- 通道数为 0 时不得使能任何通道（题面 initial_state：count = 0 时不做任何通道）（K1）
C6: G(chRet != 16#0000 -> (chRet != 16#0000 W chEn))    -- 错误码保持到该通道重新使能，不得自行消失（K5）
C10: G[0,1](chOut == 0.0)    -- 上电首周期不输出任何工程量（初态）
```

### P09　Calculate Moving Average

难度：medium；类别：B；I/O：9；规约：`data/specs/P09.ltl`。

```text
C1: G(reset -> !windowSizeReached)    -- 复位当周期必须清除窗口满标志（复位优先于周期与触发）（K4）
C3: G(windowSize < 1 -> F[0,1](error))    -- 窗口长度小于 1 时必须报错（不得静默）（K3）
C3b: G(windowSize > 100 -> F[0,1](error))    -- 窗口长度大于 100 时必须报错（K3）
C2: G(windowSizeReached -> !error)    -- 窗口满标志与错误标志不得同时为真（K3）
C10: G[0,1](!windowSizeReached && !error && average == 0.0)    -- 上电首周期无窗口、无错误、平均值为 0（初态）
```

### P10　Temperature Logic Control

难度：medium；类别：B；I/O：7；规约：`data/specs/P10.ltl`。

```text
C1: G(OverheatProtection -> !HeaterOutput)    -- 过热保护动作时加热必须关断（保护优先于温控）（K2）
C2: G(HeaterOutput -> !OverheatProtection)    -- 加热的前提是没有过热保护（同一约束的许可形式）（K2）
C7: G(TemperatureSensorInput < 0.0 -> X(!HeaterOutput))    -- 低于 0 ℃ 判为传感器故障，下一周期不得加热（K4）
C7b: G(TemperatureSensorInput > 100.0 -> X(!HeaterOutput))    -- 高于 100 ℃ 判为传感器故障，下一周期不得加热（K4）
C9: G(OverheatProtection -> G[0,150](OverheatProtection))    -- 过热保护触发后至少保持 3 s 才能解除（K3）
C10: G[0,1](!HeaterOutput && !OverheatProtection)    -- 上电首周期不加热、无保护（初态）
```

### P11　Automated Production Line Control

难度：medium；类别：C；I/O：12；规约：`data/specs/P11.ltl`。

```text
C4: G(!(MotorForward && MotorReverse))    -- 正转与反转互斥（手动模式下的硬约束）（K1）
C2: G(MotorForward -> !MotorReverse)    -- 正转的许可是反转未动作（K1）
C3: G(CompletionLight -> SensorC)    -- 完成灯只在 C 站到位后点亮（顺序推进的必要条件）（K2/K4）
C6: G(CompletionLight -> (CompletionLight W !SensorC))    -- 完成灯保持到产品离开 C 站（K4）
C10: G[0,1](!MotorForward && !MotorReverse && !CompletionLight)    -- 上电首周期无正反转、完成灯灭（初态）
```

### P12　Slab Thickness Alarm and Fault History

难度：medium；类别：D；I/O：9；规约：`data/specs/P12.ltl`。

```text
C2: G(THICKNESS_ALARM -> THICKNESS_SIGNAL_VALID)    -- 信号无效期间不得报警（报警的前提是信号有效）（K1）
C5: G(THICKNESS_FAULT && THICKNESS_SIGNAL_VALID -> F[0,25](THICKNESS_ALARM))    -- 故障出现后 500 ms 内必须报警（响应时限）（K3）
C6: G(THICKNESS_ALARM -> (THICKNESS_ALARM W !THICKNESS_FAULT))    -- 故障持续期间报警保持（至少 500 ms 由此推出）（K3）
C8: G(!THICKNESS_SIGNAL_VALID -> X(!THICKNESS_ALARM))    -- 信号失效后下一周期清报警，不保留陈旧报警（K1）
C10: G[0,1](!THICKNESS_ALARM)    -- 上电首周期不报警（初态）
```

### P13　Office HVAC Multi-mode Energy-Saving Control

难度：medium；类别：B；I/O：5；规约：`data/specs/P13.ltl`。

```text
C2: G(SUPPLY_FAN_RUN -> (OCCUPANCY_DETECTED && HVAC_MODE_SELECTOR != 3))    -- 风机运行的许可：有占用且未选夜间模式（模式取值 0 自动 / 1 舒适 / 2 节能 / 3 夜间）（K1/K2）
C3: G(!OCCUPANCY_DETECTED -> X(!SUPPLY_FAN_RUN))    -- 占用丢失后下一周期必须停风机（启动延时不适用停机）（K2）
C6: G(SUPPLY_FAN_RUN -> (SUPPLY_FAN_RUN W !OCCUPANCY_DETECTED))    -- 占用期间风机保持，不因单周期抖动反复启停（K2）
C4: G(TEMP_SETPOINT_ADJUST >= -4 && TEMP_SETPOINT_ADJUST <= 4)    -- 温度修正必须限制在 ±4 ℃（输出限幅）（K4）
C10: G[0,1](!SUPPLY_FAN_RUN && TEMP_SETPOINT_ADJUST == 0)    -- 上电首周期风机不运行、修正为 0（初态）
```

### P14　IPv4 Parsing with Format and Range Checks

难度：medium；类别：B；I/O：2；规约：`data/specs/P14.ltl`。

```text
C2: G(ipValue <= 16#FFFFFFFF)    -- 输出必须落在 32 位无符号整数域内（不得溢出）（K3）
C10: G[0,1](ipValue == 0)    -- 上电首周期输出 0（初态）
```

### P15　Material Proportioning Process Control

难度：hard；类别：C；I/O：16；规约：`data/specs/P15.ltl`。

```text
C1: G(!estop -> (!valveARun && !valveBRun && !valveCRun && !valveDRun && !mixMotorRun))    -- 急停当周期全部设备停止（优先于手动与自动）（K1）
C2: G(mixMotorRun -> !estop)    -- 搅拌运行的许可：无急停（K1）
C4: G(!(valveDRun && (valveARun || valveBRun || valveCRun)))    -- 出料阀与前三个配比阀互斥（配比与出料不得同时进行）（K3）
C6: G(mixMotorRun -> (mixMotorRun W mixMotorComplete))    -- 搅拌保持到完成信号出现（K3）
C10: G[0,1](!valveARun && !valveBRun && !valveCRun && !valveDRun && !mixMotorRun)    -- 上电首周期全部设备停止（初态）
```

### P16　Flexible Processing Control

难度：hard；类别：C；I/O：13；规约：`data/specs/P16.ltl`。

```text
C4: G(!(conveyorLeft && conveyorRight))    -- 左右输送互斥（同一时刻只有一个方向）（K2）
C2: G(conveyorLeft -> !conveyorRight)    -- 左行的许可是右行未动作（K2）
C1: G(processLength == 0 -> X(!conveyorLeft && !conveyorRight))    -- 工艺长度为 0 时下一周期必须停止输送（空工艺不得启动）（K4）
C9: G(conveyorLeft -> G[0,10](!conveyorRight))    -- 左行开始后 200 ms 内不得切到右行（换向死区）（K2）
C10: G[0,1](!conveyorLeft && !conveyorRight)    -- 上电首周期不输送（初态）
```

### P17　Recipe Management System

难度：hard；类别：C；I/O：16；规约：`data/specs/P17.ltl`。

```text
C1: G(error -> !(recipeAdded || recipeDeleted || recipeModified))    -- 出错时不得同时报成功（失败不掩盖）（K2/K3/K4）
C2: G(recipeAdded -> status == 16#0000)    -- 新增成功的唯一状态码是 16#0000（K2）
C4: G(!(recipeAdded && recipeDeleted))    -- 同一周期不可能既新增又删除（K1）
C6: G(error -> (error W (addRecipe || deleteRecipe || modifyRecipe || queryRecipe)))    -- 错误标志保持到下一次请求为止（不得自动消失）（K2/K3/K4）
C10: G[0,1](!error && !recipeAdded && !recipeDeleted && !recipeModified)    -- 上电首周期无错误、无成功标志（初态）
```

### P18　FIFO First-In-First-Out Queue

难度：hard；类别：B；I/O：7；规约：`data/specs/P18.ltl`。

```text
C1: G(reset -> elementCount == 0)    -- 复位当周期队列必须清空（优先于同周期的入队/出队）（K1）
C4: G(reset && enqueue -> X(elementCount == 0))    -- 复位与入队同时请求时以复位为准（下一周期仍为空）（K1）
C2: G(elementCount >= 0)    -- 元素计数不得为负（出队不得越过队首）（K3/K4）
C9: G(reset -> G[0,1](elementCount == 0))    -- 复位后至少保持一个周期为空（K1）
C10: G[0,1](elementCount == 0)    -- 上电首周期队列为空（初态）
```

### P19　Mechanical Arm Control

难度：hard；类别：C；I/O：24；规约：`data/specs/P19.ltl`。

```text
C1: G(!EmergencyStop -> X(!MoveDown && !MoveUp && !MoveLeft && !MoveRight && !ActivateGrip && !ActivateRelease))    -- 急停（EmergencyStop = FALSE）后下一周期六路动作全部停止（K4）
C2: G(ManualMode && DownButton && !DownLimitSwitch && EmergencyStop -> MoveDown)    -- 手动模式下的启动条件：按钮按下、未到限位且无急停（EmergencyStop = TRUE）（K1）
C4: G(!(MoveDown && MoveUp) && !(MoveLeft && MoveRight) && !(ActivateGrip && ActivateRelease))    -- 三对反向动作两两互斥（K1/K5）
C7: G(DownLimitSwitch -> X(!MoveDown))    -- 到达下限位后下一周期必须停止下行动作（K1）
C6: G(ActivateGrip -> (ActivateGrip W GripLimitSwitch))    -- 抓取输出保持到抓取限位到位为止（K5）
C10: G[0,1](!MoveDown && !MoveUp && !MoveLeft && !MoveRight && !ActivateGrip && !ActivateRelease)    -- 上电首周期无动作输出（初态）
```

### P20　Production Control

难度：hard；类别：C；I/O：17；规约：`data/specs/P20.ltl`。

```text
C4: G(!(MotorForward && MotorReverse))    -- 正反转互斥（K1）
C2: G(kick -> SensorOutput)    -- 出料动作的前提是成品站到位（K4）
C1: G(CompletionLight -> X(!kick))    -- 完成灯点亮后下一周期出料动作必须停止（K4）
C6: G(CompletionLight -> (CompletionLight W !SensorOutput))    -- 完成灯保持到产品离开成品站（K4）
C10: G[0,1](!MotorForward && !MotorReverse && !kick && !CompletionLight)    -- 上电首周期无输出（初态）
```

## A.2　自编题 S01-S14

### S01　双工位气动夹具互锁

难度：easy；类别：A；I/O：8；规约：`data/specs/S01.ltl`。

```text
C1: G(!EStop_NC -> (!ClampLeft && !ClampRight))    -- 急停当周期两侧夹具必须松开（K4）
C2: G(ClampLeft -> LeftPartPresent)    -- 夹紧的前提是对应工位有零件（左侧）（K2）
C2b: G(ClampRight -> RightPartPresent)    -- 夹紧的前提是对应工位有零件（右侧）（K2）
C4: G(!(ClampLeft && ClampRight))    -- 两侧夹具互斥（共用一路气源）（K1）
C10: G[0,1](!ClampLeft && !ClampRight && !Busy)    -- 上电首周期两侧不夹紧、不忙（初态）
```

### S02　输送线正反转与检修锁

难度：easy；类别：A；I/O：8；规约：`data/specs/S02.ltl`。

```text
C1: G(!EStop_NC -> (!MotorFwd && !MotorRev))    -- 急停当周期两个方向都必须断开（K4）
C2: G(MotorFwd -> !MaintKey)    -- 检修钥匙插入时禁止正转（K3）
C2b: G(MotorRev -> !MaintKey)    -- 检修钥匙插入时禁止反转（K3）
C4: G(!(MotorFwd && MotorRev))    -- 正反转互斥（K1）
C9: G(MotorFwd && !MotorRev -> G[0,10](!MotorRev))    -- 正转期间 200 ms 内不得出现反转（换向死区）（K2）
C10: G[0,1](!MotorFwd && !MotorRev)    -- 上电首周期两个方向都不输出（初态）
```

### S03　安全门分级停机

难度：medium；类别：A；I/O：9；规约：`data/specs/S03.ltl`。

```text
C1: G(!EStop_NC -> (!DriveA_Run && !DriveB_Run))    -- 急停当周期两区都停（优先于分级延时）（K3）
C1b: G(DoorSwitch -> F[0,1](!DriveA_Run))    -- 门打开后 A 区当周期必须停（分级停机的高等级侧）（K1）
C5: G(DoorSwitch -> F[0,25](!DriveB_Run))    -- 门打开后 B 区 500 ms 内必须停（低等级侧允许走完当前动作）（K2）
C2: G(DriveA_Run -> (!DoorSwitch && EStop_NC))    -- A 区运行的许可：门关闭且无急停（K3）
C6: G(AlarmLamp -> (AlarmLamp W !DoorSwitch))    -- 门关闭后报警才允许撤销（不得随门抖动闪烁）（K4）
C10: G[0,1](!DriveA_Run && !DriveB_Run && !AlarmLamp)    -- 上电首周期两区都不运行、无报警（初态）
```

### S04　称重零点漂移补偿

难度：medium；类别：B；I/O：7；规约：`data/specs/S04.ltl`。

```text
C4: G(CompensatedWeight == (RawWeight - ZeroOffset) * 0.01)    -- 输出必须等于换算式（不得沿用上一周期的结果）（K2）
C2: G(DriftAlarm -> driftOut)    -- 报警的前提是偏差确实超限（不得空报）（K3）
C6: G(DriftAlarm -> (DriftAlarm W driftBack))    -- 偏差回落到 ±150 以内才允许撤警（滞回保持）（K3）
C7: G(DriftAlarm && driftBack -> X(!DriftAlarm))    -- 偏差回到 ±150 死区内就必须下一周期撤报（不得滞留）（K3）
C10: G[0,1](ZeroOffset == 0 && !DriftAlarm && CompensatedWeight == 0.0)    -- 上电首周期零点为 0、无报警（K4）
```

### S05　泵站流量累计与班次清零

难度：hard；类别：B；I/O：8；规约：`data/specs/S05.ltl`。

```text
C1: G(OverflowFlag -> TotalVolume <= 1000000.0)    -- 溢出标志置位后总量不得继续增长（也不得回绕）（K3）
C2: G(TotalVolume >= 0.0 && ShiftVolume >= 0.0)    -- 两个累计量都不得为负（单向累计）（K1）
C8: G(TotalVolume >= 1000000.0 -> X(OverflowFlag))    -- 达到上限后下一周期必须置溢出标志（K3）
C8b: G(OverflowFlag -> X(OverflowFlag))    -- 溢出标志一旦置位就永久保持（不自动清除）（K3）
C6: G(ShiftVolume <= TotalVolume)    -- 当班流量不得超过累计总量（班次清零不影响总量）（K2）
C10: G[0,1](TotalVolume == 0.0 && ShiftVolume == 0.0 && !OverflowFlag)    -- 上电首周期两个累计量为 0、无溢出（初态）
```

### S06　烘箱分段升温与超温降载

难度：medium；类别：B；I/O：9；规约：`data/specs/S06.ltl`。

```text
C1: G(LoadReduce -> !HeatOn)    -- 降载动作时加热必须关断（保护优先于温控）（K3）
C2: G(HeatOn -> FanOn)    -- 加热的前提是风机运行（禁止干烧）（K4）
C4: G(!(HeatOn && LoadReduce))    -- 加热与降载互斥（K3）
C7: G(OverTempAlarm -> (OverTempAlarm W TempPV <= SetTemp - 3.0))    -- 超温报警保持到温度回落到设定值以下 3 ℃（迟滞）（K3）
C8: G(Segment < 0 || Segment > 2 -> X(Status == 16#8601))    -- 段号非法时下一周期必须报错误码（K1）
C10: G[0,1](!HeatOn && !FanOn && !OverTempAlarm && !LoadReduce)    -- 上电首周期全部输出关断（初态）
```

### S07　灌装四工位节拍控制

难度：hard；类别：C；I/O：12；规约：`data/specs/S07.ltl`。

```text
C1: G(!EStop_NC -> (!Conveyor && !FillValve && !CapMotor && !PackCyl))    -- 急停当周期四路执行器全停（K5）
C2: G(FillValve -> BottleIn)    -- 开灌装阀的前提是瓶子到位（K2）
C4: G(!(Conveyor && FillValve) && !(Conveyor && CapMotor) && !(Conveyor && PackCyl) && !(FillValve && CapMotor) && !(FillValve && PackCyl) && !(CapMotor && PackCyl))    -- 四路执行器两两互斥（单工步动作）（K4）
C6: G(FillValve -> (FillValve W FillDone))    -- 灌装阀保持到灌装完成信号出现（K2）
C9: G(FillValve -> G[0,5](FillValve))    -- 灌装动作至少保持 100 ms（防抖，避免单周期抖动误判完成）（K3）
C10: G[0,1](!Conveyor && !FillValve && !CapMotor && !PackCyl)    -- 上电首周期无动作（初态）
```

### S08　分拣线配方切换

难度：hard；类别：C；I/O：9；规约：`data/specs/S08.ltl`。

```text
C1: G(Busy -> (!SortLeft && !SortRight))    -- 切换配方期间禁止分拣（切换优先于分拣）（K1）
C2: G(SortLeft -> PartHeight > 0.0)    -- 分拣的前提是线上有料（K4）
C4: G(!(SortLeft && SortRight))    -- 左右分拣互斥（K4）
C9: G(Busy -> G[0,100](Busy))    -- 切换状态至少保持 2 s（防止请求抖动造成反复切换）（K2）
C10: G[0,1](!SortLeft && !SortRight && !Busy && ActiveRecipe == 1)    -- 上电首周期默认配方 1、不分拣（初态）
```

### S09　CIP 三步清洗时序

难度：medium；类别：C；I/O：9；规约：`data/specs/S09.ltl`。

```text
C1: G(!EStop_NC -> (!WaterValve && !LyeValve && !RinseValve && !PumpRun))    -- 急停当周期所有阀门与泵关断（K5）
C2: G(PumpRun -> (WaterValve || LyeValve || RinseValve))    -- 泵运行的前提是至少一个阀门打开（禁止空转）（K3）
C4: G(!(WaterValve && LyeValve) && !(WaterValve && RinseValve) && !(LyeValve && RinseValve))    -- 三路阀门两两互斥（同一步只开一个阀）（K2）
C5: G(StartCIP && StepNo == 0 -> F[0,5](StepNo == 1))    -- 启动清洗后 100 ms 内必须进入水洗步（响应时限）（K1）
C10: G[0,1](StepNo == 0 && !PumpRun)    -- 上电首周期步号为 0、泵不运行（初态）
```

### S10　变频器故障码分级报警

难度：easy；类别：D；I/O：6；规约：`data/specs/S10.ltl`。

```text
C1: G(VFDRun && VFDFaultCode != 16#0000 && VFDFaultCode != 16#0001 -> TripOutput)    -- 运行中出现重故障码（除 16#0001 轻故障外）必须当周期跳闸（K4）
C2: G(TripOutput -> !VFDRun)    -- 跳闸的许可形式：跳闸时不得处于运行状态（K2）
C6: G(TripOutput -> (TripOutput W ResetBtn))    -- 跳闸保持到复位按钮（不能随故障码消失自动复位）（K3）
C7: G(VFDFaultCode == 16#0001 && VFDRun -> X(VFDRun))    -- 轻故障只报警不跳闸，运行状态不得因轻故障改变（K1）
C10: G[0,1](!TripOutput && !AlarmLamp && Status == 16#0000)    -- 上电首周期不跳闸、不报警（初态）
```

### S11　传感器断线检测与降级运行

难度：hard；类别：D；I/O：7；规约：`data/specs/S11.ltl`。

```text
C1: G(DegradedMode -> ControlValue == FallbackValue)    -- 降级期间输出必须是备用值（不得继续输出失效测量值）（K4）
C2: G(DegradedMode && SensorValid -> G[0,150](DegradedMode))    -- 信号恢复后仍须保持降级至少 3 s（150 个周期）才允许退出，防止接线抖动反复切换（K3）
C6: G(DegradedMode -> AlarmLamp)    -- 降级期间报警灯常亮（K5）
C10: G[0,1](!DegradedMode && !SensorValid && ControlValue == 0.0 && !AlarmLamp)    -- 上电首周期未降级、信号无效、输出 0（安全默认），报警灯灭（初态）
```

### S12　急停后安全重启与班次统计

难度：medium；类别：D；I/O：8；规约：`data/specs/S12.ltl`。

```text
C1: G(!EStop_NC -> !MachineRun)    -- 急停当周期设备必须停（K1）
C2: G(MachineRun -> DoorClosed)    -- 运行的许可：安全门关闭（K2）
C3: G(StartBtn && !DoorClosed -> X(!MachineRun))    -- 门未关时按启动不得启动（三步确认缺一不可）（K2/K3）
C4: G(!(MachineRun && AlarmLamp))    -- 报警期间不得运行（互斥）（K1）
C10: G[0,1](!MachineRun && ShiftCount == 0 && !AlarmLamp)    -- 上电首周期不运行、计数为 0（初态）
```

### S13　双段输送合流同步与堵料防撞

难度：hard；类别：C；I/O：11；规约：`data/specs/S13.ltl`。

```text
C1: G(!LineRun -> !MainMotor && !MergeMotor)    -- 总停时两段电机都必须停（K1）
C4: G(PartAtMerge -> !MergeMotor)    -- 合流段有料时汇流段不得送料（防撞互锁）（K2）
C5: G(JamSensor && LineRun -> F[0,100] JamAlarm)    -- 堵料 2 s 内必须报警（100 周期）（K3）
C6: G(JamAlarm && !(ResetBtn && !JamSensor) -> X(JamAlarm))    -- 报警锁存到复位条件满足（K3/K4）
C7: G(PartOnMain && MainMotor && !SpeedHigh -> F[0,150] SpeedHigh)    -- 有料 3 s 内切高速（150 周期）（K5）
C10: G[0,1](!MainMotor && !MergeMotor && !SpeedHigh && !JamAlarm && Status == 16#0000)    -- 上电首周期全部停机、无报警（初态）
```

### S14　液压站压力分级加载与卸荷

难度：medium；类别：B；I/O：8；规约：`data/specs/S14.ltl`。

```text
C1: G(Pressure > 160.0 -> X(!LowPump && !HighPump && ReliefValve))    -- 过压当周期卸荷并停泵（K1）
C2: G(Pressure < 120.0 && PumpEnable && !AlarmLamp -> X(LowPump))    -- 低压加载条件成立时一周期内投泵（K2）
C4: G(!(ReliefValve && LowPump) && !(ReliefValve && HighPump))    -- 卸荷阀与泵不得同时为 TRUE（K5）
C6: G((Pressure < 0.5 || Pressure > 250.0) -> F[0,10] AlarmLamp)    -- 传感器越界 200 ms 内报警（10 周期）（K4）
C7: G(HighPump && Pressure >= 100.0 && Pressure < 140.0 -> X(HighPump))    -- 滞回带内保持高压泵状态，不抖动（K3）
C10: G[0,1](!LowPump && !HighPump && !ReliefValve && !AlarmLamp && Status == 16#0000)    -- 上电首周期不加载、无报警（初态）
```

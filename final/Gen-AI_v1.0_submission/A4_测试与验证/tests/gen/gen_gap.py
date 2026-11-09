"""D2-5：补「四类必须齐」的缺口（边界 / 异常 / 正常），共 38 条。

为什么单独一个脚本：已有 25 题由 `gen_<题号>.py` 生成、9 题是手写 CSV。
逐题改 23 个生成器风险高（手改续行极易多一个逗号导致整列右移），
所以这里统一做「读现有 CSV → 去掉同号用例 → 追加新用例」，
只碰被追加的那几条，已有用例原样保留。

运行顺序（重要）：

    python gen/gen_P05.py && ... && python gen/gen_S14.py   # 或各自的生成器
    python gen/gen_gap.py                                   # 最后跑本脚本

改完任何 `gen_<题号>.py` 后要再跑一次本脚本，否则该题的补缺用例会被覆盖。
`pytest` 里的 `test_every_task_has_four_categories` 会兜住这个遗漏。

产物：直接改写 `tests/cases/<题号>.csv`（不新增文件）。
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TESTS = HERE.parent
CASES = TESTS / "cases"
FIX = CASES / "_fixtures"

sys.path.insert(0, str(HERE))
from _emit import META, fmt  # noqa: E402


def rows(*pairs):
    return [{"in": dict(i), "out": dict(o)} for i, o in pairs]


def span(n, ins, outs):
    return [{"in": dict(ins), "out": dict(outs)} for _ in range(n)]


# 生成器里的简写列名 → fixture 里的真实列名
ALIAS = {
    "P07": {"priority": "pumpGroup[].priority",
            "selection": "pumpGroup[].selection",
            "run": "pumpGroup[].RunComd"},
    "P17": {"recipe_ids": "recipe[].recipeID",
            "recipe_types": "recipe[].ingredientType",
            "recipe_ratios": "recipe[].ingredientRatio",
            "recipe_temps": "recipe[].productionTemperature"},
}

# 每题每拍都要带上的背景输入（其余缺省按类型补零）
BASE = {
    "P19": dict(ManualMode=True, SingleStepMode=False, SingleCycleMode=False,
                ContinuousMode=False, EmergencyStop=False, Start=False,
                DownButton=False, UpButton=False, LeftButton=False,
                RightButton=False, GripButton=False, ReleaseButton=False,
                DownLimitSwitch=False, UpLimitSwitch=True,
                LeftLimitSwitch=True, RightLimitSwitch=False,
                GripLimitSwitch=False, ReleaseLimitSwitch=False),
}


# ---------------------------------------------------------------- P01
P01 = [
    dict(case_id="P01-07", refs="K3;C2", category="异常",
         purpose="异常：清洗中瓶子被取走，泵必须立即停；无瓶时按确认键不得启动",
         rows=rows(
             (dict(bottleSensor=False, cleaningConfirmButton=False,
                   fillingConfirmButton=False, cappingConfirmButton=False,
                   packingConfirmButton=False, finishedButton=False),
              dict(Pump_Motor=False, Filling_Valve=False, Capping_Machine=False,
                   Packing_Machine=False, Completion_Light=False)),
             (dict(bottleSensor=False, cleaningConfirmButton=True,
                   fillingConfirmButton=False, cappingConfirmButton=False,
                   packingConfirmButton=False, finishedButton=False),
              dict(Pump_Motor=False, Filling_Valve=False, Capping_Machine=False,
                   Packing_Machine=False, Completion_Light=False)),
             (dict(bottleSensor=True, cleaningConfirmButton=False,
                   fillingConfirmButton=False, cappingConfirmButton=False,
                   packingConfirmButton=False, finishedButton=False),
              dict(Pump_Motor=True, Filling_Valve=False, Capping_Machine=False,
                   Packing_Machine=False, Completion_Light=False)),
             (dict(bottleSensor=False, cleaningConfirmButton=False,
                   fillingConfirmButton=False, cappingConfirmButton=False,
                   packingConfirmButton=False, finishedButton=False),
              dict(Pump_Motor=False, Filling_Valve=False, Capping_Machine=False,
                   Packing_Machine=False, Completion_Light=False)),
         )),
    dict(case_id="P01-08", refs="K1;K2;C4", category="边界",
         purpose="边界：每道确认键在当拍就推进，且切换拍只有一个执行器为 TRUE",
         rows=rows(
             (dict(bottleSensor=False, cleaningConfirmButton=False,
                   fillingConfirmButton=False, cappingConfirmButton=False,
                   packingConfirmButton=False, finishedButton=False),
              dict(Pump_Motor=False, Filling_Valve=False, Capping_Machine=False,
                   Packing_Machine=False, Completion_Light=False)),
             (dict(bottleSensor=True, cleaningConfirmButton=False,
                   fillingConfirmButton=False, cappingConfirmButton=False,
                   packingConfirmButton=False, finishedButton=False),
              dict(Pump_Motor=True, Filling_Valve=False, Capping_Machine=False,
                   Packing_Machine=False, Completion_Light=False)),
             (dict(bottleSensor=True, cleaningConfirmButton=True,
                   fillingConfirmButton=False, cappingConfirmButton=False,
                   packingConfirmButton=False, finishedButton=False),
              dict(Pump_Motor=False, Filling_Valve=True, Capping_Machine=False,
                   Packing_Machine=False, Completion_Light=False)),
             (dict(bottleSensor=True, cleaningConfirmButton=False,
                   fillingConfirmButton=True, cappingConfirmButton=False,
                   packingConfirmButton=False, finishedButton=False),
              dict(Pump_Motor=False, Filling_Valve=False, Capping_Machine=True,
                   Packing_Machine=False, Completion_Light=False)),
             (dict(bottleSensor=True, cleaningConfirmButton=False,
                   fillingConfirmButton=False, cappingConfirmButton=True,
                   packingConfirmButton=False, finishedButton=False),
              dict(Pump_Motor=False, Filling_Valve=False, Capping_Machine=False,
                   Packing_Machine=True, Completion_Light=False)),
             (dict(bottleSensor=True, cleaningConfirmButton=False,
                   fillingConfirmButton=False, cappingConfirmButton=False,
                   packingConfirmButton=True, finishedButton=False),
              dict(Pump_Motor=False, Filling_Valve=False, Capping_Machine=False,
                   Packing_Machine=False, Completion_Light=True)),
         )),
]

# ---------------------------------------------------------------- P04
P04 = [
    dict(case_id="P04-06", refs="K1;K2;K3;C2", category="异常",
         purpose="异常：上电即急停（PASTE_E_STOP_NC=FALSE），去抖期间泵不得启动；解除后须重新计满",
         rows=rows(
             (dict(VISCOSITY_OK=False, PASTE_E_STOP_NC=False,
                   DebounceTime=60, CycleTime=20),
              dict(VFD_RUN=False, PUMP_MAINT_DUE=False, PUMP_RUNTIME_ACC=0)),
             (dict(VISCOSITY_OK=True, PASTE_E_STOP_NC=False,
                   DebounceTime=60, CycleTime=20),
              dict(VFD_RUN=False, PUMP_MAINT_DUE=False, PUMP_RUNTIME_ACC="X")),
             (dict(VISCOSITY_OK=True, PASTE_E_STOP_NC=False,
                   DebounceTime=60, CycleTime=20),
              dict(VFD_RUN=False, PUMP_MAINT_DUE=False, PUMP_RUNTIME_ACC="X")),
             (dict(VISCOSITY_OK=True, PASTE_E_STOP_NC=True,
                   DebounceTime=60, CycleTime=20),
              dict(VFD_RUN=False, PUMP_MAINT_DUE=False, PUMP_RUNTIME_ACC="X")),
             (dict(VISCOSITY_OK=True, PASTE_E_STOP_NC=True,
                   DebounceTime=60, CycleTime=20),
              dict(VFD_RUN=False, PUMP_MAINT_DUE=False, PUMP_RUNTIME_ACC="X")),
             (dict(VISCOSITY_OK=True, PASTE_E_STOP_NC=True,
                   DebounceTime=60, CycleTime=20),
              dict(VFD_RUN=True, PUMP_MAINT_DUE=False, PUMP_RUNTIME_ACC="X")),
         )),
    dict(case_id="P04-07", refs="K2;K3", category="边界",
         purpose="边界：DebounceTime 取下限 1 拍（T#20ms），粘度满足的第一拍即运行",
         rows=rows(
             (dict(VISCOSITY_OK=False, PASTE_E_STOP_NC=True,
                   DebounceTime=20, CycleTime=20),
              dict(VFD_RUN=False, PUMP_MAINT_DUE=False, PUMP_RUNTIME_ACC=0)),
             (dict(VISCOSITY_OK=True, PASTE_E_STOP_NC=True,
                   DebounceTime=20, CycleTime=20),
              dict(VFD_RUN=True, PUMP_MAINT_DUE=False, PUMP_RUNTIME_ACC="X")),
             (dict(VISCOSITY_OK=False, PASTE_E_STOP_NC=True,
                   DebounceTime=20, CycleTime=20),
              dict(VFD_RUN=False, PUMP_MAINT_DUE=False, PUMP_RUNTIME_ACC="X")),
         )),
]

# ---------------------------------------------------------------- P05
def p05_05():
    """抑制期内的超限信号不得累计；抑制期结束后要重新计满。"""
    deb, soft_on = 60, True
    base = dict(Gap_Exceeded=True, Weld_E_Stop_NC=True, DebounceTime=deb)
    out_f = dict(Operator_Alert=False, Weld_Soft_Start_Active=soft_on)
    r = [{"in": dict(base, Gap_Exceeded=False), "out": dict(out_f)}]
    r += span(249, base, out_f)                                  # 1..249 抑制期
    r.append({"in": dict(base), "out": dict(Operator_Alert="X", Weld_Soft_Start_Active="X")})
    r.append({"in": dict(base), "out": dict(out_f, Weld_Soft_Start_Active=False)})
    # 抖动：恢复一拍清计时，再连续 3 拍才报警
    r.append({"in": dict(base, Gap_Exceeded=False),
              "out": dict(Operator_Alert=False, Weld_Soft_Start_Active=False)})
    r += span(2, dict(base), dict(out_f, Weld_Soft_Start_Active=False))
    r.append({"in": dict(base),
              "out": dict(Operator_Alert="X", Weld_Soft_Start_Active=False)})
    r.append({"in": dict(base),
              "out": dict(Operator_Alert=True, Weld_Soft_Start_Active=False)})
    return dict(case_id="P05-05", refs="K2;K3", category="异常",
                purpose="异常：超限信号在抑制期边界抖动，恢复一拍必须清计时，之后重新计满才报警",
                rows=r)


def p05_06():
    """DebounceTime 下限 1 拍。"""
    base = dict(Gap_Exceeded=False, Weld_E_Stop_NC=True, DebounceTime=20)
    r = [{"in": dict(base), "out": dict(Operator_Alert=False, Weld_Soft_Start_Active=True)}]
    r += span(249, base, dict(Operator_Alert=False, Weld_Soft_Start_Active=True))
    r.append({"in": dict(base), "out": dict(Operator_Alert="X", Weld_Soft_Start_Active="X")})
    g = dict(base, Gap_Exceeded=True)
    r.append({"in": dict(g), "out": dict(Operator_Alert="X", Weld_Soft_Start_Active=False)})
    r.append({"in": dict(g), "out": dict(Operator_Alert=True, Weld_Soft_Start_Active=False)})
    return dict(case_id="P05-06", refs="K2;C5", category="边界",
                purpose="边界：DebounceTime 取下限 1 拍，抑制期结束后第一拍到点、第二拍报警",
                rows=r)


P05 = [p05_05(), p05_06()]

# ---------------------------------------------------------------- P06
def p06_06():
    """急停期间需求一直在，计时冻结；解除后必须重新计满 5 s。"""
    r = [{"in": dict(DO_LOW=False, AERATION_E_STOP_NC=True),
          "out": dict(BLOWER_RUN=False, AERATION_BLOWER_CYCLE_COUNT=0)}]
    r += span(100, dict(DO_LOW=True, AERATION_E_STOP_NC=False),
              dict(BLOWER_RUN=False, AERATION_BLOWER_CYCLE_COUNT=0))
    r += span(249, dict(DO_LOW=True, AERATION_E_STOP_NC=True),
              dict(BLOWER_RUN=False, AERATION_BLOWER_CYCLE_COUNT=0))
    r.append({"in": dict(DO_LOW=True, AERATION_E_STOP_NC=True),
              "out": dict(BLOWER_RUN="X", AERATION_BLOWER_CYCLE_COUNT="X")})
    r.append({"in": dict(DO_LOW=True, AERATION_E_STOP_NC=True),
              "out": dict(BLOWER_RUN=True, AERATION_BLOWER_CYCLE_COUNT=1)})
    return dict(case_id="P06-06", refs="K1;K2;K3", category="异常",
                purpose="异常：急停期间需求持续存在，计时必须冻结；解除后重新计满 5 s 才启动",
                rows=r)


P06 = [p06_06()]

# ---------------------------------------------------------------- P07
P07 = [
    dict(case_id="P07-07", refs="K2;K3", category="异常",
         purpose="异常：自动运行中改写优先级，运行集合必须按新优先级重排且始终恰 3 台",
         rows=[
             {"in": dict(mode=True, start=False, stop=False,
                         priority=[1, 2, 3, 4, 5], selection=[False] * 5),
              "out": dict(run=[False] * 5)},
             {"in": dict(mode=True, start=True, stop=False,
                         priority=[1, 2, 3, 4, 5], selection=[False] * 5),
              "out": dict(run=[False, False, True, True, True])},
             {"in": dict(mode=True, start=True, stop=False,
                         priority=[5, 4, 3, 2, 1], selection=[False] * 5),
              "out": dict(run=[True, True, True, False, False])},
             {"in": dict(mode=True, start=True, stop=False,
                         priority=[1, 1, 1, 1, 1], selection=[False] * 5),
              "out": dict(run=[True, True, True, False, False])},
         ]),
]

# ---------------------------------------------------------------- P09
P09 = [
    dict(case_id="P09-06", refs="K1;K3", category="边界",
         purpose="边界：windowSize 取上限 100，第 99 拍未满、第 100 拍才置 windowSizeReached",
         rows=([{"in": dict(cyclicExecution=False, trigger=False, value=0.0,
                            windowSize=100, reset=False),
                 "out": dict(average=0.0, windowSizeReached=False,
                             error=False, status=0)}]
               + span(99, dict(cyclicExecution=True, trigger=False, value=1.0,
                               windowSize=100, reset=False),
                      dict(average="X", windowSizeReached=False,
                           error=False, status=0))
               + [{"in": dict(cyclicExecution=True, trigger=False, value=1.0,
                              windowSize=100, reset=False),
                   "out": dict(average=1.0, windowSizeReached=True,
                               error=False, status=0)}])),
]

# ---------------------------------------------------------------- P10
P10 = [
    dict(case_id="P10-05", refs="K1;K4", category="边界",
         purpose="边界：温度恰好等于设定值不加热；量程端点 0 与 100 仍判有效",
         rows=rows(
             (dict(TemperatureSensorInput=30.0, SetTemperature=30.0),
              dict(CurrentTemperature=30.0, SetTempDisplay=30.0,
                   HeaterStatus=False, OverheatProtection=False, HeaterOutput=False)),
             (dict(TemperatureSensorInput=29.999, SetTemperature=30.0),
              dict(CurrentTemperature=29.999, SetTempDisplay=30.0,
                   HeaterStatus=True, OverheatProtection=False, HeaterOutput=True)),
             (dict(TemperatureSensorInput=30.0, SetTemperature=30.0),
              dict(CurrentTemperature=30.0, SetTempDisplay=30.0,
                   HeaterStatus=False, OverheatProtection=False, HeaterOutput=False)),
             (dict(TemperatureSensorInput=0.0, SetTemperature=30.0),
              dict(CurrentTemperature=0.0, SetTempDisplay=30.0,
                   HeaterStatus=True, OverheatProtection=False, HeaterOutput=True)),
             (dict(TemperatureSensorInput=100.0, SetTemperature=30.0),
              dict(CurrentTemperature=100.0, SetTempDisplay=30.0,
                   HeaterStatus=False, OverheatProtection=False, HeaterOutput=False)),
         )),
]

# ---------------------------------------------------------------- P11
P11 = [
    dict(case_id="P11-06", refs="K2;K3", category="异常",
         purpose="异常：A 站未到位就按 A 完成按钮，不得推进；到位后同拍才推进",
         rows=rows(
             (dict(Mode=False, ForwardButton=False, ReverseButton=False,
                   SensorA=False, SensorB=False, SensorC=False,
                   ButtonA=False, ButtonB=False, ButtonC=False),
              dict(MotorForward=False, MotorReverse=False, CompletionLight=False)),
             (dict(Mode=True, ForwardButton=False, ReverseButton=False,
                   SensorA=False, SensorB=False, SensorC=False,
                   ButtonA=True, ButtonB=False, ButtonC=False),
              dict(MotorForward=False, MotorReverse=False, CompletionLight=False)),
             (dict(Mode=True, ForwardButton=False, ReverseButton=False,
                   SensorA=True, SensorB=False, SensorC=False,
                   ButtonA=True, ButtonB=False, ButtonC=False),
              dict(MotorForward=True, MotorReverse=False, CompletionLight=False)),
         )),
    dict(case_id="P11-07", refs="K1;C4", category="边界",
         purpose="边界：手动模式正反转按钮同拍有效，两个方向都不得输出；只按正转才动作",
         rows=rows(
             (dict(Mode=False, ForwardButton=False, ReverseButton=False,
                   SensorA=False, SensorB=False, SensorC=False,
                   ButtonA=False, ButtonB=False, ButtonC=False),
              dict(MotorForward=False, MotorReverse=False, CompletionLight=False)),
             (dict(Mode=False, ForwardButton=True, ReverseButton=True,
                   SensorA=False, SensorB=False, SensorC=False,
                   ButtonA=False, ButtonB=False, ButtonC=False),
              dict(MotorForward=False, MotorReverse=False, CompletionLight=False)),
             (dict(Mode=False, ForwardButton=True, ReverseButton=False,
                   SensorA=False, SensorB=False, SensorC=False,
                   ButtonA=False, ButtonB=False, ButtonC=False),
              dict(MotorForward=True, MotorReverse=False, CompletionLight=False)),
         )),
]

# ---------------------------------------------------------------- P12
def p12_06():
    """故障持续两拍：报警保持从最后一次故障起算。"""
    base = dict(THICKNESS_FAULT=False, THICKNESS_SIGNAL_VALID=True,
                CUTTING_RUN=False, FaultTimestamp=100, CycleTime=20)
    ok = dict(THICKNESS_ALARM=False, Slab_Fault_Counter=0,
              Slab_Runtime_Accumulator=0, Slab_Fault_History=[0, 0, 0, 0, 0])
    r = [{"in": dict(base, THICKNESS_FAULT=False, FaultTimestamp=0), "out": ok}]
    r.append({"in": dict(base, THICKNESS_FAULT=True),
              "out": dict(THICKNESS_ALARM=True, Slab_Fault_Counter=1,
                          Slab_Runtime_Accumulator="X",
                          Slab_Fault_History=[100, 0, 0, 0, 0])})
    r.append({"in": dict(base, THICKNESS_FAULT=True),
              "out": dict(THICKNESS_ALARM=True, Slab_Fault_Counter=1,
                          Slab_Runtime_Accumulator="X",
                          Slab_Fault_History=[100, 0, 0, 0, 0])})
    r += span(23, base, dict(THICKNESS_ALARM=True, Slab_Fault_Counter=1,
                             Slab_Runtime_Accumulator="X",
                             Slab_Fault_History=[100, 0, 0, 0, 0]))
    r.append({"in": dict(base), "out": dict(THICKNESS_ALARM="X",
                                            Slab_Fault_Counter=1,
                                            Slab_Runtime_Accumulator="X",
                                            Slab_Fault_History=[100, 0, 0, 0, 0])})
    r.append({"in": dict(base), "out": dict(THICKNESS_ALARM="X",
                                            Slab_Fault_Counter=1,
                                            Slab_Runtime_Accumulator="X",
                                            Slab_Fault_History=[100, 0, 0, 0, 0])})
    r.append({"in": dict(base), "out": dict(THICKNESS_ALARM=False,
                                            Slab_Fault_Counter=1,
                                            Slab_Runtime_Accumulator="X",
                                            Slab_Fault_History=[100, 0, 0, 0, 0])})
    return dict(case_id="P12-06", refs="K3;C5", category="边界",
                purpose="边界：故障恰好持续 2 拍时，报警从最后一拍起保持 500 ms，期满才撤",
                rows=r)


P12 = [p12_06()]

# ---------------------------------------------------------------- P13
P13 = [
    dict(case_id="P13-06", refs="K3;K4;C2", category="异常",
         purpose="异常：模式选择器 4 非法，修正值未定义（X）；夜间模式 3 修正恒 +4 且不启风机",
         rows=[
             {"in": dict(OCCUPANCY_DETECTED=True, ENERGY_SAVING_MODE=False,
                         HVAC_MODE_SELECTOR=4),
              "out": dict(SUPPLY_FAN_RUN=False, TEMP_SETPOINT_ADJUST="X")},
             {"in": dict(OCCUPANCY_DETECTED=True, ENERGY_SAVING_MODE=False,
                         HVAC_MODE_SELECTOR=4),
              "out": dict(SUPPLY_FAN_RUN=False, TEMP_SETPOINT_ADJUST="X")},
             {"in": dict(OCCUPANCY_DETECTED=True, ENERGY_SAVING_MODE=False,
                         HVAC_MODE_SELECTOR=3),
              "out": dict(SUPPLY_FAN_RUN=False, TEMP_SETPOINT_ADJUST=4)},
         ]),
]

# ---------------------------------------------------------------- P15
P15 = [
    dict(case_id="P15-07", refs="K1;C1", category="异常",
         purpose="异常：急停期间按启动按钮一律无效；解除后新的上升沿也不得自动恢复",
         rows=rows(
             (dict(estop=True, opeMode=True, levelSensor=0, processMode=False,
                   mixMotorComplete=False, valveAStart=False, valveBStart=False,
                   valveCStart=False, valveDStart=False, mixMotorStart=False,
                   autoStart=False),
              dict(valveARun=False, valveBRun=False, valveCRun=False,
                   valveDRun=False, mixMotorRun=False)),
             (dict(estop=False, opeMode=True, levelSensor=0, processMode=False,
                   mixMotorComplete=False, valveAStart=True, valveBStart=False,
                   valveCStart=False, valveDStart=False, mixMotorStart=False,
                   autoStart=False),
              dict(valveARun=True, valveBRun=False, valveCRun=False,
                   valveDRun=False, mixMotorRun=False)),
             (dict(estop=False, opeMode=True, levelSensor=0, processMode=False,
                   mixMotorComplete=False, valveAStart=True, valveBStart=False,
                   valveCStart=False, valveDStart=False, mixMotorStart=False,
                   autoStart=False),
              dict(valveARun=True, valveBRun=False, valveCRun=False,
                   valveDRun=False, mixMotorRun=False)),
             (dict(estop=True, opeMode=True, levelSensor=0, processMode=False,
                   mixMotorComplete=False, valveAStart=True, valveBStart=False,
                   valveCStart=False, valveDStart=False, mixMotorStart=False,
                   autoStart=False),
              dict(valveARun=False, valveBRun=False, valveCRun=False,
                   valveDRun=False, mixMotorRun=False)),
             (dict(estop=True, opeMode=True, levelSensor=0, processMode=False,
                   mixMotorComplete=False, valveAStart=False, valveBStart=False,
                   valveCStart=False, valveDStart=False, mixMotorStart=False,
                   autoStart=False),
              dict(valveARun=False, valveBRun=False, valveCRun=False,
                   valveDRun=False, mixMotorRun=False)),
             (dict(estop=True, opeMode=True, levelSensor=0, processMode=False,
                   mixMotorComplete=False, valveAStart=True, valveBStart=False,
                   valveCStart=False, valveDStart=False, mixMotorStart=False,
                   autoStart=False),
              dict(valveARun=False, valveBRun=False, valveCRun=False,
                   valveDRun=False, mixMotorRun=False)),
         )),
]

# ---------------------------------------------------------------- P16
P16 = [
    dict(case_id="P16-07", refs="K2;K3", category="异常",
         purpose="异常：非目标工位的到位+完成信号同时有效，不得启动输送；目标工位到了才动",
         rows=rows(
             (dict(processLength=4, processSequence=[2, 3, 4, 5],
                   sensor1=False, sensor2=False, sensor3=False,
                   sensor4=False, sensor5=False, station1Start=False,
                   station2Complete=False, station3Complete=False,
                   station4Complete=False),
              dict(conveyorLeft=False, conveyorRight=False)),
             (dict(processLength=4, processSequence=[2, 3, 4, 5],
                   sensor1=False, sensor2=False, sensor3=True,
                   sensor4=False, sensor5=False, station1Start=False,
                   station2Complete=False, station3Complete=True,
                   station4Complete=False),
              dict(conveyorLeft=False, conveyorRight=False)),
             (dict(processLength=4, processSequence=[2, 3, 4, 5],
                   sensor1=False, sensor2=True, sensor3=False,
                   sensor4=False, sensor5=False, station1Start=False,
                   station2Complete=True, station3Complete=False,
                   station4Complete=False),
              dict(conveyorLeft=False, conveyorRight=True)),
         )),
    dict(case_id="P16-08", refs="K1;K4", category="边界",
         purpose="边界：processLength 取数组上界 8 合法，第 1 个工位到位即可右行",
         rows=rows(
             (dict(processLength=8, processSequence=[1, 2, 3, 4, 5, 1, 2, 3],
                   sensor1=False, sensor2=False, sensor3=False,
                   sensor4=False, sensor5=False, station1Start=False,
                   station2Complete=False, station3Complete=False,
                   station4Complete=False),
              dict(conveyorLeft=False, conveyorRight=False)),
             (dict(processLength=8, processSequence=[1, 2, 3, 4, 5, 1, 2, 3],
                   sensor1=True, sensor2=False, sensor3=False,
                   sensor4=False, sensor5=False, station1Start=True,
                   station2Complete=False, station3Complete=False,
                   station4Complete=False),
              dict(conveyorLeft=False, conveyorRight=True)),
         )),
]

# ---------------------------------------------------------------- P17
P17 = [
    dict(case_id="P17-08", refs="K1;K4", category="边界",
         purpose="边界：库中只剩 1 个空位时新增成功；写满后再新增报 16#8003",
         rows=[
             {"in": dict(addRecipe=False, deleteRecipe=False, modifyRecipe=False,
                         queryRecipe=False,
                         recipeIn=dict(recipeID=0, ingredientType=0,
                                       ingredientRatio=0.0,
                                       productionTemperature=0.0),
                         recipe_ids=[1, 2, 3, 4, 5, 6, 7, 8, 9, 0],
                         recipe_types=[10, 20, 0, 0, 0, 0, 0, 0, 0, 0],
                         recipe_ratios=[0.5, 0.3, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                         recipe_temps=[100.0, 120.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]),
              "out": dict(recipeAdded=False, recipeDeleted=False,
                          recipeModified=False, recipeQueryResult="X",
                          error=False, status=0)},
             {"in": dict(addRecipe=True, deleteRecipe=False, modifyRecipe=False,
                         queryRecipe=False,
                         recipeIn=dict(recipeID=10, ingredientType=30,
                                       ingredientRatio=0.4,
                                       productionTemperature=150.0),
                         recipe_ids=[1, 2, 3, 4, 5, 6, 7, 8, 9, 0],
                         recipe_types=[10, 20, 0, 0, 0, 0, 0, 0, 0, 0],
                         recipe_ratios=[0.5, 0.3, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                         recipe_temps=[100.0, 120.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]),
              "out": dict(recipeAdded=True, recipeDeleted=False,
                          recipeModified=False, recipeQueryResult="X",
                          error=False, status=0)},
             {"in": dict(addRecipe=True, deleteRecipe=False, modifyRecipe=False,
                         queryRecipe=False,
                         recipeIn=dict(recipeID=11, ingredientType=30,
                                       ingredientRatio=0.4,
                                       productionTemperature=150.0),
                         recipe_ids=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
                         recipe_types=[10, 20, 0, 0, 0, 0, 0, 0, 0, 30],
                         recipe_ratios=[0.5, 0.3, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.4],
                         recipe_temps=[100.0, 120.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 150.0]),
              "out": dict(recipeAdded=False, recipeDeleted=False,
                          recipeModified=False, recipeQueryResult="X",
                          error=True, status=0x8003)},
         ]),
]

# ---------------------------------------------------------------- P18
def p18_08():
    r = [{"in": dict(enqueue=False, dequeue=False, reset=False, item=42,
                     buffer=[0, 0, 0, 0, 0]),
          "out": dict(elementCount=0, status=0)}]
    for i in range(1, 10):                      # 1..9 交替入队到 5
        enq = (i % 2 == 1)
        cnt = (i + 1) // 2
        r.append({"in": dict(enqueue=enq, dequeue=False, reset=False,
                             item=42, buffer=[0, 0, 0, 0, 0]),
                  "out": dict(elementCount=cnt, status=0)})
    r.append({"in": dict(enqueue=False, dequeue=True, reset=False, item=42,
                         buffer=[0, 0, 0, 0, 0]),
              "out": dict(elementCount=4, status=0)})
    r.append({"in": dict(enqueue=True, dequeue=False, reset=False, item=42,
                         buffer=[0, 0, 0, 0, 0]),
              "out": dict(elementCount=5, status=0)})
    r.append({"in": dict(enqueue=False, dequeue=False, reset=False, item=42,
                         buffer=[0, 0, 0, 0, 0]),
              "out": dict(elementCount=5, status=0)})
    r.append({"in": dict(enqueue=True, dequeue=False, reset=False, item=42,
                         buffer=[0, 0, 0, 0, 0]),
              "out": dict(elementCount=5, status=0x8002)})
    return dict(case_id="P18-08", refs="K3;K4", category="边界",
                purpose="边界：队列满时出队腾出一位后可再入队；满队列再入队报 16#8002",
                rows=r)


P18 = [p18_08()]

# ---------------------------------------------------------------- P19
# 急停极性按原始 I/O 表：EmergencyStop = FALSE 为急停触发，TRUE 为正常。
# K4/C1/C2 目前按 TRUE 写，属规约缺陷（A-47），待成员1 修正。
P19 = [
    dict(case_id="P19-08", refs="K4;K1;C1", category="异常",
         purpose="异常：急停（EmergencyStop=FALSE）期间按方向按钮无动作；正常态（TRUE）按同一按钮会动",
         rows=[
             {"in": dict(EmergencyStop=False), "out": dict(MoveDown=False, MoveUp=False,
                                                           MoveLeft=False, MoveRight=False,
                                                           ActivateGrip=False,
                                                           ActivateRelease=False)},
             {"in": dict(EmergencyStop=False, DownButton=True),
              "out": dict(MoveDown=False, MoveUp=False, MoveLeft=False,
                          MoveRight=False, ActivateGrip=False,
                          ActivateRelease=False)},
             {"in": dict(EmergencyStop=False, DownButton=False, UpButton=True),
              "out": dict(MoveDown=False, MoveUp=False, MoveLeft=False,
                          MoveRight=False, ActivateGrip=False,
                          ActivateRelease=False)},
             {"in": dict(EmergencyStop=True, DownButton=True, UpButton=False),
              "out": dict(MoveDown=True, MoveUp=False, MoveLeft=False,
                          MoveRight=False, ActivateGrip=False,
                          ActivateRelease=False)},
             {"in": dict(EmergencyStop=True, DownButton=False, UpButton=False),
              "out": dict(MoveDown=False, MoveUp=False, MoveLeft=False,
                          MoveRight=False, ActivateGrip=False,
                          ActivateRelease=False)},
         ]),
    dict(case_id="P19-09", refs="K3", category="边界",
         purpose="边界：单步模式 Start 按住不放只推进一步，必须松开再按才执行下一个动作",
         rows=[
             {"in": dict(SingleStepMode=True, EmergencyStop=True, Start=False),
              "out": dict(MoveDown=False, MoveUp=False, MoveLeft=False,
                          MoveRight=False, ActivateGrip=False,
                          ActivateRelease=False)},
             {"in": dict(SingleStepMode=True, EmergencyStop=True, Start=True),
              "out": dict(MoveDown=True, MoveUp=False, MoveLeft=False,
                          MoveRight=False, ActivateGrip=False,
                          ActivateRelease=False)},
             {"in": dict(SingleStepMode=True, EmergencyStop=True, Start=True),
              "out": dict(MoveDown=True, MoveUp=False, MoveLeft=False,
                          MoveRight=False, ActivateGrip=False,
                          ActivateRelease=False)},
             {"in": dict(SingleStepMode=True, EmergencyStop=True, Start=False,
                         DownLimitSwitch=True),
              "out": dict(MoveDown=False, MoveUp=False, MoveLeft=False,
                          MoveRight=False, ActivateGrip=False,
                          ActivateRelease=False)},
             {"in": dict(SingleStepMode=True, EmergencyStop=True, Start=True,
                         DownLimitSwitch=True),
              "out": dict(MoveDown=False, MoveUp=False, MoveLeft=False,
                          MoveRight=False, ActivateGrip=True,
                          ActivateRelease=False)},
         ]),
]

# ---------------------------------------------------------------- P20
P20 = [
    dict(case_id="P20-08", refs="K3", category="异常",
         purpose="异常：称重读数 0（空秤/断线），判不合格并输出 kick，不得去烧成",
         rows=[
             {"in": dict(Mode=True, weight=True, w=0.0),
              "out": dict(MotorForward=False, MotorReverse=False, kick=True,
                          CompletionLight=False, firingTemp="X")},
             {"in": dict(Mode=True, weight=True, w=0.0),
              "out": dict(MotorForward=False, MotorReverse=False, kick=True,
                          CompletionLight=False, firingTemp="X")},
         ]),
]

# ---------------------------------------------------------------- S01
S01 = [
    dict(case_id="S01-06", refs="K3", category="边界",
         purpose="边界：无件时按下的 Start 边沿被消耗，随后有件但不松手不得夹紧，必须重新按",
         rows=rows(
             (dict(StartBtn=False, LeftPartPresent=False, RightPartPresent=False,
                   EStop_NC=True),
              dict(ClampLeft=False, ClampRight=False, Busy=False, Status=0)),
             (dict(StartBtn=True, LeftPartPresent=False, RightPartPresent=False,
                   EStop_NC=True),
              dict(ClampLeft=False, ClampRight=False, Busy=False, Status=0)),
             (dict(StartBtn=True, LeftPartPresent=True, RightPartPresent=False,
                   EStop_NC=True),
              dict(ClampLeft=False, ClampRight=False, Busy=False, Status=0)),
             (dict(StartBtn=False, LeftPartPresent=True, RightPartPresent=False,
                   EStop_NC=True),
              dict(ClampLeft=False, ClampRight=False, Busy=False, Status=0)),
             (dict(StartBtn=True, LeftPartPresent=True, RightPartPresent=False,
                   EStop_NC=True),
              dict(ClampLeft=True, ClampRight=False, Busy=True, Status=0)),
         )),
]

# ---------------------------------------------------------------- S02
def s02_06():
    r = [{"in": dict(FwdBtn=False, RevBtn=False, MaintKey=False, EStop_NC=True),
          "out": dict(MotorFwd=False, MotorRev=False, RunLamp=False, Status=0)}]
    r.append({"in": dict(FwdBtn=True, RevBtn=False, MaintKey=False, EStop_NC=True),
              "out": dict(MotorFwd=True, MotorRev=False, RunLamp=True, Status=0)})
    r.append({"in": dict(FwdBtn=False, RevBtn=True, MaintKey=False, EStop_NC=True),
              "out": dict(MotorFwd=False, MotorRev=False, RunLamp=True, Status=0x8203)})
    r += span(8, dict(FwdBtn=False, RevBtn=True, MaintKey=False, EStop_NC=True),
              dict(MotorFwd=False, MotorRev=False, RunLamp=True, Status=0x8203))
    r.append({"in": dict(FwdBtn=False, RevBtn=True, MaintKey=False, EStop_NC=True),
              "out": dict(MotorFwd=False, MotorRev="X", RunLamp=True, Status="X")})
    r.append({"in": dict(FwdBtn=False, RevBtn=True, MaintKey=False, EStop_NC=True),
              "out": dict(MotorFwd=False, MotorRev=True, RunLamp=True, Status=0)})
    return dict(case_id="S02-06", refs="K2", category="边界",
                purpose="边界：换向死区恰好满 200 ms（10 拍）才允许反转，第 10 拍仍是边界",
                rows=r)


S02 = [s02_06()]

# ---------------------------------------------------------------- S04
S04 = [
    dict(case_id="S04-06", refs="K3;C7", category="边界",
         purpose="边界：偏差恰好 ±200 不报警、201 报警；回落到 150 仍保持、149 才撤警",
         rows=rows(
             (dict(RawWeight=0, ZeroBtn=False, CalibWeight=0.0),
              dict(CompensatedWeight=0.0, ZeroOffset=0, DriftAlarm=False, Status=0)),
             (dict(RawWeight=200, ZeroBtn=False, CalibWeight=0.0),
              dict(CompensatedWeight=2.0, ZeroOffset=0, DriftAlarm=False, Status=0)),
             (dict(RawWeight=201, ZeroBtn=False, CalibWeight=0.0),
              dict(CompensatedWeight=2.01, ZeroOffset=0, DriftAlarm=True, Status=0x8401)),
             (dict(RawWeight=150, ZeroBtn=False, CalibWeight=0.0),
              dict(CompensatedWeight=1.5, ZeroOffset=0, DriftAlarm=True, Status=0x8401)),
             (dict(RawWeight=149, ZeroBtn=False, CalibWeight=0.0),
              dict(CompensatedWeight=1.49, ZeroOffset=0, DriftAlarm=False, Status=0)),
         )),
]

# ---------------------------------------------------------------- S05
S05 = [
    dict(case_id="S05-06", refs="K1;K2", category="边界",
         purpose="边界：ShiftReset 与脉冲上升沿同拍，总量仍 +0.5，当班量与计数顺序未定义（X）",
         rows=rows(
             (dict(FlowPulse=False, ShiftReset=False, CycleTime=20),
              dict(TotalVolume=0.0, ShiftVolume=0.0, PulseCount=0,
                   OverflowFlag=False, Status=0)),
             (dict(FlowPulse=True, ShiftReset=False, CycleTime=20),
              dict(TotalVolume=0.5, ShiftVolume=0.5, PulseCount=1,
                   OverflowFlag=False, Status=0)),
             (dict(FlowPulse=True, ShiftReset=True, CycleTime=20),
              dict(TotalVolume=1.0, ShiftVolume="X", PulseCount="X",
                   OverflowFlag=False, Status=0)),
         )),
]

# ---------------------------------------------------------------- S07
def s07_05():
    return dict(case_id="S07-05", refs="K1;C10", category="正常",
                purpose="正常：未按启动或没有瓶时保持空闲，步号与计数都不动",
                rows=rows(
                    (dict(BottleIn=False, FillDone=False, CapDone=False,
                          PackDone=False, StartBtn=False, EStop_NC=True),
                     dict(Conveyor=False, FillValve=False, CapMotor=False,
                          PackCyl=False, CycleCount=0, Status=0)),
                    (dict(BottleIn=False, FillDone=False, CapDone=False,
                          PackDone=False, StartBtn=True, EStop_NC=True),
                     dict(Conveyor=False, FillValve=False, CapMotor=False,
                          PackCyl=False, CycleCount=0, Status=0)),
                    (dict(BottleIn=False, FillDone=False, CapDone=False,
                          PackDone=False, StartBtn=False, EStop_NC=True),
                     dict(Conveyor=False, FillValve=False, CapMotor=False,
                          PackCyl=False, CycleCount=0, Status=0)),
                ))


def s07_06():
    """灌装在超时前一拍完成：必须推进，不得报 16#8701。"""
    r = [{"in": dict(BottleIn=False, FillDone=False, CapDone=False,
                     PackDone=False, StartBtn=False, EStop_NC=True),
          "out": dict(Conveyor=False, FillValve=False, CapMotor=False,
                      PackCyl=False, CycleCount=0, Status=0)}]
    r.append({"in": dict(BottleIn=False, FillDone=False, CapDone=False,
                         PackDone=False, StartBtn=True, EStop_NC=True),
              "out": dict(Conveyor=True, FillValve=False, CapMotor=False,
                          PackCyl=False, CycleCount=0, Status=0)})
    r.append({"in": dict(BottleIn=True, FillDone=False, CapDone=False,
                         PackDone=False, StartBtn=False, EStop_NC=True),
              "out": dict(Conveyor=False, FillValve=True, CapMotor=False,
                          PackCyl=False, CycleCount=0, Status=0)})
    r += span(246, dict(BottleIn=True, FillDone=False, CapDone=False,
                        PackDone=False, StartBtn=False, EStop_NC=True),
              dict(Conveyor=False, FillValve=True, CapMotor=False,
                   PackCyl=False, CycleCount=0, Status=0))
    r.append({"in": dict(BottleIn=True, FillDone=True, CapDone=False,
                         PackDone=False, StartBtn=False, EStop_NC=True),
              "out": dict(Conveyor=False, FillValve=False, CapMotor=True,
                          PackCyl=False, CycleCount=0, Status=0)})
    return dict(case_id="S07-06", refs="K2;K3", category="边界",
                purpose="边界：灌装在超时前完成，必须推进到封盖且不得报 16#8701",
                rows=r)


S07 = [s07_05(), s07_06()]

# ---------------------------------------------------------------- S08
S08 = [
    dict(case_id="S08-05", refs="K3", category="边界",
         purpose="边界：RecipeSelect 取非法下界 0，ActiveRecipe 不变，Status = 16#8801",
         rows=rows(
             (dict(RecipeSelect=1, ChangeoverReq=False, PartHeight=0.0, EStop_NC=True),
              dict(ActiveRecipe=1, SortLeft=False, SortRight=False,
                   Busy=False, Status=0)),
             (dict(RecipeSelect=0, ChangeoverReq=True, PartHeight=0.0, EStop_NC=True),
              dict(ActiveRecipe=1, SortLeft=False, SortRight=False,
                   Busy=False, Status=0x8801)),
         )),
]

# ---------------------------------------------------------------- S09
S09 = [
    dict(case_id="S09-05", refs="K1", category="异常",
         purpose="异常：未启动时按 StepDone 不得开始步序，阀门与泵保持全 FALSE",
         rows=rows(
             (dict(StartCIP=False, StepDone=False, EStop_NC=True),
              dict(WaterValve=False, LyeValve=False, RinseValve=False,
                   PumpRun=False, StepNo=0, Status=0)),
             (dict(StartCIP=False, StepDone=True, EStop_NC=True),
              dict(WaterValve=False, LyeValve=False, RinseValve=False,
                   PumpRun=False, StepNo=0, Status=0)),
             (dict(StartCIP=False, StepDone=False, EStop_NC=True),
              dict(WaterValve=False, LyeValve=False, RinseValve=False,
                   PumpRun=False, StepNo=0, Status=0)),
         )),
    dict(case_id="S09-06", refs="K1;K4", category="边界",
         purpose="边界：StepDone 保持为电平只推进一步，必须松开再按才进入下一步",
         rows=rows(
             (dict(StartCIP=False, StepDone=False, EStop_NC=True),
              dict(WaterValve=False, LyeValve=False, RinseValve=False,
                   PumpRun=False, StepNo=0, Status=0)),
             (dict(StartCIP=True, StepDone=False, EStop_NC=True),
              dict(WaterValve=True, LyeValve=False, RinseValve=False,
                   PumpRun=True, StepNo=1, Status=0)),
             (dict(StartCIP=False, StepDone=True, EStop_NC=True),
              dict(WaterValve=False, LyeValve=True, RinseValve=False,
                   PumpRun=True, StepNo=2, Status=0)),
             (dict(StartCIP=False, StepDone=True, EStop_NC=True),
              dict(WaterValve=False, LyeValve=True, RinseValve=False,
                   PumpRun=True, StepNo=2, Status=0)),
             (dict(StartCIP=False, StepDone=False, EStop_NC=True),
              dict(WaterValve=False, LyeValve=True, RinseValve=False,
                   PumpRun=True, StepNo=2, Status=0)),
             (dict(StartCIP=False, StepDone=True, EStop_NC=True),
              dict(WaterValve=False, LyeValve=False, RinseValve=True,
                   PumpRun=True, StepNo=3, Status=0)),
         )),
]

# ---------------------------------------------------------------- S10
S10 = [
    dict(case_id="S10-06", refs="K2;K3", category="边界",
         purpose="边界：复位按住不放时出现新的重故障，必须重新跳闸（复位不屏蔽新故障）",
         rows=rows(
             (dict(VFDFaultCode=0, VFDRun=True, ResetBtn=False),
              dict(AlarmLamp=False, TripOutput=False, Status=0)),
             (dict(VFDFaultCode=2, VFDRun=True, ResetBtn=False),
              dict(AlarmLamp=True, TripOutput=True, Status=2)),
             (dict(VFDFaultCode=0, VFDRun=True, ResetBtn=True),
              dict(AlarmLamp=False, TripOutput=False, Status=0)),
             (dict(VFDFaultCode=2, VFDRun=True, ResetBtn=True),
              dict(AlarmLamp=True, TripOutput=True, Status=2)),
         )),
]

# ---------------------------------------------------------------- S11
S11 = [
    dict(case_id="S11-05", refs="K1", category="边界",
         purpose="边界：断线判据恰好 3.6 mA 仍有效、3.59 判断线；回到 3.8 才恢复",
         rows=rows(
             (dict(SensorCurrent=12.0, FallbackValue=80.0),
              dict(SensorValid="X", DegradedMode=False, ControlValue="X",
                   AlarmLamp=False, Status=0)),
             (dict(SensorCurrent=3.6, FallbackValue=80.0),
              dict(SensorValid=True, DegradedMode=False, ControlValue="X",
                   AlarmLamp=False, Status=0)),
             (dict(SensorCurrent=3.59, FallbackValue=80.0),
              dict(SensorValid=False, DegradedMode=False, ControlValue="X",
                   AlarmLamp="X", Status=0)),
             (dict(SensorCurrent=3.8, FallbackValue=80.0),
              dict(SensorValid=True, DegradedMode=False, ControlValue="X",
                   AlarmLamp=False, Status=0)),
         )),
]

# ---------------------------------------------------------------- S12
def s12_05():
    r = [{"in": dict(EStop_NC=True, ResetBtn=False, StartBtn=False, DoorClosed=True),
          "out": dict(MachineRun=False, ShiftCount=0, AlarmLamp=False, Status=0)}]
    r.append({"in": dict(EStop_NC=True, ResetBtn=False, StartBtn=True, DoorClosed=True),
              "out": dict(MachineRun=True, ShiftCount=0, AlarmLamp=False, Status=0)})
    r += span(2998, dict(EStop_NC=True, ResetBtn=False, StartBtn=False, DoorClosed=True),
              dict(MachineRun=True, ShiftCount=0, AlarmLamp=False, Status=0))
    r.append({"in": dict(EStop_NC=False, ResetBtn=False, StartBtn=False, DoorClosed=True),
              "out": dict(MachineRun=False, ShiftCount=0, AlarmLamp=True, Status=0x8B01)})
    return dict(case_id="S12-05", refs="K1;K4", category="边界",
                purpose="边界：运行满 60 s 的当拍发生急停，ShiftCount 不得加 1（急停优先）",
                rows=r)


S12 = [s12_05()]

# ---------------------------------------------------------------- S13
def s13_06():
    """有料 150 拍切高速；无料 250 拍才回落低速。"""
    base_on = dict(line=True, merge_part=False, main_part=True, jam=False,
                   reset=False, mode_auto=True)
    base_off = dict(line=True, merge_part=False, main_part=False, jam=False,
                    reset=False, mode_auto=True)
    out_on = dict(main=True, merge=True, high=False, alarm=False, status=0)
    out_high = dict(main=True, merge=True, high=True, alarm=False, status=0)
    r = [{"in": dict(line=False, merge_part=False, main_part=False, jam=False,
                     reset=False, mode_auto=True),
          "out": dict(main=False, merge=False, high=False, alarm=False, status=0)}]
    r.append({"in": dict(line=True, merge_part=False, main_part=False, jam=False,
                         reset=False, mode_auto=True),
              "out": dict(main=True, merge=True, high=False, alarm=False, status=0)})
    r += span(149, base_on, out_on)                       # 2..150 有料
    r.append({"in": dict(base_on), "out": dict(out_on, high="X")})
    r.append({"in": dict(base_on), "out": dict(out_high)})
    r += span(248, base_off, out_high)                    # 无料 248 拍仍高速
    r.append({"in": dict(base_off), "out": dict(out_high, high="X")})
    r.append({"in": dict(base_off), "out": dict(out_on)})
    return dict(case_id="S13-06", refs="K5;C7", category="边界",
                purpose="边界：无料满 5 s（250 拍）才回落低速；中间 249 拍必须保持高速",
                rows=r)


S13 = [s13_06()]

# ---------------------------------------------------------------- S14
S14 = [
    dict(case_id="S14-06", refs="K1;K2", category="边界",
         purpose="边界：压力恰好 160.0 不卸荷、160.1 卸荷；恰好 120.0 不加载、119.9 加载",
         rows=rows(
             (dict(Pressure=100.0, PumpEnable=True, ResetBtn=False),
              dict(LowPump=True, HighPump=False, ReliefValve=False,
                   AlarmLamp=False, Status=0)),
             (dict(Pressure=160.0, PumpEnable=True, ResetBtn=False),
              dict(LowPump=True, HighPump=False, ReliefValve=False,
                   AlarmLamp=False, Status=0)),
             (dict(Pressure=160.1, PumpEnable=True, ResetBtn=False),
              dict(LowPump=False, HighPump=False, ReliefValve=True,
                   AlarmLamp=False, Status=0)),
             (dict(Pressure=120.0, PumpEnable=True, ResetBtn=False),
              dict(LowPump=False, HighPump=False, ReliefValve=False,
                   AlarmLamp=False, Status=0)),
             (dict(Pressure=119.9, PumpEnable=True, ResetBtn=False),
              dict(LowPump=True, HighPump=False, ReliefValve=False,
                   AlarmLamp=False, Status=0)),
         )),
]

EXTRA = {
    "P01": P01, "P04": P04, "P05": P05, "P06": P06, "P07": P07, "P09": P09,
    "P10": P10, "P11": P11, "P12": P12, "P13": P13, "P15": P15, "P16": P16,
    "P17": P17, "P18": P18, "P19": P19, "P20": P20,
    "S01": S01, "S02": S02, "S04": S04, "S05": S05, "S07": S07, "S08": S08,
    "S09": S09, "S10": S10, "S11": S11, "S12": S12, "S13": S13, "S14": S14,
}

# 只改类别与目的文本的既有用例（不新增行）
RECATEGORIZE = {
    "P02": {"P02-05": ("异常", "异常：上电首拍输入就非零（输入卡在上电值），不得报边沿")},
    "S05": {"S05-05": ("异常", "异常：单周期两次脉冲需要输入层支持，本 CSV 只能记录不可判定")},
}


def _io(task):
    import json
    fx = json.loads((FIX / ("%s.io.json" % task)).read_text(encoding="utf-8"))
    ins = [r["name"] for r in fx["io"] if r["direction"] == "IN"]
    outs = [r["name"] for r in fx["io"] if r["direction"] == "OUT"]
    types = {r["name"]: r["type"] for r in fx["io"]}
    return ins, outs, types


def _default(typ):
    """按 IEC 类型给缺省值（只用于没写到的列）。"""
    if typ == "BOOL":
        return False
    if typ.startswith("ARRAY"):
        import re
        m = re.search(r"ARRAY\[(\d+)\.\.(\d+)\]", typ)
        n = (int(m.group(2)) - int(m.group(1)) + 1) if m else 0
        et = typ.split(" OF ", 1)[1]
        return [_default(et)] * n
    if typ in ("REAL", "LREAL"):
        return 0.0
    if typ in ("TIME", "LTIME"):
        return 0
    if typ == "VARIANT":
        return 0
    if typ.startswith("STRING"):
        return ""
    if typ.startswith("ST_"):
        return {}
    return 0


def _read(path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        return reader.fieldnames, list(reader)


def _write(path, header, rows_):
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=header)
        w.writeheader()
        w.writerows(rows_)


def apply_task(task):
    path = CASES / ("%s.csv" % task)
    header, old = _read(path)
    ins, outs, types = _io(task)
    alias = ALIAS.get(task, {})
    base = BASE.get(task, {})
    new_ids = {c["case_id"] for c in EXTRA.get(task, [])}
    kept = [r for r in old if r["case_id"] not in new_ids]

    for cid, (cat, purpose) in RECATEGORIZE.get(task, {}).items():
        for r in kept:
            if r["case_id"] == cid and r["cycle"] == "0":
                r["category"] = cat
                r["purpose"] = purpose

    added = []
    for case in EXTRA.get(task, []):
        prev_in = {n: _default(types[n]) for n in ins}
        prev_in.update(base)
        prev_out = {n: _default(types[n]) for n in outs}
        for i, row in enumerate(case["rows"]):
            head = (i == 0)
            cur_in = dict(prev_in)
            cur_in.update({alias.get(k, k): v for k, v in row["in"].items()})
            cur_out = dict(prev_out)
            cur_out.update({alias.get(k, k): v for k, v in row["out"].items()})
            added.append({
                "case_id": case["case_id"],
                "cycle": i,
                "spec_refs": case["refs"] if head else "",
                "purpose": case["purpose"] if head else "",
                "category": case["category"] if head else "",
                **{k: fmt(cur_in[k], types[k]) for k in ins},
                **{k: fmt(cur_out[k], types[k]) for k in outs},
            })
            prev_in, prev_out = cur_in, cur_out

    _write(path, header, kept + added)
    return len(EXTRA.get(task, [])), len(added)


def main():
    n_case = n_row = 0
    for task in sorted(set(EXTRA) | set(RECATEGORIZE)):
        c, r = apply_task(task)
        n_case += c
        n_row += r
        print("%-4s +%d 条 / %d 行" % (task, c, r))
    print("合计新增 %d 条用例 / %d 行" % (n_case, n_row))
    return 0


if __name__ == "__main__":
    sys.exit(main())

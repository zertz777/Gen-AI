"""生成 P13（办公楼 HVAC 节能控制）的用例。

30 s 启动延时 = 1500 拍，手写不现实。
条件成立满 30 s 的那一拍写 X（"满 30 s"算不算已启动未定义），下一拍起判定。
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from _emit import Case, write_cases  # noqa: E402

TESTS = HERE.parent
FX = TESTS / "cases" / "_fixtures" / "P13.io.json"
OUT = TESTS / "cases" / "P13.csv"

DELAY_30S = 1500   # 30 s ÷ 20 ms

AUTO, COMFORT, ECONOMY, NIGHT = 0, 1, 2, 3


def io(occ, mode, es, fan, adj):
    return ({"OCCUPANCY_DETECTED": occ, "ENERGY_SAVING_MODE": es,
             "HVAC_MODE_SELECTOR": mode},
            {"SUPPLY_FAN_RUN": fan, "TEMP_SETPOINT_ADJUST": adj})


def xio(occ, mode, es):
    """边界拍：只把风机状态标 X，温度修正仍确定。"""
    adj = adjust(occ, mode, es)
    return ({"OCCUPANCY_DETECTED": occ, "ENERGY_SAVING_MODE": es,
             "HVAC_MODE_SELECTOR": mode},
            {"SUPPLY_FAN_RUN": "X", "TEMP_SETPOINT_ADJUST": adj})


def adjust(occ, mode, es):
    """K3 的温度修正表；夜间恒 +4，节能开关只影响自动模式。"""
    if mode == NIGHT:
        return 4
    if occ:
        return 0
    if mode == AUTO:
        return 3 if es else 2
    if mode == COMFORT:
        return 1
    if mode == ECONOMY:
        return 4
    return "X"          # 非法模式，需求未定义（"callers supply a valid value"）


def to(c, n, ins, outs):
    """把用例铺到第 n 拍之前（即下一拍编号为 n）。"""
    while len(c.rows) < n:
        c.add(ins, outs)
    return c


def case_01():
    """正常 30 s 延时启动（舒适模式）。"""
    c = Case("P13-01", "K1;C2;C10",
             "占用且非夜间模式下满 30 s 才启动风机；上电首拍输出为初值")
    c.add(*io(True, COMFORT, False, False, 0))              # 0 初态
    to(c, DELAY_30S, *io(True, COMFORT, False, False, 0))   # 1..1499 计时中
    c.add(*xio(True, COMFORT, False))                       # 1500 满 30 s 边界
    c.span(10, *io(True, COMFORT, False, True, 0))          # 1501..1510 启动
    return c


def case_02():
    """占用丢失立即停风机并复位延时，恢复后必须重新计满 30 s。"""
    c = Case("P13-02", "K2;C3;C6",
             "占用丢失当拍停风机并复位计时；占用恢复后须重新计满 30 s")
    c.add(*io(True, ECONOMY, False, False, 0))              # 0
    to(c, 21, *io(True, ECONOMY, False, False, 0))          # 1..20 只计了 20 拍
    c.add(*io(False, ECONOMY, False, False, 4))             # 21 占用丢失，立即停
    to(c, 41, *io(False, ECONOMY, False, False, 4))         # 22..40 空置
    to(c, 41 + DELAY_30S - 1, *io(True, ECONOMY, False, False, 0))   # 41..1539 重新计时
    c.add(*xio(True, ECONOMY, False))                       # 1540 满 30 s 边界
    c.span(5, *io(True, ECONOMY, False, True, 0))           # 1541..1545
    return c


def case_03():
    """夜间模式不启动风机，温度修正恒 +4。"""
    c = Case("P13-03", "K1;K3;C2",
             "夜间模式即使有占用也不启动风机，修正恒为 +4")
    c.add(*io(True, NIGHT, False, False, 0))                # 0
    c.span(30, *io(True, NIGHT, False, False, 4))           # 1..30 一直不启动
    c.span(10, *io(False, NIGHT, True, False, 4))           # 31..40 空置同样 +4
    return c


def case_04():
    """温度修正表全覆盖：模式 × 占用 × 节能。"""
    c = Case("P13-04", "K3;K4;C4",
             "修正表：自动 0/+2/+3、舒适 0/+1、经济 0/+4、夜间恒 +4，均在 ±4 内")
    c.add(*io(True, AUTO, False, False, 0))         # 0 初态
    c.add(*io(True, AUTO, False, False, 0))         # 1 自动·占用
    c.add(*io(False, AUTO, False, False, 2))        # 2 自动·空置·标准
    c.add(*io(False, AUTO, True, False, 3))         # 3 自动·空置·节能
    c.add(*io(True, AUTO, True, False, 0))          # 4 自动·占用·节能
    c.add(*io(True, COMFORT, False, False, 0))      # 5 舒适·占用
    c.add(*io(False, COMFORT, False, False, 1))     # 6 舒适·空置
    c.add(*io(False, COMFORT, True, False, 1))      # 7 节能开关不影响舒适
    c.add(*io(True, ECONOMY, False, False, 0))      # 8 经济·占用
    c.add(*io(False, ECONOMY, False, False, 4))     # 9 经济·空置
    c.add(*io(False, NIGHT, False, False, 4))       # 10 夜间·空置
    c.add(*io(True, NIGHT, True, False, 4))         # 11 夜间·占用·节能
    return c


def case_05():
    """模式切换：修正立即跟随，风机因条件中断而不启动。"""
    c = Case("P13-05", "K3;K1;C2",
             "模式切换当拍修正立即跟随；切到夜间会中断计时，风机不得启动")
    c.add(*io(False, AUTO, True, False, 0))         # 0 初态
    c.add(*io(False, AUTO, True, False, 3))         # 1 自动·空置·节能
    c.add(*io(False, AUTO, False, False, 2))        # 2 关掉节能，变 +2
    c.add(*io(False, ECONOMY, True, False, 4))      # 3 切经济，+4
    c.add(*io(False, COMFORT, True, False, 1))      # 4 切舒适，+1
    c.add(*io(True, COMFORT, False, False, 0))      # 5 占用，修正归 0
    c.add(*io(True, NIGHT, False, False, 4))        # 6 切夜间，计时作废
    c.add(*io(True, AUTO, False, False, 0))         # 7 切回自动，须重新计 30 s
    c.span(5, *io(True, AUTO, False, False, 0))     # 8..12 仍不得启动
    return c


def main():
    cases = [c.dict() for c in
             (case_01(), case_02(), case_03(), case_04(), case_05())]
    write_cases(OUT, FX, cases)
    print("P13: %d 条用例 / %d 行 -> %s"
          % (len(cases), sum(len(c["rows"]) for c in cases), OUT))


if __name__ == "__main__":
    main()

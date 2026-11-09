"""生成 S04（称重零点漂移补偿）的用例。"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from _emit import Case, write_cases  # noqa: E402

TESTS = HERE.parent
FX = TESTS / "cases" / "_fixtures" / "S04.io.json"
OUT = TESTS / "cases" / "S04.csv"


def i_(raw, zero=False, calib=0.0):
    return {"RawWeight": raw, "ZeroBtn": zero, "CalibWeight": calib}


def o_(comp, offset=0, alarm=False, st=0):
    return {"CompensatedWeight": comp, "ZeroOffset": offset,
            "DriftAlarm": alarm, "Status": st}


def case_01():
    """未标定时零点为 0，补偿值按 0.01 系数换算。"""
    c = Case("S04-01", "K2;K4;C10",
             "上电零点为 0；CompensatedWeight = RawWeight × 0.01，每拍重算")
    c.add(i_(0), o_(0.0))                        # 0 初态
    c.add(i_(1000), o_(10.0))                    # 1
    c.add(i_(2500), o_(25.0))                    # 2
    c.add(i_(500), o_(5.0))                      # 3 另一量程
    return c


def case_02():
    """零点标定：上升沿把当前原始值记为零点。"""
    c = Case("S04-02", "K1;K2",
             "ZeroBtn 上升沿把 RawWeight 存为零点，补偿值随之归零")
    c.add(i_(500), o_(5.0))                      # 0
    c.add(i_(500, zero=True), o_(0.0, 500))      # 1 标定
    c.add(i_(700), o_(2.0, 500))                 # 2 (700-500)*0.01
    c.add(i_(300), o_(-2.0, 500))                # 3
    return c


def case_03():
    """按住 ZeroBtn 不重复标定。"""
    c = Case("S04-03", "K1",
             "ZeroBtn 按住期间原始值变化，零点不得跟着变")
    c.add(i_(500), o_(5.0))                      # 0
    c.add(i_(500, zero=True), o_(0.0, 500))      # 1
    c.add(i_(900, zero=True), o_(4.0, 500))      # 2 按住，零点不变
    c.add(i_(900, zero=True), o_(4.0, 500))      # 3
    return c


def case_04():
    """漂移报警：偏差超 200 置位，回到 150 以内复位。"""
    c = Case("S04-04", "K3",
             "偏差 250 置漂移报警（16#8401），回到 140 撤销")
    c.add(i_(0), o_(0.0))                        # 0
    c.add(i_(250), o_(2.5, 0, True, 0x8401))     # 1 超 +200
    c.add(i_(140), o_(1.4))                      # 2 回到 150 以内
    c.add(i_(-260), o_(-2.6, 0, True, 0x8401))   # 3 超 -200
    c.add(i_(-150), o_(-1.5))                    # 4 恰好 -150，复位
    return c


def case_05():
    """滞回：200 与 150 之间保持原状态。"""
    c = Case("S04-05", "K3",
             "偏差 190 不报警；升到 210 报警后，回落到 160 仍保持报警")
    c.add(i_(0), o_(0.0))                        # 0
    c.add(i_(190), o_(1.9))                      # 1 未超 200，不报警
    c.add(i_(210), o_(2.1, 0, True, 0x8401))     # 2 超 200，报警
    c.add(i_(160), o_(1.6, 0, True, 0x8401))     # 3 仍在 150 外，保持
    c.add(i_(150), o_(1.5))                      # 4 回到 150，撤销
    return c


def main():
    cases = [c.dict() for c in
             (case_01(), case_02(), case_03(), case_04(), case_05())]
    write_cases(OUT, FX, cases)
    print("S04: %d 条用例 / %d 行" % (len(cases), sum(len(c["rows"]) for c in cases)))


if __name__ == "__main__":
    main()

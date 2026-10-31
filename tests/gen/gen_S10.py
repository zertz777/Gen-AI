"""生成 S10（变频器故障码分级报警）的用例。"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from _emit import Case, write_cases  # noqa: E402

TESTS = HERE.parent
FX = TESTS / "cases" / "_fixtures" / "S10.io.json"
OUT = TESTS / "cases" / "S10.csv"


def i_(code=0, run=False, reset=False):
    return {"VFDFaultCode": code, "VFDRun": run, "ResetBtn": reset}


def o_(lamp=False, trip=False, st=0):
    return {"AlarmLamp": lamp, "TripOutput": trip, "Status": st}


def case_01():
    """轻故障 16#0001：只亮灯，不跳闸。"""
    c = Case("S10-01", "K1;C10",
             "轻故障只点亮报警灯，TripOutput 保持 FALSE，Status = 16#0001")
    c.add(i_(run=True), o_())                              # 0
    c.add(i_(1, run=True), o_(lamp=True, st=1))            # 1
    c.add(i_(1, run=True), o_(lamp=True, st=1))            # 2
    c.add(i_(0, run=True), o_())                           # 3 故障消失
    return c


def case_02():
    """重故障 16#0002：立即跳闸。"""
    c = Case("S10-02", "K1",
             "重故障码 16#0002 当拍置 TripOutput，Status 锁存故障码")
    c.add(i_(run=True), o_())                              # 0
    c.add(i_(2, run=True), o_(lamp=True, trip=True, st=2))  # 1
    return c


def case_03():
    """重故障锁存：故障码消失也不自动复位。"""
    c = Case("S10-03", "K2;K3",
             "重故障码消失后 TripOutput 仍为 TRUE；ResetBtn 上升沿才解除")
    c.add(i_(run=True), o_())                              # 0
    c.add(i_(2, run=True), o_(lamp=True, trip=True, st=2))  # 1
    c.add(i_(0, run=True), o_(lamp=True, trip=True, st=2))  # 2 故障消失，仍锁存
    c.add(i_(0, run=True), o_(lamp=True, trip=True, st=2))  # 3
    c.add(i_(0, run=True, reset=True), o_())               # 4 复位
    c.add(i_(0, run=True), o_())                           # 5
    return c


def case_04():
    """运行中任何非零故障码都跳闸。"""
    c = Case("S10-04", "K4",
             "VFDRun = TRUE 时出现 16#0003 立即跳闸")
    c.add(i_(run=True), o_())                              # 0
    c.add(i_(3, run=True), o_(lamp=True, trip=True, st=3))  # 1
    return c


def case_05():
    """故障仍在时复位无效。"""
    c = Case("S10-05", "K3",
             "当前仍有重故障时按复位不得清除 TripOutput")
    c.add(i_(run=True), o_())                              # 0
    c.add(i_(2, run=True), o_(lamp=True, trip=True, st=2))  # 1
    c.add(i_(2, run=True, reset=True), o_(lamp=True, trip=True, st=2))  # 2 复位无效
    c.add(i_(0, run=True), o_(lamp=True, trip=True, st=2))  # 3
    c.add(i_(0, run=True, reset=True), o_())               # 4 故障消失后复位
    return c


def main():
    cases = [c.dict() for c in
             (case_01(), case_02(), case_03(), case_04(), case_05())]
    write_cases(OUT, FX, cases)
    print("S10: %d 条用例 / %d 行" % (len(cases), sum(len(c["rows"]) for c in cases)))


if __name__ == "__main__":
    main()

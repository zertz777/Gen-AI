"""生成 P20（五工位生产线）的用例。

自动流程：上料→清洗→称重→烧成→成品；称重合格算烧成温度，不合格 kick。
firingTemp 在算出之前的取值需求未定义，写 X（见 A-37）。
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from _emit import Case, write_cases  # noqa: E402

TESTS = HERE.parent
FX = TESTS / "cases" / "_fixtures" / "P20.io.json"
OUT = TESTS / "cases" / "P20.csv"


def i_(mode=False, fwd=False, rev=False, feed=False, wash=False,
       weight=False, firing=False, out=False, wc=False, wtc=False,
       w=0.0, fc=False):
    return {"Mode": mode, "ForwardButton": fwd, "ReverseButton": rev,
            "SensorFeed": feed, "SensorWash": wash, "SensorWeight": weight,
            "SensorFiring": firing, "SensorOutput": out,
            "washComplete": wc, "weightComplete": wtc, "weight": w,
            "firingComplete": fc}


def o_(fwd=False, rev=False, kick=False, light=False, temp="X"):
    return {"MotorForward": fwd, "MotorReverse": rev, "kick": kick,
            "CompletionLight": light, "firingTemp": temp}


def case_01():
    """手动模式正反转互斥。"""
    c = Case("P20-01", "K1;C4;C10",
             "手动模式正转/反转按钮互斥：同时按下两个都不动")
    c.add(i_(), o_())                                       # 0 初态
    c.add(i_(fwd=True), o_(fwd=True))                       # 1 正转
    c.add(i_(rev=True), o_())                               # 2 两键同按，互锁
    c.add(i_(rev=True), o_(rev=True))                       # 3 只按反转
    c.add(i_(), o_())                                       # 4 松手
    return c


def case_02():
    """自动模式合格件：weight=150 → firingTemp=525。"""
    c = Case("P20-02", "K2;K3",
             "合格件按 100—200 线性映射到 500—550：150 对应 525")
    c.add(i_(mode=True), o_())                                          # 0
    c.add(i_(mode=True, feed=True), o_(fwd=True))                       # 1 上料→清洗
    c.add(i_(mode=True, wash=True), o_())                               # 2 到清洗站
    c.add(i_(mode=True, wash=True, wc=True), o_(fwd=True))              # 3 清洗完→称重
    c.add(i_(mode=True, weight=True), o_())                             # 4 到称重站
    c.add(i_(mode=True, weight=True, wtc=True, w=150.0),
          o_(fwd=True, temp=525.0))                                     # 5 合格，出温度
    c.add(i_(mode=True, firing=True), o_(temp=525.0))                   # 6 到烧成站
    c.add(i_(mode=True, firing=True, fc=True), o_(fwd=True, temp=525.0))  # 7 烧成完→成品
    c.add(i_(mode=True, out=True), o_(light=True, temp=525.0))          # 8 到成品站
    c.add(i_(mode=True, out=True), o_(light=True, temp=525.0))          # 9 灯保持
    c.add(i_(mode=True), o_(temp=525.0))                                # 10 取走，灯灭
    return c


def case_03():
    """自动模式不合格件：weight=80 → kick。"""
    c = Case("P20-03", "K2;K3;C2",
             "重量 80 超出 100—200，判不合格并输出 kick，不得去烧成")
    c.add(i_(mode=True), o_())                                          # 0
    c.add(i_(mode=True, feed=True), o_(fwd=True))                       # 1
    c.add(i_(mode=True, wash=True), o_())                               # 2
    c.add(i_(mode=True, wash=True, wc=True), o_(fwd=True))              # 3
    c.add(i_(mode=True, weight=True), o_())                             # 4
    c.add(i_(mode=True, weight=True, wtc=True, w=80.0), o_(kick=True))  # 5 不合格
    c.add(i_(mode=True, weight=True, w=80.0), o_(kick="X"))             # 6 kick 持续时间未定义
    return c


def case_04():
    """合格边界：weight=100 → firingTemp=500。"""
    c = Case("P20-04", "K2;K3",
             "重量下边界 100 判合格，温度取 500")
    c.add(i_(mode=True), o_())                                          # 0
    c.add(i_(mode=True, feed=True), o_(fwd=True))                       # 1
    c.add(i_(mode=True, wash=True), o_())                               # 2
    c.add(i_(mode=True, wash=True, wc=True), o_(fwd=True))              # 3
    c.add(i_(mode=True, weight=True), o_())                             # 4
    c.add(i_(mode=True, weight=True, wtc=True, w=100.0),
          o_(fwd=True, temp=500.0))                                     # 5
    c.add(i_(mode=True, firing=True), o_(temp=500.0))                   # 6
    return c


def case_05():
    """合格边界：weight=200 → firingTemp=550。"""
    c = Case("P20-05", "K2;K3",
             "重量上边界 200 判合格，温度取 550")
    c.add(i_(mode=True), o_())                                          # 0
    c.add(i_(mode=True, feed=True), o_(fwd=True))                       # 1
    c.add(i_(mode=True, wash=True), o_())                               # 2
    c.add(i_(mode=True, wash=True, wc=True), o_(fwd=True))              # 3
    c.add(i_(mode=True, weight=True), o_())                             # 4
    c.add(i_(mode=True, weight=True, wtc=True, w=200.0),
          o_(fwd=True, temp=550.0))                                     # 5
    c.add(i_(mode=True, firing=True), o_(temp=550.0))                   # 6
    return c


def case_06():
    """完成灯：成品站到位点亮，取走后熄灭。"""
    c = Case("P20-06", "K4;C1;C6",
             "成品站到位点亮完成灯，产品取走后熄灭；灯亮期间不得再有 kick")
    c.add(i_(mode=True), o_())                                          # 0
    c.add(i_(mode=True, feed=True), o_(fwd=True))                       # 1
    c.add(i_(mode=True, wash=True), o_())                               # 2
    c.add(i_(mode=True, wash=True, wc=True), o_(fwd=True))              # 3
    c.add(i_(mode=True, weight=True), o_())                             # 4
    c.add(i_(mode=True, weight=True, wtc=True, w=150.0),
          o_(fwd=True, temp=525.0))                                     # 5
    c.add(i_(mode=True, firing=True), o_(temp=525.0))                   # 6
    c.add(i_(mode=True, firing=True, fc=True), o_(fwd=True, temp=525.0))  # 7
    c.add(i_(mode=True, out=True), o_(light=True, temp=525.0))          # 8 点亮
    c.add(i_(mode=True, out=True), o_(light=True, temp=525.0))          # 9 保持
    c.add(i_(mode=True), o_(temp=525.0))                                # 10 取走，熄灭
    c.add(i_(mode=True), o_(temp=525.0))                                # 11
    return c


def case_07():
    """K3：到位但完成信号未到，不得推进。"""
    c = Case("P20-07", "K3",
             "清洗站到位但 washComplete 未到（或与传感器不一致）时不得推进")
    c.add(i_(mode=True, wc=True), o_())                                 # 0 无到位却报完成，不得动
    c.add(i_(mode=True, feed=True), o_(fwd=True))                       # 1
    c.add(i_(mode=True, wash=True), o_())                               # 2 到清洗站
    c.add(i_(mode=True, wash=True), o_())                               # 3 等完成信号
    c.add(i_(mode=True, wash=True), o_())                               # 4
    c.add(i_(mode=True, wash=True, wc=True), o_(fwd=True))              # 5 完成，推进
    return c


def main():
    cases = [c.dict() for c in
             (case_01(), case_02(), case_03(), case_04(),
              case_05(), case_06(), case_07())]
    write_cases(OUT, FX, cases)
    print("P20: %d 条用例 / %d 行 -> %s"
          % (len(cases), sum(len(c["rows"]) for c in cases), OUT))


if __name__ == "__main__":
    main()

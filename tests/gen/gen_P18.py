"""生成 P18（FIFO 环形队列）的用例。

item / buffer 是 INOUT，在 fixture 里当输入（D-09），所以只能判定
elementCount 与 status；队内数据本身由 PLCVerif 的 INOUT 变量去验。
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from _emit import Case, write_cases  # noqa: E402

TESTS = HERE.parent
FX = TESTS / "cases" / "_fixtures" / "P18.io.json"
OUT = TESTS / "cases" / "P18.csv"

CAP5 = [0, 0, 0, 0, 0]
CAP1 = [0]


def i_(enq=False, deq=False, reset=False, item=42, buf=None):
    return {"enqueue": enq, "dequeue": deq, "reset": reset,
            "item": item, "buffer": list(CAP5 if buf is None else buf)}


def o_(count, status=0):
    return {"elementCount": count, "status": status}


def case_01():
    """入队三次、出队三次，计数逐次变化。"""
    c = Case("P18-01", "K2;K4;C10",
             "上升沿才入队/出队：按住不放不重复操作，计数与有效元素数一致")
    c.add(i_(), o_(0))                       # 0 初态
    c.add(i_(enq=True), o_(1))               # 1 入队 1
    c.add(i_(enq=True), o_(1))               # 2 无新上升沿
    c.add(i_(), o_(1))                       # 3
    c.add(i_(enq=True), o_(2))               # 4 入队 2
    c.add(i_(), o_(2))                       # 5
    c.add(i_(enq=True), o_(3))               # 6 入队 3
    c.add(i_(deq=True), o_(2))               # 7 出队 1
    c.add(i_(), o_(2))                       # 8
    c.add(i_(deq=True), o_(1))               # 9 出队 2
    c.add(i_(), o_(1))                       # 10
    c.add(i_(deq=True), o_(0))               # 11 出队 3
    c.add(i_(), o_(0))                       # 12 空
    return c


def case_02():
    """队列满时入队被拒绝，status = 16#8002。"""
    c = Case("P18-02", "K3;K4",
             "容量 5 的队列满后再入队被拒绝，计数保持 5")
    c.add(i_(), o_(0))                       # 0
    c.add(i_(enq=True), o_(1))               # 1
    c.add(i_(), o_(1))                       # 2
    c.add(i_(enq=True), o_(2))               # 3
    c.add(i_(), o_(2))                       # 4
    c.add(i_(enq=True), o_(3))               # 5
    c.add(i_(), o_(3))                       # 6
    c.add(i_(enq=True), o_(4))               # 7
    c.add(i_(), o_(4))                       # 8
    c.add(i_(enq=True), o_(5))               # 9 满
    c.add(i_(), o_(5))                       # 10
    c.add(i_(enq=True), o_(5, 0x8002))       # 11 拒绝
    c.add(i_(), o_(5))                       # 12 空闲，status 归零
    return c


def case_03():
    """reset 优先于同拍的入队。"""
    c = Case("P18-03", "K1;C1;C4",
             "reset 与入队同拍时以 reset 为准：计数清 0、status = 0")
    c.add(i_(), o_(0))                       # 0
    c.add(i_(enq=True), o_(1))               # 1
    c.add(i_(), o_(1))                       # 2
    c.add(i_(enq=True), o_(2))               # 3
    c.add(i_(enq=True, reset=True), o_(0))   # 4 复位优先
    c.add(i_(), o_(0))                       # 5
    return c


def case_04():
    """reset 后至少保持一拍为空（C9）。"""
    c = Case("P18-04", "K1;C9",
             "reset 拉高期间与撤销后一拍，计数都必须为 0")
    c.add(i_(), o_(0))                       # 0
    c.add(i_(enq=True), o_(1))               # 1
    c.add(i_(reset=True), o_(0))             # 2
    c.add(i_(reset=True), o_(0))             # 3
    c.add(i_(), o_(0))                       # 4 撤销后仍空
    return c


def case_05():
    """空队出队被拒绝，status = 16#8001。"""
    c = Case("P18-05", "K3;C2",
             "空队列出队被拒绝，计数保持 0，status = 16#8001")
    c.add(i_(), o_(0))                       # 0
    c.add(i_(deq=True), o_(0, 0x8001))       # 1 拒绝
    c.add(i_(), o_(0))                       # 2 status 归零
    c.add(i_(deq=True), o_(0, 0x8001))       # 3 再拒绝
    return c


def case_06():
    """入队出队交替，计数不越界。"""
    c = Case("P18-06", "K2;K3;K4",
             "入队/出队交替进行，计数始终等于有效元素数")
    c.add(i_(), o_(0))                       # 0
    c.add(i_(enq=True), o_(1))               # 1
    c.add(i_(), o_(1))                       # 2
    c.add(i_(enq=True), o_(2))               # 3
    c.add(i_(deq=True), o_(1))               # 4
    c.add(i_(), o_(1))                       # 5
    c.add(i_(enq=True), o_(2))               # 6
    c.add(i_(deq=True), o_(1))               # 7
    c.add(i_(), o_(1))                       # 8
    c.add(i_(deq=True), o_(0))               # 9
    c.add(i_(deq=True), o_(0))               # 10 无新沿
    return c


def case_07():
    """容量由 buffer 长度决定：长度 1 时入队一次即满。"""
    c = Case("P18-07", "K4;K3",
             "buffer 长度 1 时容量为 1，第二次入队立即报 16#8002")
    c.add(i_(buf=CAP1), o_(0))               # 0
    c.add(i_(enq=True, buf=CAP1), o_(1))     # 1
    c.add(i_(buf=CAP1), o_(1))               # 2
    c.add(i_(enq=True, buf=CAP1), o_(1, 0x8002))  # 3 满
    c.add(i_(deq=True, buf=CAP1), o_(0))     # 4 出队
    return c


def main():
    cases = [c.dict() for c in
             (case_01(), case_02(), case_03(), case_04(),
              case_05(), case_06(), case_07())]
    write_cases(OUT, FX, cases)
    print("P18: %d 条用例 / %d 行 -> %s"
          % (len(cases), sum(len(c["rows"]) for c in cases), OUT))


if __name__ == "__main__":
    main()

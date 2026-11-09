"""实际输出的读取与校验（成员2 → 成员4 的接口契约）。

一个 run 的目录约定：

    <run_dir>/
    ├── source/final.st              # 被测程序（成员2 产出）
    └── test/
        ├── actual/<case_id>.csv     # 每个用例一份，逐拍实际输出（成员2 产出）
        ├── status.json              # 可选：{"status":"pass|fail|timeout","reason":"..."}
        └── cases_result.jsonl       # 判定结果（成员4 产出）

actual CSV 格式（列名与 cases/_fixtures/<题号>.io.json 的输出列逐字一致）：

    case_id,cycle,hiAlarm,loAlarm,error,status
    P03-01,1,TRUE,FALSE,FALSE,16#0000
    P03-01,2,TRUE,FALSE,FALSE,16#0000

规则（违反任一条都算"工具没把结果交对"，判 error 而不是 fail）：
1. 输出列必须齐全；缺一列就报出缺哪一列
2. cycle 从 1 开始且连续；允许带 cycle=0（初态行），读取时忽略
3. 拍数必须与用例期望拍数一致
4. 值按 fixture 里的声明类型解析（BOOL 只认 TRUE/FALSE，WORD 认 16#xxxx）

为什么要在这里解析类型：旧版 replay 后端把 "TRUE" 当字符串直接和 True 比，
BOOL 列必然判 fail——这条路径以前没有真 actual 文件，所以一直没暴露。
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

from .case_loader import CaseError, parse_value


class ActualError(Exception):
    """actual 文件不合法（缺列、拍数不对、类型错）。属于工具故障，不算模型失败。"""


class ActualStore:
    """按 case_id 取实际输出。

    path 可以是：
      - 目录：<dir>/<case_id>.csv（推荐的 run 内布局）
      - 单文件：一个 CSV 里混放多个 case_id
    """

    def __init__(self, path):
        self.path = Path(path)
        if not self.path.exists():
            raise ActualError("actual 路径不存在：%s" % self.path)
        self._cache = {}

    # ---- 内部 ----
    def _rows(self, case_id):
        if case_id in self._cache:
            return self._cache[case_id]
        if self.path.is_dir():
            f = self.path / ("%s.csv" % case_id)
            if not f.exists():
                raise ActualError("缺少 %s 的 actual 文件：%s" % (case_id, f))
            rows = self._read_csv(f, case_id)
        else:
            rows = self._read_csv(self.path, case_id)
        self._cache[case_id] = rows
        return rows

    @staticmethod
    def _read_csv(path, case_id):
        with open(path, encoding="utf-8-sig", newline="") as fh:
            reader = csv.DictReader(fh)
            header = reader.fieldnames or []
            if "case_id" not in header or "cycle" not in header:
                raise ActualError("%s 缺 case_id/cycle 列：%r" % (path, header))
            rows = [r for r in reader if (r.get("case_id") or "").strip() == case_id]
        if not rows:
            raise ActualError("%s 里没有 %s 的行" % (path, case_id))
        return rows

    # ---- 对外 ----
    def has(self, case_id):
        try:
            self._rows(case_id)
            return True
        except ActualError:
            return False

    def load(self, case_id, expected_cycles, out_types):
        """返回 [{"cycle": 1, "out": {...}}, ...]，已按声明类型解析。

        expected_cycles: 期望的拍号列表，如 [1,2,3]
        out_types: {列名: IEC 类型}，来自 fixture
        """
        rows = self._rows(case_id)
        header = set(rows[0].keys())
        missing = [n for n in out_types if n not in header]
        if missing:
            raise ActualError("%s 缺输出列：%s" % (case_id, ", ".join(missing)))

        parsed = []
        for r in rows:
            try:
                cyc = int(r["cycle"])
            except (TypeError, ValueError):
                raise ActualError("%s 的 cycle 不是整数：%r" % (case_id, r.get("cycle")))
            if cyc == 0:                       # 初态行：允许，但不参与比对
                continue
            out = {}
            for name, typ in out_types.items():
                try:
                    out[name] = parse_value(r[name], typ)
                except CaseError as e:
                    raise ActualError("%s 第 %d 拍 %s 解析失败：%s"
                                      % (case_id, cyc, name, e)) from e
            parsed.append({"cycle": cyc, "out": out})

        got = [x["cycle"] for x in parsed]
        if got != list(expected_cycles):
            raise ActualError("%s 的拍号不对：期望 %d 拍 %s，实际 %d 拍 %s"
                              % (case_id, len(expected_cycles),
                                 _brief(expected_cycles), len(got), _brief(got)))
        return parsed


def _brief(nums, keep=4):
    s = ",".join(str(n) for n in nums[:keep])
    return s + ("…" if len(nums) > keep else "")


def read_status(run_dir):
    """读 <run_dir>/test/status.json；不存在返回 None。

    成员2 只需在整题跑崩/超时时写一条：
        {"status": "timeout", "reason": "compile timeout 90s"}
    """
    p = Path(run_dir) / "test" / "status.json"
    if not p.exists():
        return None
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ActualError("status.json 不是合法 JSON：%s" % e) from e
    if not isinstance(d, dict) or "status" not in d:
        raise ActualError("status.json 必须带 status 字段：%r" % d)
    if d["status"] not in ("pass", "fail", "timeout", "error"):
        raise ActualError("status.json 的 status 只能是 pass/fail/timeout/error：%r"
                          % d["status"])
    return d

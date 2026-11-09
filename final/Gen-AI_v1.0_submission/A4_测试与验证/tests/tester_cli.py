"""成员4 逐周期测试器：接成员2 的 `test.command` 协议。

成员2 的 `agent/src/tools.py` 会用这四个占位符调用本脚本：

    python tests/tester_cli.py \
      --source {source} --task-card {task_card} \
      --cases-dir {cases_dir} --result {result}

本脚本按 `docs/toolchain.md` §4 写结果 JSON：

    {"status":"pass|fail|timeout|tool_error|skipped",
     "total":6,"passed":5,
     "passed_ids":["P03-01",...],
     "failures":[{"case_id":"P03-02","cycle":2,"signal":"hiAlarm",
                  "expected":true,"actual":false}]}

退出码：pass=0，fail=1，tool_error=2，skipped/timeout=0。
（成员2 的校验规则：pass 要求 total>0、passed==total、退出码 0；fail 要求 passed<total。）

执行后端（三选一，默认 auto）：

    replay  读逐拍 actual（成员2 的产物），推荐
    exec    调外部命令跑 ST，命令模板支持 {source} {inputs} {outputs} {task_card}
    auto    有 actual 用 replay，否则有 --runner-cmd 用 exec，都没有就 skipped

actual 的查找顺序（相对 {source}）：
    <source_dir>/actual/  →  <source_dir>/test/actual/  →  <source_dir>/../test/actual/
"""
from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from runner.actual_io import ActualError, ActualStore, read_status   # noqa: E402
from runner.backends import BackendError, ExecBackend, ReplayBackend  # noqa: E402
from runner.case_loader import CaseError, load_cases                 # noqa: E402
from runner.io_normalize import normalize                            # noqa: E402
from runner.verdict import PASS, judge                               # noqa: E402


def _write_result(path, payload):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                 encoding="utf-8")


def _find_actual(source: Path):
    for c in (source.parent / "actual",
              source.parent / "test" / "actual",
              source.parent.parent / "test" / "actual",
              source.parent.parent / "actual"):
        if c.is_dir():
            return c
    return None


def _find_status(source: Path):
    for c in (source.parent / "status.json",
              source.parent.parent / "test" / "status.json",
              source.parent.parent / "status.json"):
        if c.is_file():
            return c
    return None


def _fixture_from_task_card(task_card: dict, workdir: Path) -> Path:
    fx = normalize(task_card)
    p = workdir / ("%s.io.json" % fx["task_id"])
    p.write_text(json.dumps(fx, ensure_ascii=False, indent=2), encoding="utf-8")
    return p


def _failure(case_id, res):
    mm = res.get("mismatch") or {}
    if mm and "variable" in mm:
        return {"case_id": case_id, "cycle": mm.get("cycle"),
                "signal": mm.get("variable"), "expected": mm.get("expected"),
                "actual": mm.get("actual")}
    return {"case_id": case_id, "cycle": None, "signal": None,
            "expected": None, "actual": None,
            "reason": res.get("reason") or (mm.get("error") if mm else None)}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", required=True, help="被测 ST 源文件")
    ap.add_argument("--task-card", required=True, help="成员2 的 task_card.json")
    ap.add_argument("--cases-dir", required=True, help="用例目录（含 <题号>.csv）")
    ap.add_argument("--result", required=True, help="要写出的 JSON 结果")
    ap.add_argument("--backend", default="auto",
                    choices=["auto", "replay", "exec"])
    ap.add_argument("--actual", help="replay：actual 文件或目录（默认自动查找）")
    ap.add_argument("--runner-cmd", help="exec：命令模板，也可用环境变量 PLC_RUNNER_CMD")
    ap.add_argument("--timeout", type=float, default=90.0)
    a = ap.parse_args(argv)

    source = Path(a.source)
    cases_dir = Path(a.cases_dir)
    runner_cmd = a.runner_cmd or __import__("os").environ.get("PLC_RUNNER_CMD")

    def done(status, reason=None, total=0, passed=0, ids=None, failures=None, rc=0):
        payload = {"status": status, "total": total, "passed": passed,
                   "passed_ids": ids or [], "failures": failures or []}
        if reason:
            payload["reason"] = reason
        _write_result(a.result, payload)
        return rc

    try:
        task_card = json.loads(source and Path(a.task_card).read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as e:
        return done("tool_error", "task_card 读取失败：%s" % e, rc=2)

    task_id = task_card.get("task_id")
    cases_csv = cases_dir / ("%s.csv" % task_id) if task_id else None
    if not task_id or not cases_csv or not cases_csv.is_file():
        return done("skipped", "找不到用例：%s" % cases_csv, rc=0)

    tmp = Path(tempfile.mkdtemp(prefix="tester_"))
    try:
        io_json = _fixture_from_task_card(task_card, tmp)
        _, cases = load_cases(cases_csv, io_json)
    except (CaseError, OSError, ValueError) as e:
        return done("tool_error", "用例/task_card 校验失败：%s" % e, rc=2)

    # 选后端
    backend = None
    status = None
    actual = Path(a.actual) if a.actual else _find_actual(source)
    if a.backend in ("auto", "replay") and actual:
        try:
            st = _find_status(source)
            status = read_status(st.parent) if st else None
            backend = ReplayBackend(ActualStore(actual), _outs(io_json), status)
        except (ActualError, OSError) as e:
            return done("tool_error", "actual 不可用：%s" % e, rc=2)
    elif a.backend in ("auto", "exec") and runner_cmd:
        backend = ExecBackend(runner_cmd, _outs(io_json), a.timeout,
                              workdir=str(source.parent),
                              extra={"task_card": str(Path(a.task_card).resolve())})
    if backend is None:
        return done("skipped", "没有 actual，也没有 runner 命令", rc=0)

    results = [judge(c, backend, str(source), a.timeout) for c in cases]
    ids = [r["case_id"] for r in results if r["status"] == PASS]
    failures = [_failure(r["case_id"], r) for r in results if r["status"] != PASS]
    total, passed = len(results), len(ids)

    if any(r["status"] == "error" for r in results):
        return done("tool_error", "actual/执行器格式错误，见 failures",
                    total, passed, ids, failures, rc=2)
    if any(r["status"] == "timeout" for r in results):
        return done("timeout", "有用例执行超时", total, passed, ids, failures, rc=0)
    if passed == total and total:
        return done("pass", None, total, passed, ids, [], rc=0)
    return done("fail", "有失配用例", total, passed, ids, failures, rc=1)


def _outs(io_json: Path):
    d = json.loads(io_json.read_text(encoding="utf-8"))
    return {r["name"]: r["type"] for r in d["io"] if r["direction"] == "OUT"}


if __name__ == "__main__":
    sys.exit(main())

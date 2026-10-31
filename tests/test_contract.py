"""成员2 → 成员4 的接口契约测试：actual CSV、exec 后端、批量汇总。

这三样是 D2-4 新增的，出错的话下午的全量测试会整体失真，所以单独测。
"""
import csv
import json
import sys
import time
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from runner.actual_io import ActualError, ActualStore, read_status      # noqa: E402
from runner.backends import (BackendError, BackendTimeout, ExecBackend,  # noqa: E402
                             ReplayBackend, split_cmd)
from runner.case_loader import load_cases, load_io                       # noqa: E402
from runner.compare import compare_case                                  # noqa: E402
from runner.verdict import PASS, judge                                   # noqa: E402

P03 = HERE / "cases" / "P03.csv"
P03IO = HERE / "cases" / "_fixtures" / "P03.io.json"


def _fmt(v, typ):
    if v == "X":                       # 期望侧的不判定，actual 必须给个具体值
        return "FALSE" if typ == "BOOL" else ("16#0000" if "WORD" in typ else "0")
    if isinstance(v, bool):
        return "TRUE" if v else "FALSE"
    if isinstance(v, list):
        return json.dumps(v, ensure_ascii=False).replace("true", "TRUE").replace("false", "FALSE")
    return str(v)


def write_actual(cases_csv, io_json, out_dir, case_filter=None):
    """把期望值写成 actual（模拟成员2 的正常产出）。"""
    _, _, outs = load_io(io_json)
    _, cases = load_cases(cases_csv, io_json)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    for case in cases:
        if case_filter and not case_filter(case):
            continue
        with (out_dir / ("%s.csv" % case.case_id)).open("w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(["case_id", "cycle"] + list(outs))
            for c in case.cycles[1:]:
                w.writerow([case.case_id, c["cycle"]] + [_fmt(c["out"][k], outs[k]) for k in outs])


# ---------- actual CSV 校验 ----------

def test_actual_parses_types_and_matches_expected(tmp_path):
    write_actual(P03, P03IO, tmp_path)
    _, _, outs = load_io(P03IO)
    _, cases = load_cases(P03, P03IO)
    store = ActualStore(tmp_path)
    for case in cases:
        expected_cycles = [c["cycle"] for c in case.cycles[1:]]
        actual = store.load(case.case_id, expected_cycles, outs)
        ok, mm = compare_case(case, actual)
        assert ok, (case.case_id, mm)


def test_actual_missing_column_is_tool_error(tmp_path):
    write_actual(P03, P03IO, tmp_path)
    f = tmp_path / "P03-01.csv"
    lines = f.read_text(encoding="utf-8").splitlines()
    # 删掉 status 列
    keep = [",".join(line.split(",")[:-1]) for line in lines]
    f.write_text("\n".join(keep) + "\n", encoding="utf-8")
    _, _, outs = load_io(P03IO)
    _, cases = load_cases(P03, P03IO)
    with pytest.raises(ActualError, match="缺输出列"):
        ActualStore(tmp_path).load(cases[0].case_id, [1, 2, 3, 4, 5], outs)


def test_actual_cycle_gap_rejected(tmp_path):
    write_actual(P03, P03IO, tmp_path)
    f = tmp_path / "P03-01.csv"
    lines = f.read_text(encoding="utf-8").splitlines()
    f.write_text("\n".join(lines[:2] + lines[3:]) + "\n", encoding="utf-8")
    _, _, outs = load_io(P03IO)
    _, cases = load_cases(P03, P03IO)
    with pytest.raises(ActualError, match="拍号不对"):
        ActualStore(tmp_path).load("P03-01", [1, 2, 3, 4, 5], outs)


def test_actual_cycle_zero_is_ignored(tmp_path):
    write_actual(P03, P03IO, tmp_path)
    f = tmp_path / "P03-01.csv"
    lines = f.read_text(encoding="utf-8").splitlines()
    f.write_text("\n".join([lines[0], "P03-01,0,FALSE,FALSE,FALSE,16#0000"] + lines[1:]) + "\n",
                 encoding="utf-8")
    _, _, outs = load_io(P03IO)
    _, cases = load_cases(P03, P03IO)
    got = ActualStore(tmp_path).load("P03-01", [1, 2, 3, 4, 5], outs)
    assert [c["cycle"] for c in got] == [1, 2, 3, 4, 5]


def test_status_json_timeout(tmp_path):
    p = tmp_path / "test"
    p.mkdir()
    (p / "status.json").write_text('{"status":"timeout","reason":"compile 90s"}',
                                   encoding="utf-8")
    assert read_status(tmp_path)["status"] == "timeout"


def test_status_json_rejects_bad_value(tmp_path):
    p = tmp_path / "test"
    p.mkdir()
    (p / "status.json").write_text('{"status":"炸了"}', encoding="utf-8")
    with pytest.raises(ActualError):
        read_status(tmp_path)


# ---------- replay 后端 ----------

def test_replay_passes_when_actual_equals_expected(tmp_path):
    write_actual(P03, P03IO, tmp_path)
    _, _, outs = load_io(P03IO)
    _, cases = load_cases(P03, P03IO)
    backend = ReplayBackend(ActualStore(tmp_path), outs)
    for case in cases:
        assert judge(case, backend, "", 5)["status"] == PASS


def test_replay_status_timeout_is_timeout_not_fail(tmp_path):
    write_actual(P03, P03IO, tmp_path)
    _, _, outs = load_io(P03IO)
    _, cases = load_cases(P03, P03IO)
    backend = ReplayBackend(ActualStore(tmp_path), outs, {"status": "timeout", "reason": "x"})
    r = judge(cases[0], backend, "", 5)
    assert r["status"] == "timeout" and r["reason"] == "x"


def test_replay_missing_actual_is_error(tmp_path):
    _, _, outs = load_io(P03IO)
    _, cases = load_cases(P03, P03IO)
    backend = ReplayBackend(ActualStore(tmp_path), outs)
    r = judge(cases[0], backend, "", 5)
    assert r["status"] == "error" and "缺少" in r["reason"]


# ---------- exec 后端 ----------

def test_split_cmd_keeps_windows_backslash():
    argv = split_cmd(r'"C:\Program Files\Python\python.exe" run_one.py --x 1')
    assert argv[0] == r"C:\Program Files\Python\python.exe"
    assert argv[1:] == ["run_one.py", "--x", "1"]
    assert split_cmd('["python","a b.py"]') == ["python", "a b.py"]


def test_exec_backend_hard_timeout(tmp_path):
    _, _, outs = load_io(P03IO)
    _, cases = load_cases(P03, P03IO)
    backend = ExecBackend('["python","-c","import time; time.sleep(5)"]',
                          outs, timeout_s=0.5)
    t0 = time.perf_counter()
    with pytest.raises(BackendTimeout):
        backend.run("x", cases[0])
    assert time.perf_counter() - t0 < 4        # 真的被打断，不是等它睡完


def test_exec_backend_reports_nonzero_exit(tmp_path):
    _, _, outs = load_io(P03IO)
    _, cases = load_cases(P03, P03IO)
    backend = ExecBackend('["python","-c","import sys; sys.exit(3)"]', outs, timeout_s=5)
    with pytest.raises(BackendError, match="退出码 3"):
        backend.run("x", cases[0])


def test_exec_backend_writes_outputs(tmp_path):
    """一个最小的 P03 实现：证明 inputs/outputs 占位符与解析链路通。"""
    script = tmp_path / "runner.py"
    script.write_text(
        "import csv, sys\n"
        "inp, outp = sys.argv[1], sys.argv[2]\n"
        "rows = list(csv.DictReader(open(inp, encoding='utf-8')))\n"
        "with open(outp, 'w', encoding='utf-8', newline='') as f:\n"
        "    w = csv.writer(f)\n"
        "    w.writerow(['case_id','cycle','hiAlarm','loAlarm','error','status'])\n"
        "    for r in rows:\n"
        "        if r['cycle'] == '0':\n"
        "            continue\n"
        "        v, hi, lo = float(r['Value']), float(r['hiLevel']), float(r['loLevel'])\n"
        "        w.writerow(['P03-01', r['cycle'], 'TRUE' if v > hi else 'FALSE',\n"
        "                    'TRUE' if v < lo else 'FALSE', 'FALSE', '16#0000'])\n",
        encoding="utf-8")
    _, _, outs = load_io(P03IO)
    _, cases = load_cases(P03, P03IO)
    backend = ExecBackend(json.dumps(["python", str(script), "{inputs}", "{outputs}"]),
                          outs, timeout_s=10)
    actual = backend.run("x", cases[0])       # P03-01 只有高报，低报恒 FALSE
    assert len(actual) == 5 and actual[0]["cycle"] == 1
    assert actual[0]["out"]["hiAlarm"] is True

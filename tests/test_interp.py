"""ST 解释器单测：语法子集、计时语义、数组/结构体、CLI 契约。

重点不是"解释器功能多"，而是**三条会被验收的口径**：

1. 参考实现（refimpl/P03.st）跑 6 条真实用例逐拍全 pass；
2. 计时按 D-11"同一拍先累加后判定"——5 s / 20 ms = 第 25 拍动作；
3. CLI 写出来的 actual 必须能被 `runner.actual_io.ActualStore` 按契约读回。
"""
import csv
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from runner.actual_io import ActualStore                                    # noqa: E402
from runner.case_loader import load_cases, load_io                          # noqa: E402
from runner.compare import compare_case                                     # noqa: E402
from runner.interp.eval import InterpError, Interpreter                     # noqa: E402
from runner.interp.st_types import TypeSpec, format_value, parse_literal       # noqa: E402

P03_CASES = HERE / "cases" / "P03.csv"
P03_IO = HERE / "cases" / "_fixtures" / "P03.io.json"
P03_REF = HERE / "refimpl" / "P03.st"
RUN_PY = HERE / "runner" / "interp" / "run.py"


# ---------------------------------------------------------------- 工具

def _step(itp, mapping=None):
    """设输入 -> 跑一拍 -> 返回 {列名: CSV 文本}。"""
    if mapping is not None:
        itp.set_inputs(mapping)
    itp.run_cycle()
    return itp.snapshot_text()


def _run_source(src, cases_path, io_path, block=None):
    """每条用例都用新的解释器（初态重来），返回 [(case_id, ok, mismatch)]。"""
    _, cases = load_cases(str(cases_path), str(io_path))
    out = []
    for case in cases:
        itp = Interpreter.from_source(src, block=block, cycle_ms=20.0)
        actual = []
        for c in case.cycles:
            itp.set_inputs(dict(c["in"]))
            if c["cycle"] == 0:
                continue
            itp.run_cycle()
            actual.append({"cycle": c["cycle"],
                           "out": {name: val for name, _, val in itp.snapshot()}})
        ok, mm = compare_case(case, actual)
        out.append((case.case_id, ok, mm))
    return out


def _write_inputs(path, case):
    """按 ExecBackend 的格式写 cycle + IN 列（含 cycle=0 初态）。"""
    ins = list(case.cycles[0]["in"].keys())
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["cycle"] + ins)
        for c in case.cycles:
            w.writerow([c["cycle"]] + [_csv(c["in"][k]) for k in ins])


def _csv(v):
    if isinstance(v, bool):
        return "TRUE" if v else "FALSE"
    if isinstance(v, (list, dict)):
        import json
        return json.dumps(v, ensure_ascii=False).replace("true", "TRUE").replace("false", "FALSE")
    return str(v)


# ---------------------------------------------------------------- P03 参考实现

def test_p03_refimpl_passes_all_six_cases():
    src = P03_REF.read_text(encoding="utf-8")
    results = _run_source(src, P03_CASES, P03_IO, block="FB_P03")
    assert len(results) == 6
    bad = [(cid, mm) for cid, ok, mm in results if not ok]
    assert not bad, "参考实现没通过：%r" % (bad,)


def test_k1_branch_returns_before_alarm_logic():
    """P03-04：参数非法时 error/status 置位，且报警逻辑不再执行（alarm 保持 FALSE）。"""
    src = P03_REF.read_text(encoding="utf-8")
    itp = Interpreter.from_source(src, block="FB_P03")
    snap = _step(itp, {"Value": "5", "hiLevel": "3", "loLevel": "10", "hystWindow": "2"})
    assert snap["error"] == "TRUE"
    assert snap["status"] == "16#8001"
    assert snap["hiAlarm"] == "FALSE" and snap["loAlarm"] == "FALSE"


# ---------------------------------------------------------------- 计时语义

TON_SRC = """
FUNCTION_BLOCK FB_T
VAR_INPUT
    In : BOOL;
    PT : TIME;
END_VAR
VAR_OUTPUT
    Q : BOOL;
    ET : TIME;
END_VAR
VAR
    t : TON;
END_VAR
    t(IN := In, PT := PT);
    Q := t.Q;
    ET := t.ET;
END_FUNCTION_BLOCK
"""


def test_ton_accumulate_then_test_25th_cycle():
    """5 s ÷ 20 ms = 250 拍；这里用 500 ms 验证第 25 拍就动作（不是第 26 拍）。"""
    itp = Interpreter.from_source(TON_SRC)
    first_q, et_at_first = None, None
    for cyc in range(1, 40):
        snap = _step(itp, {"In": "TRUE", "PT": "T#500ms"})
        if snap["Q"] == "TRUE" and first_q is None:
            first_q, et_at_first = cyc, snap["ET"]
    assert first_q == 25
    assert et_at_first == "T#500ms"


def test_ton_resets_when_in_false():
    itp = Interpreter.from_source(TON_SRC)
    for _ in range(30):
        _step(itp, {"In": "TRUE", "PT": "T#500ms"})
    assert _step(itp)["Q"] == "TRUE"
    snap = _step(itp, {"In": "FALSE", "PT": "T#500ms"})
    assert snap["Q"] == "FALSE" and snap["ET"] == "T#0ms"


RTRIG_SRC = """
FUNCTION_BLOCK FB_E
VAR_INPUT
    clk : BOOL;
END_VAR
VAR_OUTPUT
    q : BOOL;
END_VAR
VAR
    tr : R_TRIG;
END_VAR
    tr(CLK := clk);
    q := tr.Q;
END_FUNCTION_BLOCK
"""


def test_r_trig_only_on_rising_edge():
    itp = Interpreter.from_source(RTRIG_SRC)
    seq = [("TRUE", "TRUE"), ("TRUE", "FALSE"), ("FALSE", "FALSE"), ("TRUE", "TRUE")]
    for clk, expect in seq:
        assert _step(itp, {"clk": clk})["q"] == expect, "clk=%s 时 q 应为 %s" % (clk, expect)


# ---------------------------------------------------------------- 数组 / 结构体

ARRAY_SRC = """
TYPE ST_Pump :
STRUCT
    priority : INT;
    RunComd : BOOL;
END_STRUCT
END_TYPE

FUNCTION_BLOCK FB_A
VAR_IN_OUT
    pumpGroup : ARRAY[1..3] OF ST_Pump;
END_VAR
VAR_OUTPUT
    total : INT;
END_VAR
VAR
    i : INT;
END_VAR
    total := 0;
    FOR i := 1 TO 3 DO
        IF pumpGroup[i].priority > 1 THEN
            pumpGroup[i].RunComd := TRUE;
            total := total + pumpGroup[i].priority;
        ELSE
            pumpGroup[i].RunComd := FALSE;
        END_IF;
    END_FOR;
END_FUNCTION_BLOCK
"""


DYN_SRC = """
FUNCTION_BLOCK FB_D
VAR_INPUT
    count : INT;
    ipText : STRING(254);
END_VAR
VAR_IN_OUT
    values : ARRAY[*] OF INT;
END_VAR
VAR_OUTPUT
    n : INT;
    tag : STRING;
END_VAR
VAR
    i : INT;
END_VAR
    n := 0;
    FOR i := 1 TO count DO
        n := n + values[i];
    END_FOR;
    tag := ipText;
END_FUNCTION_BLOCK
"""


def test_dynamic_array_and_string_length():
    """P08 的 `ARRAY[*]` 与 P14 的 `STRING(254)`：真实语料里出现过，必须能解析。"""
    itp = Interpreter.from_source(DYN_SRC)
    snap = _step(itp, {"count": "3", "values": "[1, 2, 3]", "ipText": '"10.0.0.1"'})
    assert snap["n"] == "6"
    assert snap["tag"] == '"10.0.0.1"'


def test_struct_array_input_and_output_columns():
    itp = Interpreter.from_source(ARRAY_SRC)
    # 列名与 fixture 逐字一致（结构体数组按字段拆列）
    cols = itp.output_columns()
    assert "pumpGroup[].RunComd" in cols
    assert "pumpGroup[].priority" in cols
    itp.set_inputs({"pumpGroup[].priority": "[1, 2, 3]"})
    itp.run_cycle()
    snap = itp.snapshot_text()
    assert snap["pumpGroup[].RunComd"] == "[FALSE, TRUE, TRUE]"
    assert snap["total"] == "5"


# ---------------------------------------------------------------- 控制流 / 整数语义

LOOP_SRC = """
FUNCTION_BLOCK FB_L
VAR_INPUT
    n : INT;
END_VAR
VAR_OUTPUT
    s : INT;
    m : INT;
    q : INT;
    r : INT;
END_VAR
VAR
    i : INT;
END_VAR
    s := 0;
    FOR i := 1 TO n DO
        s := s + i;
    END_FOR;
    CASE n OF
        1, 2:
            m := 10;
        3:
            m := 30;
        ELSE
            m := 99;
    END_CASE;
    q := -7 / 2;
    r := -7 MOD 2;
END_FUNCTION_BLOCK
"""


def test_for_case_and_integer_truncation():
    itp = Interpreter.from_source(LOOP_SRC)
    snap = _step(itp, {"n": "3"})
    assert snap["s"] == "6" and snap["m"] == "30"
    assert snap["q"] == "-3"          # 向 0 截断，不是 Python 的 -4
    assert snap["r"] == "-1"

    itp2 = Interpreter.from_source(LOOP_SRC)
    assert _step(itp2, {"n": "5"})["m"] == "99"


def test_infinite_loop_is_an_error_not_a_timeout():
    src = """
FUNCTION_BLOCK FB_H
VAR_OUTPUT
    x : INT;
END_VAR
    WHILE TRUE DO
        x := x + 1;
    END_WHILE;
END_FUNCTION_BLOCK
"""
    with pytest.raises(InterpError):
        Interpreter.from_source(src).run_cycle()


# ---------------------------------------------------------------- 不支持的东西要报错

def test_unsupported_var_external_is_rejected():
    src = """
FUNCTION_BLOCK FB_X
VAR_EXTERNAL
    x : INT;
END_VAR
END_FUNCTION_BLOCK
"""
    with pytest.raises(InterpError) as ei:
        Interpreter.from_source(src)
    assert "VAR_EXTERNAL" in str(ei.value)


def test_unknown_variable_reports_line():
    src = """
FUNCTION_BLOCK FB_Y
VAR_OUTPUT
    a : INT;
END_VAR
    a := b + 1;
END_FUNCTION_BLOCK
"""
    with pytest.raises(InterpError) as ei:
        Interpreter.from_source(src).run_cycle()
    assert "未声明的变量" in str(ei.value)


# ---------------------------------------------------------------- 类型转换

TIME_CONV_SRC = """
FUNCTION_BLOCK FB_C
VAR_INPUT
    CycleTime : TIME;
END_VAR
VAR_OUTPUT
    Acc : LTIME;
    Flag : BOOL;
    Ratio : REAL;
END_VAR
VAR
    t : LTIME;
    n : INT;
END_VAR
    t := TIME_TO_LTIME(CycleTime);
    Acc := Acc + t;
    Flag := Acc >= LTIME#40ms;
    n := 3;
    Ratio := INT_TO_REAL(n) / 2.0;
END_FUNCTION_BLOCK
"""


def test_time_to_ltime_and_int_to_real():
    """真实语料里出现过的转换函数（E3_P04 用到 TIME_TO_LTIME），补上后语义要自洽。"""
    itp = Interpreter.from_source(TIME_CONV_SRC)
    snap1 = _step(itp, {"CycleTime": "T#20ms"})
    assert snap1["Acc"] == "T#20ms" and snap1["Flag"] == "FALSE"
    snap2 = _step(itp, {"CycleTime": "T#20ms"})
    assert snap2["Acc"] == "T#40ms" and snap2["Flag"] == "TRUE"
    assert snap2["Ratio"] == "1.5"

    itp2 = Interpreter.from_source(TIME_CONV_SRC)
    snap3 = _step(itp2, {"CycleTime": "T#1s"})
    assert snap3["Acc"] == "T#1000ms" and snap3["Flag"] == "TRUE"


# ---------------------------------------------------------------- 字面量

def test_literal_round_trip():
    w = TypeSpec("scalar", name="WORD")
    assert parse_literal("16#8001", w, {}) == 0x8001
    assert format_value(0x8001, w, {}) == "16#8001"
    t = TypeSpec("scalar", name="TIME")
    assert parse_literal("T#1s500ms", t, {}) == 1500.0
    assert format_value(1500.0, t, {}) == "T#1500ms"
    b = TypeSpec("scalar", name="BOOL")
    assert parse_literal("TRUE", b, {}) is True
    assert format_value(False, b, {}) == "FALSE"


# ---------------------------------------------------------------- CLI 契约

def test_cli_single_case_writes_readable_actual(tmp_path):
    _, cases = load_cases(str(P03_CASES), str(P03_IO))
    case = cases[0]
    inputs = tmp_path / "inputs.csv"
    out = tmp_path / "outputs.csv"
    _write_inputs(inputs, case)

    r = subprocess.run([sys.executable, str(RUN_PY), "--source", str(P03_REF),
                        "--inputs", str(inputs), "--outputs", str(out),
                        "--case-id", case.case_id],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr

    _, _, outs = load_io(str(P03_IO))
    store = ActualStore(out)
    cycles = store.load(case.case_id, [c["cycle"] for c in case.cycles[1:]], outs)
    ok, mm = compare_case(case, cycles)
    assert ok, mm


def test_cli_batch_mode_writes_all_cases(tmp_path):
    out_dir = tmp_path / "actual"
    r = subprocess.run([sys.executable, str(RUN_PY), "--source", str(P03_REF),
                        "--cases", str(P03_CASES), "--io", str(P03_IO),
                        "--out-dir", str(out_dir), "--task", "P03"],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    _, cases = load_cases(str(P03_CASES), str(P03_IO))
    files = sorted(p.name for p in out_dir.glob("*.csv"))
    assert len(files) == len(cases) == 6
    _, _, outs = load_io(str(P03_IO))
    store = ActualStore(out_dir)
    for case in cases:
        cycles = store.load(case.case_id, [c["cycle"] for c in case.cycles[1:]], outs)
        ok, mm = compare_case(case, cycles)
        assert ok, (case.case_id, mm)


def test_cli_reports_error_for_unparsable_source(tmp_path):
    bad = tmp_path / "bad.st"
    bad.write_text("FUNCTION_BLOCK FB_B\nVAR_OUTPUT\n  a : INT;\nEND_VAR\n"
                   "  a := ;\nEND_FUNCTION_BLOCK\n", encoding="utf-8")
    inputs = tmp_path / "in.csv"
    inputs.write_text("cycle\n0\n1\n", encoding="utf-8")
    r = subprocess.run([sys.executable, str(RUN_PY), "--source", str(bad),
                        "--inputs", str(inputs), "--outputs", str(tmp_path / "o.csv")],
                       capture_output=True, text=True)
    assert r.returncode == 2
    assert "解释器错误" in r.stderr

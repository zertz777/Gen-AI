"""执行器单测：加载、比对、失配定位、X 语义、超时三态。"""
import json
import sys
import time
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from runner.case_loader import DONT_CARE, CaseError, load_cases, parse_value  # noqa: E402
from runner.compare import compare_case                                        # noqa: E402
from runner.verdict import TIMEOUT, run_with_timeout                           # noqa: E402

P03 = HERE / "cases" / "P03.csv"
P03IO = HERE / "cases" / "_fixtures" / "P03.io.json"
P07 = HERE / "cases" / "P07.csv"
P07IO = HERE / "cases" / "_fixtures" / "P07.io.json"


def _actual(case):
    return [{"cycle": c["cycle"], "out": dict(c["out"])} for c in case.cycles[1:]]


# ---------- loader ----------

def test_p03_loads_six_cases():
    tid, cases = load_cases(str(P03), str(P03IO))
    assert tid == "P03"
    assert len(cases) == 6
    assert sum(len(c.cycles) for c in cases) == 29
    assert cases[0].cycles[0]["cycle"] == 0


def test_p07_array_literal_parsed():
    tid, cases = load_cases(str(P07), str(P07IO))
    case = cases[0]
    assert case.cycles[0]["in"]["pumpGroup[].selection"] == [False] * 5
    assert case.cycles[6]["out"]["pumpGroup[].RunComd"] == [False, True, True, False, True]


def test_bool_rejects_hex():
    with pytest.raises(CaseError):
        parse_value("16#8002", "BOOL")


def test_time_literal_to_ms():
    assert parse_value("T#500ms", "TIME") == 500.0
    assert parse_value("T#2s", "TIME") == 2000.0


def test_x_rejected_in_input_column(tmp_path):
    bad = tmp_path / "bad.csv"
    bad.write_text(
        "case_id,cycle,spec_refs,purpose,Value,hiLevel,loLevel,hystWindow,"
        "hiAlarm,loAlarm,error,status\n"
        'P03-01,0,"K3","x",X,10,3,2,FALSE,FALSE,FALSE,16#0000\n',
        encoding="utf-8")
    with pytest.raises(CaseError):
        load_cases(str(bad), str(P03IO))


def test_cycle_gap_rejected(tmp_path):
    bad = tmp_path / "gap.csv"
    bad.write_text(
        "case_id,cycle,spec_refs,purpose,Value,hiLevel,loLevel,hystWindow,"
        "hiAlarm,loAlarm,error,status\n"
        'P03-01,0,"K3","x",0,10,3,2,FALSE,FALSE,FALSE,16#0000\n'
        'P03-01,2,"","",5,10,3,2,FALSE,FALSE,FALSE,16#0000\n',
        encoding="utf-8")
    with pytest.raises(CaseError):
        load_cases(str(bad), str(P03IO))


# ---------- compare ----------

def test_dont_care_passes():
    _, cases = load_cases(str(P03), str(P03IO))
    case = cases[3]                     # P03-04 第 1 拍两个报警是 X
    ok, mismatch = compare_case(case, _actual(case))
    assert ok and mismatch is None


def test_first_mismatch_is_located():
    _, cases = load_cases(str(P03), str(P03IO))
    case = cases[0]
    actual = _actual(case)
    actual[1]["out"]["hiAlarm"] = False     # 第 2 拍本该 TRUE
    ok, mm = compare_case(case, actual)
    assert not ok
    assert mm == {"cycle": 2, "variable": "hiAlarm",
                  "expected": True, "actual": False}


def test_cycle_count_mismatch_detected():
    _, cases = load_cases(str(P03), str(P03IO))
    case = cases[0]
    ok, mm = compare_case(case, _actual(case)[:-1])
    assert not ok and mm["variable"] == "<扫描拍数>"


def test_float_tolerance():
    from runner.compare import _eq
    assert _eq(1.0000001, 1.0, 1e-6)
    assert not _eq(1.001, 1.0, 1e-6)


# ---------- verdict ----------

def test_timeout_is_separate_state():
    _, timed_out = run_with_timeout(time.sleep, (0.2,), 0.01)
    assert timed_out


def test_no_timeout_when_fast():
    result, timed_out = run_with_timeout(lambda: 42, (), 1.0)
    assert not timed_out and result == 42


def test_dont_care_sentinel_value():
    assert DONT_CARE == "X"
    assert TIMEOUT == "timeout"


# ---------- io_normalize ----------

from runner.io_normalize import normalize  # noqa: E402


def _card(tid, io):
    return {"task_id": tid, "io_table": io}


def test_p07_flatten_and_container_dropped():
    card = _card("P07", [
        {"name": "mode", "direction": "IN", "data_type": "BOOL"},
        {"name": "pumpGroup", "direction": "INOUT", "data_type": "ARRAY[1..5] OF ST_Pump"},
        {"name": "priority", "direction": "IN", "data_type": "INT"},
        {"name": "RunComd", "direction": "OUT", "data_type": "BOOL"},
    ])
    io = normalize(card)["io"]
    names = [r["name"] for r in io]
    assert names == ["mode", "pumpGroup[].priority", "pumpGroup[].RunComd"]
    assert io[1]["type"] == "ARRAY[1..5] OF INT"      # 子列升一维


def test_p17_recipe_fields_prefixed():
    card = _card("P17", [
        {"name": "recipe", "direction": "INOUT", "data_type": "ARRAY[1..10] OF ST_Recipe"},
        {"name": "recipeID", "direction": "IN", "data_type": "INT"},
    ])
    io = normalize(card)["io"]
    assert [r["name"] for r in io] == ["recipe[].recipeID"]
    assert io[0]["type"] == "ARRAY[1..10] OF INT"


def test_inout_without_children_becomes_input():
    card = _card("P18", [
        {"name": "item", "direction": "INOUT", "data_type": "VARIANT"},
        {"name": "elementCount", "direction": "OUT", "data_type": "DINT"},
    ])
    io = normalize(card)["io"]
    assert io[0]["name"] == "item" and io[0]["direction"] == "IN"


def test_all_34_fixtures_are_wellformed():
    files = sorted((HERE / "cases" / "_fixtures").glob("*.io.json"))
    assert len(files) == 34
    for f in files:
        d = json.loads(f.read_text(encoding="utf-8"))
        dirs = [r["direction"] for r in d["io"]]
        assert dirs.count("IN") >= 1, f.name
        assert dirs.count("OUT") >= 1, f.name
        assert "INOUT" not in dirs, f.name
        names = [r["name"] for r in d["io"]]
        assert len(names) == len(set(names)), f.name


# ---------- 全量用例 ----------

def test_every_case_file_loads():
    files = sorted(list((HERE / "cases").glob("P*.csv"))
                   + list((HERE / "cases").glob("S*.csv")))
    assert len(files) == 34, [f.name for f in files]
    for f in files:
        tid = f.stem
        _, cases = load_cases(str(f), str(HERE / "cases" / "_fixtures" / (tid + ".io.json")))
        assert cases, f.name
        for c in cases:
            assert c.cycles[0]["cycle"] == 0
            assert len(c.spec_refs) >= 1
            assert c.purpose.strip()


# ---------- 用例分类（任务书 T4.2） ----------

CATS = ("正常", "边界", "异常", "安全")


def _all_cases():
    for f in sorted(list((HERE / "cases").glob("P*.csv"))
                    + list((HERE / "cases").glob("S*.csv"))):
        _, cases = load_cases(str(f), str(HERE / "cases" / "_fixtures" / (f.stem + ".io.json")))
        for c in cases:
            yield f.stem, c


def test_every_case_has_valid_category():
    seen = set()
    for tid, c in _all_cases():
        assert c.category in CATS, (tid, c.case_id, c.category)
        seen.add(c.category)
    assert seen == set(CATS), seen          # 四类必须齐


def test_every_task_has_four_categories():
    """T4.2 的字面要求：逐题四类齐，不是全局齐。"""
    from collections import defaultdict
    per = defaultdict(set)
    for tid, c in _all_cases():
        per[tid].add(c.category)
    missing = {t: sorted(set(CATS) - cats) for t, cats in per.items() if set(CATS) - cats}
    assert not missing, missing


def test_case_count_at_least_150():
    n = sum(1 for _ in _all_cases())
    assert n >= 150, n


def test_no_all_dont_care_case():
    """一条用例所有输出都写 X 等于没测，直接拦掉。"""
    for tid, c in _all_cases():
        outs = [v for cyc in c.cycles[1:] for v in cyc["out"].values()]
        assert any(v != "X" for v in outs), (tid, c.case_id)


def test_every_task_has_a_safety_case():
    from collections import defaultdict
    per = defaultdict(set)
    for tid, c in _all_cases():
        per[tid].add(c.category)
    missing = sorted(t for t in per if "安全" not in per[t])
    assert not missing, missing


def test_each_task_has_at_least_four_cases():
    from collections import Counter
    n = Counter(tid for tid, _ in _all_cases())
    few = sorted(t for t, k in n.items() if k < 4)
    assert not few, few


def test_coverage_index_matches_constraints():
    import csv
    rows = list(csv.DictReader(
        (HERE / "coverage.csv").open(encoding="utf-8-sig")))
    assert len(rows) == 143
    assert {r["task_id"] for r in rows} == {
        "P%02d" % i for i in range(1, 21)} | {"S%02d" % i for i in range(1, 15)}
    assert all(r["status"] in ("已覆盖", "未覆盖") for r in rows)


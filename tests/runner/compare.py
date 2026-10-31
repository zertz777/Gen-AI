"""逐周期比对，返回首个失配的周期号 / 变量 / 期望值 / 实际值。"""
from __future__ import annotations

from .case_loader import DONT_CARE


def _eq(expected, actual, tol):
    if expected == DONT_CARE:
        return True
    if isinstance(expected, bool) or isinstance(actual, bool):
        return expected is actual
    if isinstance(expected, float) or isinstance(actual, float):
        try:
            e, a = float(expected), float(actual)
        except (TypeError, ValueError):
            return False
        return abs(e - a) <= max(tol, tol * abs(e))
    if isinstance(expected, list):
        if not isinstance(actual, list) or len(expected) != len(actual):
            return False
        return all(_eq(x, y, tol) for x, y in zip(expected, actual))
    return expected == actual


def compare_case(case, actual_cycles, tol=1e-6):
    """actual_cycles: [{"cycle": 1, "out": {...}}, ...]

    返回 (ok, mismatch)。mismatch = {cycle, variable, expected, actual} 或 None。
    cycle=0 是初态行，不参与比对。
    """
    expected = case.cycles[1:]
    if len(actual_cycles) != len(expected):
        return False, {
            "cycle": len(actual_cycles) + 1,
            "variable": "<扫描拍数>",
            "expected": len(expected),
            "actual": len(actual_cycles),
        }
    for exp, act in zip(expected, actual_cycles):
        for name, e_val in exp["out"].items():
            a_val = act["out"].get(name, "<缺失>")
            if not _eq(e_val, a_val, tol):
                return False, {
                    "cycle": exp["cycle"],
                    "variable": name,
                    "expected": e_val,
                    "actual": a_val,
                }
    return True, None

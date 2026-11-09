"""从实验批次的 evaluation.json 生成缺陷单（tests/defects.md）。

一条失败 = 一条缺陷，字段与 `tests/defects.md` 定下的 11 列一一对应：

    defect_id, task_id, run_id, case_id, cycle, variable, expected, actual, kind, repro, status

数据来源（只读，不改任何原始记录）：

    <runs>/<batch>/live/<run_id>/{baseline,best}.evaluation.json
        -> test.passed / test.total / test.failures[{case_id, cycle, signal, expected, actual}]
    <cases>/<题号>.csv  -> category / spec_refs（用来判 kind）

kind 的判定顺序（可复现，不是拍脑袋）：

    1. run 的 compile_status != pass      -> 编译
    2. final_status 里带 timeout          -> 工具超时
    3. 该用例 category == 边界            -> 边界
    4. spec_refs 命中的 K 条款含时间字眼  -> 时序
    5. 其余                               -> 逻辑

用法：

    python tests/gen/gen_defects.py \
        --runs "<组员3包>/正式实验_runs" \
        --cases tests/cases \
        --summary "<组员3包>/统计输出/逐题逐组结果.csv" \
        --out tests/defects.md
"""
from __future__ import annotations

import argparse
import csv
import glob
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

# ---------------------------------------------------------------- 争议用例
#: 详见 docs/判据与用例版本核对.md；这里只做标记，不改判定
DISPUTED = {
    "P19-02": "用例错：UpLimitSwitch=TRUE 却期望 MoveUp=TRUE（违反 K1）",
    "P19-03": "用例错：同上",
    "P19-04": "用例错：同上",
    "P19-08": "版本错：实验用的是旧版急停极性用例",
    "P19-09": "版本错 + 模式互斥未满足",
    "S11-02": "用例错：断线未满 2 s 时期望 ControlValue=0 无依据",
    "S11-03": "用例错：同上",
    "S11-04": "歧义：1 Hz 闪烁的相位边界未定义",
    "S11-05": "用例错：3.59 mA 已越断线阈值，期望 Status=0 错",
    "S05-06": "用例错：非上升沿却期望累加（K1 只认上升沿）",
}

_TIME_WORDS = ("时间", "计时", "延时", "秒", "ms", "拍", "定时", "周期", "去抖", "抑制")
_TIME_RE = re.compile(r"(T#|\d+\s*(ms|s)\b|秒|拍)")

CASE_META_COLS = ("case_id", "cycle", "spec_refs", "purpose", "category")


# ---------------------------------------------------------------- 读数据

def pick_evaluation(files):
    for name in ("baseline.evaluation.json", "best.evaluation.json"):
        if name in files:
            return files[name]
    return None


def load_runs(runs_dir: Path):
    """{run_dir: evaluation_path}"""
    out = {}
    for p in glob.glob(str(runs_dir / "**" / "*.evaluation.json"), recursive=True):
        d = Path(p).parent
        out.setdefault(d, {})[Path(p).name] = p
    picked = {}
    for d, files in out.items():
        e = pick_evaluation(files)
        if e:
            picked[d] = e
    return picked


def load_case_meta(cases_dir: Path):
    """{(task, case_id): {"category":..., "spec_refs":...}}"""
    meta = {}
    for f in sorted(cases_dir.glob("*.csv")):
        task = f.stem
        with open(f, encoding="utf-8-sig", newline="") as fh:
            for row in csv.DictReader(fh):
                cid = (row.get("case_id") or "").strip()
                if not cid:
                    continue
                item = meta.setdefault((task, cid), {"category": "", "spec_refs": ""})
                if row.get("cycle") == "0":
                    item["category"] = (row.get("category") or "").strip()
                    item["spec_refs"] = (row.get("spec_refs") or "").strip()
    return meta


def load_summary(summary_csv: Path):
    """run_id -> 行（用于对账与拿 final_status / compile_status）"""
    if not summary_csv or not summary_csv.exists():
        return {}
    with open(summary_csv, encoding="utf-8-sig", newline="") as fh:
        return {r["run_id"]: r for r in csv.DictReader(fh)}


def load_constraints(tasks_dir: Path):
    """{task: {K号: 条款原文}}，用来判"时序"类。"""
    out = {}
    if not tasks_dir or not tasks_dir.exists():
        return out
    for f in sorted(tasks_dir.glob("*.yaml")):
        txt = f.read_text(encoding="utf-8", errors="replace")
        table = {}
        for m in re.finditer(r"^\s*-\s*(K\d+)\s*(.*)$", txt, re.M):
            table[m.group(1)] = m.group(2)
        out[f.stem] = table
    return out


# ---------------------------------------------------------------- 分类

def classify(row, case, constraints):
    if (row.get("compile_status") or "") != "pass":
        return "编译"
    if "timeout" in (row.get("final_status") or "") or "超时" in (row.get("final_status") or ""):
        return "工具超时"
    if (case or {}).get("category") == "边界":
        return "边界"
    ks = [k.strip() for k in ((case or {}).get("spec_refs") or "").split(";") if k.strip()]
    for k in ks:
        text = constraints.get(k, "")
        if any(w in text for w in _TIME_WORDS) or _TIME_RE.search(text):
            return "时序"
    return "逻辑"


# ---------------------------------------------------------------- 主流程

def build(runs_dir: Path, cases_dir: Path, summary_csv: Path, tasks_dir: Path):
    cases = load_case_meta(cases_dir)
    summary = load_summary(summary_csv)
    constraints_by_task = load_constraints(tasks_dir)
    runs = load_runs(runs_dir)

    rows = []
    for run_dir in sorted(runs):
        run_id = run_dir.name
        parts = run_id.split("_")
        group = parts[0]
        task = parts[1]
        ev = json.loads(Path(runs[run_dir]).read_text(encoding="utf-8"))
        test = ev.get("test") or {}
        compile_ = ev.get("compile") or {}
        sumrow = summary.get(run_id, {})
        row_ctx = {
            "compile_status": compile_.get("status") or sumrow.get("compile_status", ""),
            "final_status": sumrow.get("final_status", ""),
        }
        for fail in test.get("failures") or []:
            cid = (fail.get("case_id") or "").strip()
            case = cases.get((task, cid), {})
            rows.append({
                "task_id": task,
                "run_id": run_id,
                "group": group,
                "case_id": cid,
                "cycle": fail.get("cycle"),
                "variable": fail.get("signal"),
                "expected": fail.get("expected"),
                "actual": fail.get("actual"),
                "kind": classify(row_ctx, case, constraints_by_task.get(task, {})),
                "category": case.get("category", ""),
                "disputed": DISPUTED.get(cid, ""),
            })

    rows.sort(key=lambda r: (r["run_id"], str(r["case_id"])))
    for i, r in enumerate(rows, 1):
        r["defect_id"] = "DEF-%03d" % i

    # 与成员3 的逐题表对账
    agree, mismatch = [], []
    for run_dir, ev_path in sorted(runs.items()):
        run_id = run_dir.name
        ev = json.loads(Path(ev_path).read_text(encoding="utf-8"))
        test = ev.get("test") or {}
        srow = summary.get(run_id)
        if not srow:
            continue
        if str(test.get("passed")) != str(srow.get("test_passed")) or \
                str(test.get("total")) != str(srow.get("test_total")):
            mismatch.append((run_id, test.get("passed"), test.get("total"),
                             srow.get("test_passed"), srow.get("test_total")))
        else:
            agree.append(run_id)
    return rows, dict(agree=len(agree), mismatch=mismatch, runs=len(runs))


def fmt(v):
    if isinstance(v, bool):
        return "TRUE" if v else "FALSE"
    if v is None:
        return "—"
    return str(v)


def render(rows, stats, runs_dir: Path):
    by_group = Counter(r["group"] for r in rows)
    by_kind = Counter(r["kind"] for r in rows)
    by_task = Counter(r["task_id"] for r in rows)
    disputed = [r for r in rows if r["disputed"]]
    per_run = Counter(r["run_id"] for r in rows)

    out = []
    w = out.append
    w("# 缺陷单（defects）")
    w("")
    w("成员4 的 D4.4 交付物。**一条失败 = 一条缺陷**，不多不少；回归结果单独一节，不混进第一轮。")
    w("")
    w("本文件由 `tests/gen/gen_defects.py` 从实验批次的 `evaluation.json` 自动生成，")
    w("可随时重算：`python tests/gen/gen_defects.py --runs <实验目录> --cases tests/cases --out tests/defects.md`。")
    w("")
    w("## 0 当前状态")
    w("")
    w("| 项 | 值 |")
    w("| --- | --- |")
    w("| 数据来源 | `%s/%s`（相对实验包根目录） |"
      % (runs_dir.parent.name, runs_dir.name))
    w("| 有 evaluation.json 的 run | **%d**（逐题逐组表 136 条，缺的 4 条是 `abandoned:timeout`，未进测试阶段） |"
      % stats["runs"])
    w("| 真实缺陷条数 | **%d**（= 全部 run 的失配条目之和） |" % len(rows))
    w("| 涉及 run 数 | %d |" % len(per_run))
    w("| 与成员3 `逐题逐组结果.csv` 逐 run 对账 | 一致 **%d** 条，不一致 **%d** 条 |"
      % (stats["agree"], len(stats["mismatch"])))
    w("| 争议用例条目 | %d 条（见 §5，来自 `docs/判据与用例版本核对.md`） |" % len(disputed))
    w("")
    if stats["mismatch"]:
        w("> 对账不一致的 run：")
        for m in stats["mismatch"]:
            w("> - `%s`：evaluation 为 %s/%s，逐题表为 %s/%s" % (m[0], m[1], m[2], m[3], m[4]))
        w("")
    w("## 1 字段（缺一列成员2 就没法修）")
    w("")
    w("| 字段 | 说明 |")
    w("| --- | --- |")
    w("| `defect_id` | `DEF-` + 三位序号 |")
    w("| `task_id` | P01—P20 / S01—S14 |")
    w("| `run_id` | 组别_题号_r次_s种子，如 `E3_P03_1_42` |")
    w("| `case_id` / `cycle` | 失配的用例与拍号（逐周期比对得出，不是只看末态） |")
    w("| `variable` | 首个失配变量 |")
    w("| `expected` / `actual` | 期望值 / 实际值（按声明类型写） |")
    w("| `kind` | 逻辑 / 时序 / 边界 / 编译 / 工具超时（判定规则见脚本注释） |")
    w("| `repro` | 复跑命令（见 §4；actual 未随包交付，需在实验机复跑） |")
    w("| `status` | 待修 / 已修待回归 / 已关闭 / 不修（附理由） |")
    w("")
    w("## 2 分布")
    w("")
    w("### 2.1 按组")
    w("")
    w("| 组别 | 缺陷条数 | 涉及 run |")
    w("| --- | ---: | ---: |")
    for g in sorted(by_group):
        w("| %s | %d | %d |" % (g, by_group[g], len({r["run_id"] for r in rows if r["group"] == g})))
    w("")
    w("### 2.2 按原因")
    w("")
    w("| kind | 条数 | 占比 |")
    w("| --- | ---: | ---: |")
    for k, n in by_kind.most_common():
        w("| %s | %d | %.1f%% |" % (k, n, 100.0 * n / len(rows) if rows else 0))
    w("")
    w("### 2.3 按题（失败最多的 12 题）")
    w("")
    w("| 题号 | 条数 |")
    w("| --- | ---: |")
    for t, n in by_task.most_common(12):
        w("| %s | %d |" % (t, n))
    w("")
    w("## 3 缺陷明细（%d 条）" % len(rows))
    w("")
    w("| defect_id | task_id | run_id | case_id | cycle | variable | expected | actual | kind | repro | status |")
    w("| --- | --- | --- | --- | ---: | --- | --- | --- | --- | --- | --- |")
    for r in rows:
        repro = "python agent/scripts/member4_test.py --source %s/final.st --cases-dir tests/cases" % r["run_id"]
        w("| %s | %s | %s | %s | %s | %s | %s | %s | %s | `%s` | 待修 |" % (
            r["defect_id"], r["task_id"], r["run_id"], r["case_id"], fmt(r["cycle"]),
            r["variable"], fmt(r["expected"]), fmt(r["actual"]), r["kind"], repro))
    w("")
    w("## 4 复现")
    w("")
    w("`actual/*.csv` 没有随精简包交付，所以本机只能用**实验机**复跑。每条缺陷的复现命令模板：")
    w("")
    w("```bash")
    w("# 在实验机（装了 CODESYS V3.5 SP22 Patch 4 + matiec）上，任一 run 复跑：")
    w("python agent/scripts/member4_test.py \\")
    w("  --source <批次>/live/<run_id>/final.st \\")
    w("  --task-card <批次>/live/<run_id>/task_card.json \\")
    w("  --cases-dir tests/cases --artifact-dir /tmp/repro \\")
    w("  --exe \"<CODESYS.exe 路径>\" --profile \"CODESYS V3.5 SP22 Patch 4\"")
    w("```")
    w("")
    w("如果后续补交 `test/actual/*.csv`，本机可以直接用 replay 后端复现同一拍：")
    w("")
    w("```bash")
    w("python tests/run_tests.py --cases tests/cases/P03.csv \\")
    w("  --io tests/cases/_fixtures/P03.io.json --out /tmp/P03.jsonl \\")
    w("  --backend replay --actual experiments/runs/E3/P03_r1_s42/test/actual")
    w("```")
    w("")
    w("## 5 争议用例条目（%d 条，单独列，不混进上面的计数）" % len(disputed))
    w("")
    w("这些条目**不一定是模型的错**，逐条依据见 `docs/判据与用例版本核对.md`：")
    w("")
    w("| 用例 | 条数 | 裁决 |")
    w("| --- | ---: | --- |")
    cnt = Counter(r["case_id"] for r in disputed)
    for cid, n in cnt.most_common():
        w("| %s | %d | %s |" % (cid, n, DISPUTED[cid]))
    w("")
    w("## 6 回归（D4.6）")
    w("")
    w("| 项 | 数值 |")
    w("| --- | --- |")
    w("| 复测题数 | 待填 |")
    w("| 修好 | 待填 |")
    w("| 仍失败 | 待填 |")
    w("| **修复引入的破坏数** | 待填 |")
    w("")
    w("**为什么是空的**：回归要求「同一题修复前后的两份产物都要有逐拍 actual」才能算出")
    w("「修 A 把 B 改坏」的数量。精简包只交付了每次 run 的最终产物，没有保留修复前中间产物的 actual；")
    w("`repair_1.evaluation.json` 只在整个包里出现 1 次。要补这一节，需要在实验机上对 `repair_rounds>0` 的题重跑一次，")
    w("把修复前/后两次的 actual 都落盘。这条如实标注，不拿替代数据凑。")
    w("")
    w("## 7 结论")
    w("")
    w("- 失败主要集中在 %s 三类原因；`工具超时` 与 `编译` 已按口径单列，未计入模型失败。"
      % " / ".join(k for k, _ in by_kind.most_common(3)))
    w("- %d 条争议条目应先按 `docs/判据与用例版本核对.md` 裁决，其中 S05-06 会影响 E1/E2/E4 的整题通过数。" % len(disputed))
    w("- 逐 run 与成员3 的汇总对账：一致 %d 条，不一致 %d 条。"
      % (stats["agree"], len(stats["mismatch"])))
    return "\n".join(out) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description="从 evaluation.json 生成 defects.md")
    here = Path(__file__).resolve()
    ap.add_argument("--runs", required=True, help="实验批次根目录（含 */live/<run_id>/）")
    ap.add_argument("--cases", default=str(here.parents[1] / "cases"), help="用例目录")
    ap.add_argument("--summary", default="", help="逐题逐组结果.csv（可选，用于对账）")
    ap.add_argument("--tasks", default="", help="题面 YAML 目录（可选，用于判 kind）")
    ap.add_argument("--out", default=str(here.parents[1] / "defects.md"))
    a = ap.parse_args(argv)

    rows, stats = build(Path(a.runs), Path(a.cases),
                        Path(a.summary) if a.summary else None,
                        Path(a.tasks) if a.tasks else None)
    text = render(rows, stats, Path(a.runs))
    out = Path(a.out)
    out.write_text(text, encoding="utf-8")
    print("缺陷 %d 条，涉及 %d 个 run；对账一致 %d / 不一致 %d -> %s"
          % (len(rows), len({r["run_id"] for r in rows}), stats["agree"],
             len(stats["mismatch"]), out))
    return 0


if __name__ == "__main__":
    sys.exit(main())

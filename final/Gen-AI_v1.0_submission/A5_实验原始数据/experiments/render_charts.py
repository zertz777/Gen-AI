"""Render four 300 dpi charts from the verified 34 x 4 result table."""

from __future__ import annotations

import argparse
import csv
import statistics
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
TASKS = ROOT / "data" / "tasks"
SETTINGS = ("E1", "E2", "E3", "E4")
COLORS = ("#2670A8", "#4C9CBA", "#D68642", "#C25454")


def read_rows(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != 136:
        raise ValueError(f"Expected 136 result rows, found {len(rows)}")
    return rows


def task_difficulty(task_id: str) -> str:
    for line in (TASKS / f"{task_id}.yaml").read_text(encoding="utf-8").splitlines():
        if line.startswith("difficulty:"):
            return line.split(":", 1)[1].strip()
    raise ValueError(f"Missing difficulty for {task_id}")


def save(fig, out: Path, filename: str) -> None:
    fig.tight_layout()
    fig.savefig(out / filename, dpi=300, bbox_inches="tight")
    fig.savefig(out / (Path(filename).stem + ".svg"), bbox_inches="tight")
    plt.close(fig)


def render(table: Path, out: Path) -> None:
    rows = read_rows(table)
    out.mkdir(parents=True, exist_ok=True)
    plt.rcParams["font.family"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False
    by_group = {setting: [r for r in rows if r["setting_id"] == setting]
                for setting in SETTINGS}
    if any(len(group) != 34 for group in by_group.values()):
        raise ValueError("Each experimental group must contain 34 tasks")

    # 1. Strict full-task pass count.
    passed = [sum(r["final_status"] == "passed" for r in by_group[s]) for s in SETTINGS]
    fig, ax = plt.subplots(figsize=(6.6, 4.2))
    bars = ax.bar(SETTINGS, passed, color=COLORS)
    ax.bar_label(bars, labels=[f"{n}/34" for n in passed], padding=3)
    ax.set_ylim(0, 36)
    ax.set_ylabel("整题通过数")
    ax.set_title("四组全部用例通过的题数")
    save(fig, out, "fig4-1_strict_pass.png")

    # 2. Pass rates by task difficulty, using the same task IDs in every group.
    difficulty = {r["task_id"]: task_difficulty(r["task_id"]) for r in rows}
    levels = ("easy", "medium", "hard")
    fig, ax = plt.subplots(figsize=(8.4, 4.6))
    width = 0.18
    for i, setting in enumerate(SETTINGS):
        values = []
        for level in levels:
            subset = [r for r in by_group[setting] if difficulty[r["task_id"]] == level]
            values.append(100 * sum(r["final_status"] == "passed" for r in subset) / len(subset))
        ax.bar([x + (i - 1.5) * width for x in range(3)], values,
               width=width, label=setting, color=COLORS[i])
    ax.set_xticks(range(3), ["易", "中", "难"])
    ax.set_ylim(0, 105)
    ax.set_ylabel("整题通过率（%）")
    ax.set_title("按难度分层的四组结果")
    ax.legend(ncol=4)
    save(fig, out, "fig4-2_difficulty.png")

    # 3. Raw terminal status categories; this does not hide tool and budget stops.
    def category(status: str) -> str:
        if status == "passed":
            return "全部用例通过"
        if status.startswith("best-effort:test_fail"):
            return "功能用例未全过"
        if "budget" in status:
            return "预算终止"
        if "timeout" in status:
            return "超时"
        if "tool_error" in status:
            return "工具错误"
        if "compile_fail" in status:
            return "编译失败"
        return "其他状态"
    labels = ("全部用例通过", "功能用例未全过", "预算终止", "超时", "工具错误", "编译失败", "其他状态")
    palette = ("#4B9C76", "#DCA75C", "#BD6F63", "#8D79AE", "#718BA2", "#A85454", "#B0B0B0")
    fig, ax = plt.subplots(figsize=(8.7, 4.8))
    bottom = [0] * 4
    for label, color in zip(labels, palette):
        counts = [sum(category(r["final_status"]) == label for r in by_group[s]) for s in SETTINGS]
        if any(counts):
            ax.bar(SETTINGS, counts, bottom=bottom, label=label, color=color)
            bottom = [x + y for x, y in zip(bottom, counts)]
    ax.set_ylim(0, 36)
    ax.set_ylabel("题数")
    ax.set_title("各组终态分布（每组 34 题）")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=3)
    save(fig, out, "fig4-3_status.png")

    # 4. End-to-end run time. Keep timeout observations visible in the table.
    medians = []
    p95s = []
    for setting in SETTINGS:
        samples = sorted(float(r["latency_s"]) for r in by_group[setting]
                         if r["latency_s"] not in ("", None))
        medians.append(statistics.median(samples))
        position = 0.95 * (len(samples) - 1)
        low = int(position)
        high = min(low + 1, len(samples) - 1)
        p95s.append(samples[low] + (samples[high] - samples[low]) * (position - low))
    fig, ax = plt.subplots(figsize=(7.8, 4.3))
    x = range(4)
    ax.bar([i - 0.18 for i in x], medians, width=0.36, label="中位数", color="#2670A8")
    ax.bar([i + 0.18 for i in x], p95s, width=0.36, label="p95", color="#D68642")
    ax.set_xticks(list(x), SETTINGS)
    ax.set_ylabel("端到端耗时（秒）")
    ax.set_title("单题运行耗时分布")
    ax.legend()
    save(fig, out, "fig4-4_latency.png")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--table", type=Path, default=ROOT / "experiments" / "per_task.csv")
    parser.add_argument("--out", type=Path, default=ROOT / "figures")
    args = parser.parse_args()
    if not args.table.is_file():
        parser.error("Final table is missing; run finalize_results.py --final after all 32 reruns complete")
    render(args.table, args.out)
    print(f"Four charts written to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

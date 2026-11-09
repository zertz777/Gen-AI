"""Generate the per-task LTL specification appendix used by the report."""
from __future__ import annotations

import re
from pathlib import Path

from yaml_io import load


ROOT = Path(__file__).resolve().parents[1]
TASKS = ROOT / "data" / "tasks"
SPECS = ROOT / "data" / "specs"
OUTPUT = ROOT / "docs" / "report" / "appendix_specs.md"


def task_lines(task_id: str) -> list[str]:
    task = load(TASKS / f"{task_id}.yaml")
    spec_path = SPECS / f"{task_id}.ltl"
    clauses = [
        line.rstrip()
        for line in spec_path.read_text(encoding="utf-8").splitlines()
        if re.match(r"^C\d+[a-z]?:", line)
    ]
    return [
        f"### {task_id}　{task['title']}",
        "",
        f"难度：{task['difficulty']}；类别：{task['category']}；"
        f"I/O：{len(task.get('io_table', []))}；规约：`data/specs/{task_id}.ltl`。",
        "",
        "```text",
        *clauses,
        "```",
        "",
    ]


def main() -> int:
    task_ids = sorted(path.stem for path in TASKS.glob("*.yaml"))
    if len(task_ids) != 34:
        raise ValueError(f"Expected 34 tasks, found {len(task_ids)}")

    lines = [
        "# 附录 A　逐题形式化规约",
        "",
        "本附录列出冻结数据中的全部 34 份 LTL 规约。每条公式保留条款号、时序表达式、验收口径与 K 约束引用；"
        "完整文件位于 `data/specs/<task_id>.ltl`。",
        "",
        "## A.1　公共题 P01-P20",
        "",
    ]
    for task_id in [f"P{i:02d}" for i in range(1, 21)]:
        lines.extend(task_lines(task_id))
    lines.extend(["## A.2　自编题 S01-S14", ""])
    for task_id in [f"S{i:02d}" for i in range(1, 15)]:
        lines.extend(task_lines(task_id))

    OUTPUT.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(OUTPUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

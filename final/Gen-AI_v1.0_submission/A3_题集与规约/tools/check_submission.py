"""Run the 12 submission checks from the member-5 delivery checklist."""
from __future__ import annotations

import csv
import json
import re
import sys
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FINAL_TREE = ROOT / "final" / "Gen-AI_v1.0_submission"
FINAL_ZIP = ROOT / "final" / "Gen-AI_v1.0_submission.zip"
SECRET_PATTERNS = (
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"Authorization\s*[:=]\s*Bearer\s+[A-Za-z0-9._-]{10,}", re.I),
    re.compile(r"""(?:API_KEY|SECRET_KEY|ACCESS_TOKEN)\s*[:=]\s*["']?[A-Za-z0-9._-]{12,}""", re.I),
)
ABSOLUTE_PATH_PATTERNS = (
    re.compile(r"(?<![A-Za-z])[A-Z]:[\\/](?:Users|Documents|Program Files|Windows|MWORKS)"),
    re.compile(r"/(?:home|Users)/[^/\s]+/"),
)
TEMP_SUFFIXES = {".tmp", ".bak", ".swp", ".pyc", ".pyo"}
TEXT_SUFFIXES = {
    ".md",
    ".txt",
    ".py",
    ".yaml",
    ".yml",
    ".json",
    ".csv",
    ".toml",
    ".ini",
    ".cfg",
}


def check(condition: bool, label: str, detail: str) -> dict:
    return {"ok": bool(condition), "label": label, "detail": detail}


def count_cases() -> tuple[int, int, bool]:
    total = 0
    security_tasks = 0
    files = sorted((ROOT / "tests" / "cases").glob("P*.csv"))
    files += sorted((ROOT / "tests" / "cases").glob("S*.csv"))
    for path in files:
        with path.open(encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.DictReader(handle))
        cases = {row["case_id"] for row in rows if row.get("case_id")}
        total += len(cases)
        if any(row.get("category") == "安全" for row in rows):
            security_tasks += 1
    return total, security_tasks, len(files) == 34


def scan_delivery() -> tuple[list[str], list[str], list[str]]:
    secrets: list[str] = []
    absolute_paths: list[str] = []
    temp_files: list[str] = []
    for path in FINAL_TREE.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(FINAL_TREE).as_posix()
        if path.suffix.lower() in TEMP_SUFFIXES or path.name.startswith("~$"):
            temp_files.append(relative)
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if any(pattern.search(text) for pattern in SECRET_PATTERNS):
            secrets.append(relative)
        if any(pattern.search(text) for pattern in ABSOLUTE_PATH_PATTERNS):
            absolute_paths.append(relative)
    return secrets, absolute_paths, temp_files


def main() -> int:
    results: list[dict] = []
    task_files = sorted((ROOT / "data" / "tasks").glob("*.yaml"))
    spec_files = sorted((ROOT / "data" / "specs").glob("*.ltl"))
    results.append(check(len(task_files) == 34, "32/34题题面齐全", f"{len(task_files)} 份题面"))
    results.append(check(len(spec_files) == 34, "规约与题面一一对应", f"{len(spec_files)} 份规约"))

    with (ROOT / "data" / "provenance.csv").open(encoding="utf-8-sig", newline="") as handle:
        provenance_rows = list(csv.DictReader(handle))
    results.append(check(len(provenance_rows) == 34, "来源表完整", f"{len(provenance_rows)} 行"))

    results.append(
        check(
            (ROOT / "agent" / "run.py").is_file(),
            "框架单题入口存在",
            "agent/run.py",
        )
    )
    log_fields = set()
    for path in (ROOT / "experiments" / "runs").glob("E*/*/result.json"):
        log_fields = set(json.loads(path.read_text(encoding="utf-8-sig")))
        break
    results.append(
        check(len(log_fields) == 22, "结果日志为22字段", f"{len(log_fields)} fields")
    )

    config_files = sorted((ROOT / "experiments" / "configs").glob("E*.yaml"))
    results.append(check(len(config_files) == 4, "四组配置齐全", f"{len(config_files)} 份"))

    run_results = sorted((ROOT / "experiments" / "runs").glob("E*/*/result.json"))
    tasks_by_setting = {
        setting: {path.parent.name.split("_")[1] for path in run_results if path.parent.parent.name == setting}
        for setting in ("E1", "E2", "E3", "E4")
    }
    results.append(
        check(
            len(run_results) == 136 and all(len(tasks) == 34 for tasks in tasks_by_setting.values()),
            "136份最终运行记录齐全",
            f"{len(run_results)} result.json",
        )
    )
    results.append(
        check((ROOT / "tools" / "stats.py").is_file(), "summary可由stats.py重算", "tools/stats.py")
    )

    case_count, security_tasks, task_files_ok = count_cases()
    results.append(
        check(
            case_count >= 150 and security_tasks == 34 and task_files_ok,
            "用例≥150且每题有安全用例",
            f"{case_count} cases, {security_tasks}/34 security tasks",
        )
    )
    defects = (ROOT / "tests" / "defects.md").read_text(encoding="utf-8")
    cycle_rows = len(re.findall(r"^\|\s*DEF-\d+\s*\|", defects, re.MULTILINE))
    reproduction = ROOT / "experiments" / "reproduction" / "summary.jsonl"
    reproduced = 0
    if reproduction.is_file():
        reproduced = sum(
            json.loads(line).get("replay_status") == "completed"
            for line in reproduction.read_text(encoding="utf-8").splitlines()
            if line.strip()
        )
    results.append(
        check(
            cycle_rows >= 100 and reproduction.is_file(),
            "失败可定位到周期号",
            f"{cycle_rows} defect rows with cycle field; {reproduced} independent replays",
        )
    )

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    required_commands = (
        "pip install -r requirements.txt",
        "python agent/run.py --framework self --model fixture --tasks data/tasks/S01.yaml",
        "python agent/run.py --framework self --model fixture --tasks data/tasks --task-set all34",
    )
    command_count = sum(command in readme for command in required_commands)
    results.append(
        check(command_count == 3, "README三条命令", f"{command_count} core command lines")
    )

    delivery_ok = FINAL_TREE.is_dir() and FINAL_ZIP.is_file()
    if delivery_ok:
        secrets, absolute_paths, temp_files = scan_delivery()
        detail = (
            f"secrets={len(secrets)}, absolute_paths={len(absolute_paths)}, "
            f"temp={len(temp_files)}"
        )
        delivery_ok = not any((secrets, absolute_paths, temp_files))
    else:
        secrets, absolute_paths, temp_files = [], [], []
        detail = "final tree or zip missing"
    results.append(
        check(delivery_ok, "提交包无key、绝对路径或临时文件", detail)
    )

    report = {
        "ok": all(item["ok"] for item in results),
        "checks": results,
        "scan": {
            "secret_files": secrets,
            "absolute_path_files": absolute_paths,
            "temporary_files": temp_files,
        },
    }
    output = ROOT / "checklist.json"
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    for item in results:
        print(("PASS" if item["ok"] else "FAIL"), item["label"], "-", item["detail"])
    print(f"report: {output}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

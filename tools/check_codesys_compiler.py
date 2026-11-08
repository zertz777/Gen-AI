"""仅做真实CODESYS编译验收；一次IDE启动，默认6个诊断探针，可附全部题面骨架。"""
from __future__ import annotations
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from agent.src.parse import parse_task
from agent.src.task_card import make_skeleton
from agent.src.tools import run_process, normalize_errors


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def resolve(value, root):
    path = Path(value)
    return path.resolve() if path.is_absolute() else (root / path).resolve()


def parse_bridge_config(config, root=ROOT):
    """严格识别configure_codesys生成的argv；不执行/解释任意工具命令。"""
    try:
        command = config["tools"]["authoritative"]["command"]
    except (KeyError, TypeError):
        raise ValueError("配置缺少tools.authoritative.command") from None
    if not isinstance(command, list) or len(command) < 2 or not all(isinstance(value, str) for value in command):
        raise ValueError("仅支持configure_codesys生成的bridge argv数组")
    if resolve(command[1], root) != (root / "agent/scripts/codesys_bridge.py").resolve():
        raise ValueError("不支持其他编译命令；请先使用tools/configure_codesys.py生成配置")
    if not resolve(command[0], root).is_file():
        raise ValueError("配置中的Python启动器不存在")
    args = command[2:]
    allowed = {"--source", "--result", "--task-card", "--exe", "--profile", "--template", "--application", "--additionalfolder"}
    if len(args) % 2:
        raise ValueError("bridge参数必须是明确的名称/值对")
    values = {}
    for flag, value in zip(args[::2], args[1::2]):
        if flag not in allowed or flag in values or not value or any(ord(c) < 32 for c in value):
            raise ValueError("bridge包含未知、重复、空或非法参数")
        values[flag] = value
    required = allowed - {"--additionalfolder"}
    if not required.issubset(values):
        raise ValueError("bridge配置缺少必需参数")
    for flag, placeholder in (("--source", "{source}"), ("--result", "{result}"), ("--task-card", "{task_card}")):
        if values[flag] != placeholder:
            raise ValueError("bridge占位符不匹配：" + flag)
    result = {"exe": resolve(values["--exe"], root), "template": resolve(values["--template"], root),
              "profile": values["--profile"], "application": values["--application"],
              "additionalfolder": resolve(values["--additionalfolder"], root) if "--additionalfolder" in values else None}
    if not result["exe"].is_file() or result["exe"].name.lower() != "codesys.exe":
        raise ValueError("配置的真实CODESYS.exe不存在")
    if not result["template"].is_file() or result["template"].suffix.lower() != ".project":
        raise ValueError("配置的真实.project模板不存在")
    if result["additionalfolder"] and not result["additionalfolder"].is_dir():
        raise ValueError("additionalfolder不存在")
    return result


def probes():
    def fb(name, declaration, body):
        return f"FUNCTION_BLOCK {name}\n{declaration}\n{body}\nEND_FUNCTION_BLOCK\n"
    return [
        {"case_id": "C00_good", "kind": "known_good", "expected": "pass", "source": fb("FB_AgentProbeGood", "VAR_INPUT\n x : BOOL;\nEND_VAR\nVAR_OUTPUT\n y : BOOL;\nEND_VAR", "y := x;")},
        {"case_id": "C01_undeclared", "kind": "undeclared", "expected": "fail", "source": fb("FB_AgentProbeUndeclared", "VAR_OUTPUT\n y : BOOL;\nEND_VAR", "y := AgentSignalNotDeclared_6E79B1;")},
        {"case_id": "C02_type", "kind": "type", "expected": "fail", "source": fb("FB_AgentProbeType", "VAR_OUTPUT\n y : BOOL;\nEND_VAR", "y := 'not-a-bool';")},
        {"case_id": "C03_syntax", "kind": "syntax", "expected": "fail", "source": fb("FB_AgentProbeSyntax", "VAR_INPUT\n x : BOOL;\nEND_VAR\nVAR_OUTPUT\n y : BOOL;\nEND_VAR", "IF x y := TRUE; END_IF;")},
        {"case_id": "C04_missing_dependency", "kind": "missing_dependency", "expected": "fail", "source": fb("FB_AgentProbeMissingDependency", "VAR\n dep : FB_AgentMissingLibraryProbe_6E79B1;\nEND_VAR", "dep();"),
         "note": "故意引用未定义依赖类型；实际诊断可能为未声明/未知类型，不断言一定归类为缺库"},
        {"case_id": "C05_dead_code", "kind": "dead_code", "expected": "observe", "source": fb("FB_AgentProbeDeadCode", "VAR_OUTPUT\n y : BOOL;\nEND_VAR", "IF FALSE THEN\n y := TRUE;\nELSE\n y := FALSE;\nEND_IF;"),
         "note": "观察实际诊断；编译器可优化且不发警告，不强制产生死代码warning"},
    ]


def prepare_cases(output, settings, tasks=None):
    cases = probes()
    if tasks:
        task_path = Path(tasks)
        paths = sorted(task_path.glob("*.yaml")) if task_path.is_dir() else [task_path]
        if not paths:
            raise ValueError("没有找到题面YAML")
        for path in paths:
            card = parse_task(path, root=ROOT)
            if card.get("task_id") != path.stem or not card.get("pou_name"):
                raise ValueError("题号与文件名不匹配或无法生成骨架：" + path.name)
            cases.append({"case_id": "task_" + path.stem + "_skeleton", "kind": "task_skeleton",
                          "expected": "pass", "source": make_skeleton(card), "task_card": card,
                          "note": "仅检查声明/方言兼容；空实现不证明题目功能正确"})
    requests = []
    for case in cases:
        folder = output / case["case_id"]
        folder.mkdir()
        source = folder / "source.st"
        source.write_bytes(case.pop("source").encode("utf-8"))
        project = folder / "compile.project"
        shutil.copy2(settings["template"], project)
        card = folder / "task_card.json"
        write_json(card, case.pop("task_card", {"purpose": "compiler_probe", "task_id": case["case_id"]}))
        request = {"case_id": case["case_id"], "source": str(source), "project": str(project),
                   "result": str(folder / "result.json"), "source_sha256": sha256(source),
                   "application": settings["application"], "task_card": str(card)}
        write_json(folder / "request.json", request)
        case.update(source_sha256=request["source_sha256"], artifact_path=folder.name)
        requests.append(request)
    return cases, requests


def collect_case(case, request, process):
    path = Path(request["result"])
    payload = None
    protocol_error = None
    if path.is_file():
        try:
            payload = json.loads(path.read_text(encoding="utf-8-sig"))
            if not isinstance(payload, dict) or payload.get("status") not in ("pass", "fail", "tool_error", "timeout"):
                raise ValueError("invalid native status")
            if payload.get("compiler") != "CODESYS" or type(payload.get("code_generated")) is not bool:
                raise ValueError("native compiler/code_generated contract missing")
            if payload.get("source_sha256") != request["source_sha256"] or sha256(request["source"]) != request["source_sha256"]:
                raise ValueError("source checksum mismatch")
            if payload.get("status") == "pass" and not payload["code_generated"]:
                raise ValueError("pass without successful target code generation")
        except (ValueError, OSError, TypeError) as exc:
            protocol_error = str(exc)
            payload = None
    if payload is None:
        status = "timeout" if process["status"] == "timeout" else "tool_error"
        if protocol_error:
            status = "tool_error"
        return {**case, "status": status, "code_generated": False, "evidence_kind": "live",
                "evidence_available": False, "elapsed_s": None, "warning_count": 0,
                "diagnostic_codes": [], "errors": [], "expected_check": "unavailable",
                "reason": protocol_error or "CODESYS did not produce a per-case result"}
    errors = payload.get("errors", [])
    if not isinstance(errors, list):
        errors = []
    raw = "\n".join(str(e.get("raw", e.get("message", ""))) for e in errors if isinstance(e, dict))
    # Native codes are already classified using the installed compiler's message
    # identifiers. Localized raw text is only a fallback for older bridges.
    native_codes = {e['code'] for e in errors if isinstance(e, dict) and isinstance(e.get('code'), str)}
    mapped_codes = {item['code'] for item in normalize_errors(raw)} if not native_codes else set()
    status = payload["status"]
    matched = status == case["expected"] if case["expected"] in ("pass", "fail") else status in ("pass", "fail")
    check = "matched" if matched else "mismatch" if status in ("pass", "fail") else "unavailable"
    return {**case, "status": status, "code_generated": payload["code_generated"],
            "evidence_kind": "live", "evidence_available": True, "elapsed_s": payload.get("elapsed_s"),
            "warning_count": sum(isinstance(e, dict) and e.get("severity") == "warning" for e in errors),
            "diagnostic_codes": sorted(native_codes or mapped_codes), "errors": errors,
            "native_messages": payload.get("messages", []), "expected_check": check}


def validate(config_path, output, tasks=None, timeout=900, root=ROOT):
    config_path, output = Path(config_path).resolve(), Path(output).resolve()
    config = json.loads(config_path.read_text(encoding="utf-8-sig"))
    settings = parse_bridge_config(config, root=root)
    if not 0 < timeout <= 900:
        raise ValueError("批次硬超时必须大于0且不超过900秒")
    if output.exists() and any(output.iterdir()):
        raise ValueError("输出目录非空；使用新目录，避免将旧结果当作本次证据")
    output.mkdir(parents=True, exist_ok=True)
    cases, requests = prepare_cases(output, settings, tasks)
    batch = {"cases": requests, "summary": str(output / "native_batch.json")}
    batch_path = output / "batch_request.json"
    write_json(batch_path, batch)
    command = [str(settings["exe"]), "--profile=" + settings["profile"],
               "--runscript=" + str(root / "agent/scripts/codesys_compile_batch.py"), "--noUI"]
    if settings["additionalfolder"]:
        command.append("--additionalfolder=" + str(settings["additionalfolder"]))
    process = run_process(command, timeout_s=timeout, cwd=str(root),
                          env=dict(os.environ, PLC_BATCH_REQUEST=str(batch_path)))
    (output / "stdout.txt").write_text(process["stdout"], encoding="utf-8")
    (output / "stderr.txt").write_text(process["stderr"], encoding="utf-8")
    write_json(output / "process.json", process)
    rows = [collect_case(case, request, process) for case, request in zip(cases, requests)]
    accepted = process["status"] == "pass" and all(row["expected_check"] == "matched" for row in rows)
    summary = {"schema_version": "1.0", "evidence_kind": "live", "operation": "compiler_acceptance_only",
        "model_calls": 0, "functional_tests_run": False, "recorded_at": datetime.now(timezone.utc).isoformat(),
        "profile": settings["profile"], "config_sha256": sha256(config_path),
        "template_sha256": sha256(settings["template"]), "compiler_exe_sha256": sha256(settings["exe"]),
        "process_status": process["status"], "latency_s": process["elapsed_s"], "case_count": len(rows),
        "acceptance_status": "pass" if accepted else "fail", "cases": rows,
        "limits": ["只编译，不执行PLC功能测试；题面骨架没有题目实现",
                   "缺依赖探针不强制编译器使用缺库诊断；死代码探针不强制warning",
                   "超时后未完成案例没有编译结果，不计作模型或语法失败"]}
    write_json(output / "summary.json", summary)
    columns = ["case_id", "kind", "status", "code_generated", "elapsed_s", "expected", "expected_check",
               "warning_count", "source_sha256", "evidence_available", "artifact_path"]
    with (output / "cases.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    lines = ["# CODESYS真实编译验收", "", "本文件只汇总本次IDE产生的编译结果；未调用模型，未运行功能测试。", "",
             f"验收：{summary['acceptance_status']}；案例：{len(rows)}；进程：{process['status']}；总耗时：{process['elapsed_s']} s。", "",
             "|案例|编译状态|目标代码生成|预期核对|警告数|耗时(s)|", "|---|---|---|---|---|---|"]
    lines += [f"|{r['case_id']}|{r['status']}|{r['code_generated']}|{r['expected_check']}|{r['warning_count']}|{r['elapsed_s']}|" for r in rows]
    lines += ["", "缺依赖探针仅检查真实编译器拒绝未定义依赖，错误可以被归类为未知类型/未声明。死代码可以被静默优化。", "",
              "完整原生诊断、源哈希和每例产物索引见summary.json与案例子目录。"]
    (output / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return summary


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True)
    parser.add_argument("--out", default="validation/codesys_live")
    parser.add_argument("--tasks", help="可选：附加题面目录或单个YAML的声明骨架")
    parser.add_argument("--timeout", type=float, default=900)
    args = parser.parse_args(argv)
    try:
        summary = validate(args.config, args.out, args.tasks, args.timeout)
        print(json.dumps({"acceptance_status": summary["acceptance_status"], "case_count": summary["case_count"],
                          "process_status": summary["process_status"], "out": str(Path(args.out))}, ensure_ascii=False))
        return 0 if summary["acceptance_status"] == "pass" else 1
    except (ValueError, OSError) as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

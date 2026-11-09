"""外部工具适配器。fixture 只验证框架连线，绝不充当 PLC 证据。

命令为 argv 数组，不经过 shell。权威编译、功能测试和验证使用 JSON
结果文件，stdout/退出码不能代替判定结果。每次调用保留源码和原始输出。
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import re
import signal
import subprocess
import time
from typing import Any


def _kill_tree(proc: subprocess.Popen) -> None:
    if os.name == "nt":
        subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                       creationflags=subprocess.CREATE_NO_WINDOW, check=False)
    else:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    if proc.poll() is None:
        proc.kill()


def process_command(command, windows=None):
    """CODESYS parses the raw Windows command line and requires quotes after '='.

    Python's normal whole-argument quoting makes --profile invisible to this parser.
    This is still CreateProcess with shell=False; other tools keep normal argv.
    """
    windows = os.name == 'nt' if windows is None else windows
    if not windows or Path(command[0]).name.lower() != 'codesys.exe':
        return list(command)
    parts = [subprocess.list2cmdline([command[0]])]
    for argument in command[1:]:
        if argument.startswith('--') and '=' in argument:
            key, value = argument.split('=', 1)
            if any(char in value for char in ('"', '\r', '\n', '\x00')):
                raise ValueError('Invalid CODESYS command argument')
            parts.append(key + '="' + value + '"')
        else:
            parts.append(subprocess.list2cmdline([argument]))
    return ' '.join(parts)


def run_process(command: list[str], timeout_s: float = 90, cwd=None,
                input_text: str | None = None, env: dict | None = None) -> dict:
    """有界运行并在超时后回收整个进程树；不输出环境变量。"""
    started = time.monotonic()
    base = {"status": "tool_error", "returncode": None, "stdout": "", "stderr": ""}
    if not isinstance(command, (list, tuple)) or not command or not all(isinstance(x, str) for x in command):
        return dict(base, stderr="command must be a nonempty argv array", elapsed_s=0.0)
    if timeout_s <= 0:
        return dict(base, status="timeout", stderr="deadline exceeded before launch", elapsed_s=0.0)
    kwargs = {"creationflags": subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP} if os.name == "nt" else {"start_new_session": True}
    native_codesys = Path(command[0]).name.lower() == 'codesys.exe' or (
        len(command) > 1 and Path(command[1]).name.lower() == 'codesys_bridge.py')
    console_encoding = 'mbcs' if os.name == 'nt' and native_codesys else 'utf-8'
    try:
        proc = subprocess.Popen(process_command(command), cwd=cwd, env=env,
                                stdin=subprocess.PIPE if input_text is not None else subprocess.DEVNULL,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                text=True, encoding=console_encoding, errors="replace", **kwargs)
        try:
            stdout, stderr = proc.communicate(input_text, timeout=timeout_s)
            status = "pass" if proc.returncode == 0 else "fail"
        except subprocess.TimeoutExpired:
            _kill_tree(proc)
            stdout, stderr = proc.communicate()
            status = "timeout"
        return {"status": status, "returncode": proc.returncode, "stdout": stdout,
                "stderr": stderr, "elapsed_s": round(time.monotonic() - started, 6)}
    except (OSError, ValueError) as exc:
        return dict(base, stderr=str(exc), elapsed_s=round(time.monotonic() - started, 6))


def normalize_errors(text: str, default_severity: str = "error") -> list[dict]:
    """保留 raw；英文/中文常见消息归并为修复类别，非完整编译器语法解析器。"""
    errors = []
    for raw in text.splitlines():
        if not raw.strip():
            continue
        if re.match(r"\s*\d+\s+error\(s\)\s+found\.", raw, re.I):
            continue  # MATIEC summary banner is not an additional diagnostic.
        lower = raw.lower()
        severity = "warning" if re.search(r"\bwarning\b|警告", lower) else default_severity
        if re.search(r"dead.?code|unreachable|不可达|死代码", lower):
            code, severity = "W_DEAD_CODE", "warning"
        elif re.search(r"undeclared|not declared|unknown identifier|not defined|未声明|未定义|没有定义标识符|未知标识符", lower):
            code = "E_UNDECLARED"
        elif re.search(r"type mismatch|incompatible.*type|cannot convert|can't convert|类型不|无法转换|不能将类型.*转换|未知的类型|cannot.*convert", lower):
            code = "E_TYPE"
        elif re.search(r"library.*(?:missing|not found|not installed|could not)|(?:missing|cannot find|could not find).*library|缺.*库|库.*(?:缺失|未找到)", lower):
            code = "E_LIBRARY"
        elif re.search(r"syntax|unexpected|expected|语法|缺少.*(?:分号|括号)", lower):
            code = "E_SYNTAX"
        elif re.search(r"\berror\b|错误|\bC\d{4}\b", raw, re.I):
            code = "W_COMPILE" if severity == "warning" else "E_COMPILE"
        elif severity == "warning":
            code = "W_COMPILE"
        else:
            continue
        line = None
        for pattern in (r"\bline\s+(\d+)\b", r"\((\d+)(?:[,;:]\s*\d+)?\)", r":(\d+)-\d+\.\.\d+-\d+:", r":(\d+)(?::\d+)?:", r"第?\s*(\d+)\s*行"):
            match = re.search(pattern, raw, re.I)
            if match:
                line = int(match.group(1))
                break
        errors.append({"code": code, "severity": severity, "line": line,
                       "message": raw.strip(), "raw": raw})
    return errors


def _error(code: str, message: str) -> dict:
    return {"code": code, "severity": "error", "line": None, "message": message, "raw": message}


def _normalized_json_errors(items: Any) -> list[dict]:
    if not isinstance(items, list):
        raise ValueError("errors must be an array")
    out = []
    for item in items:
        if not isinstance(item, dict):
            raise ValueError("each error must be an object")
        raw = str(item.get("raw", item.get("message", "")))
        severity = str(item.get("severity", "error")).lower()
        severity = "fatal" if severity in ("fatalerror", "fatal_error") else severity
        if severity not in ("error", "fatal", "warning", "info", "information"):
            raise ValueError("invalid diagnostic severity")
        mapped = normalize_errors(raw, severity)
        line = item.get("line")
        if line is not None and (not isinstance(line, int) or isinstance(line, bool) or line < 1):
            raise ValueError("error.line must be a positive integer or null")
        native_code = item.get("code")
        code = mapped[0]["code"] if mapped and (not native_code or native_code in ("E_COMPILE", "W_COMPILE") or re.fullmatch(r"[CW]?\d{3,}", str(native_code))) else native_code or "E_COMPILE"
        out.append({"code": str(code),
                    "severity": severity, "line": line,
                    "message": str(item.get("message", raw)), "raw": raw})
    return out


class Toolchain:
    def __init__(self, config: dict, deadline: float, artifact_dir, mode: str = "live"):
        if mode not in ("live", "fixture"):
            raise ValueError("mode must be live or fixture")
        self.config, self.deadline, self.mode = config, deadline, mode
        self.artifact_dir = Path(artifact_dir).resolve()
        self.artifact_dir.mkdir(parents=True, exist_ok=True)

    def _paths(self, source: str, tag: str, channel: str) -> tuple[Path, Path, Path]:
        if not re.fullmatch(r"[A-Za-z0-9_.-]+", str(tag)) or str(tag) in (".", ".."):
            raise ValueError("invalid artifact tag")
        folder = self.artifact_dir / "tools" / str(tag) / channel
        folder.mkdir(parents=True, exist_ok=True)
        src, result = folder / "source.st", folder / "result.json"
        src.write_text(source, encoding="utf-8")
        # 不接受上一轮遗留的结果文件。
        result.unlink(missing_ok=True)
        return folder, src, result

    def _external(self, source: str, tag: str, channel: str, default_timeout: float) -> dict:
        folder, src, result = self._paths(source, tag, channel)
        cfg = self.config.get(channel, {})
        command = cfg.get("command", [])
        values = {"source": str(src), "result": str(result), "artifact_dir": str(folder),
                  "task_card": str(self.config.get("task_card", self.artifact_dir / "task_card.json")),
                  "cases_dir": str(self.config.get("test", {}).get("cases_dir", "tests/cases"))}
        if not command:
            process = {"status": "tool_error", "returncode": None, "stdout": "", "stderr": channel + " command is not configured", "elapsed_s": 0.0}
        else:
            try:
                if not isinstance(command, list) or not all(isinstance(x, str) for x in command):
                    raise ValueError("command must be an argv array")
                # 只替换约定占位符，保留命令中合法的 JSON/代码花括号。
                argv = list(command)
                for key, value in values.items():
                    argv = [x.replace("{" + key + "}", value) for x in argv]
                timeout = min(float(cfg.get("timeout_s", default_timeout)), self.deadline - time.monotonic())
                process = run_process(argv, timeout_s=timeout,
                                      cwd=cfg.get("cwd", self.config.get("project_root", Path(__file__).resolve().parents[2])))
            except (ValueError, KeyError, TypeError) as exc:
                process = {"status": "tool_error", "returncode": None, "stdout": "", "stderr": str(exc), "elapsed_s": 0.0}
        (folder / "stdout.txt").write_text(process.get("stdout", ""), encoding="utf-8")
        (folder / "stderr.txt").write_text(process.get("stderr", ""), encoding="utf-8")
        (folder / "process.json").write_text(json.dumps(process, ensure_ascii=False, indent=2), encoding="utf-8")
        payload = None
        if process["status"] in ("pass", "fail") and result.is_file():
            try:
                payload = json.loads(result.read_text(encoding="utf-8-sig"))
                if not isinstance(payload, dict):
                    raise ValueError("result must be an object")
            except (ValueError, OSError) as exc:
                process["status"] = "tool_error"
                process["stderr"] += "\ninvalid result JSON: " + str(exc)
        return {"process": process, "payload": payload, "folder": folder}

    def _fast(self, source: str, tag: str) -> dict:
        run = self._external(source, tag, "fast", 3)
        process = run["process"]
        errors = normalize_errors(process["stdout"] + "\n" + process["stderr"])
        if process["status"] == "tool_error":
            errors.append(_error("E_TOOL", process["stderr"]))
        elif process["status"] == "fail" and not any(x["severity"] == "error" for x in errors):
            errors.append(_error("E_COMPILE", "Fast compiler exited nonzero; inspect stdout.txt/stderr.txt"))
        return {"status": process["status"], "errors": errors, "elapsed_s": process["elapsed_s"], "evidence_kind": "live"}

    def _authority(self, source: str, tag: str) -> dict:
        run = self._external(source, tag, "authoritative", 90)
        process, payload = run["process"], run["payload"]
        status, errors = process["status"], []
        if status in ("pass", "fail"):
            try:
                if payload is None or payload.get("status") not in ("pass", "fail", "timeout", "tool_error"):
                    raise ValueError("authoritative bridge must write status and errors to result JSON")
                errors = _normalized_json_errors(payload.get("errors"))
                status = payload["status"]
                if status == "pass" and (process["returncode"] != 0 or any(x["severity"] in ("error", "fatal") for x in errors)):
                    raise ValueError("contradictory authority pass / process errors")
            except ValueError as exc:
                status, errors = "tool_error", [_error("E_PROTOCOL", str(exc))]
        elif status == "tool_error":
            errors = [_error("E_TOOL", process["stderr"])]
        elif status == "timeout":
            errors = [_error("E_TIMEOUT", "authoritative compiler timed out")]
        result = {"status": status, "errors": errors, "elapsed_s": process["elapsed_s"], "evidence_kind": "live"}
        (run["folder"] / "normalized.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        return result

    def compile(self, source: str, tag: str) -> dict:
        if self.mode == "fixture":
            folder, _, _ = self._paths(source, tag, "fixture_compile")
            status = "tool_error" if "FIXTURE_TOOL_ERROR" in source else "timeout" if "FIXTURE_TIMEOUT" in source else "fail" if "FIXTURE_COMPILE_FAIL" in source else "pass"
            errors = [] if status == "pass" else [_error("E_SYNTAX" if status == "fail" else "E_" + status.upper(), "FIXTURE ONLY: simulated " + status)]
            fake = {"status": status, "errors": errors, "elapsed_s": 0.0, "evidence_kind": "fixture"}
            result = {"status": status, "fast": dict(fake), "authoritative": dict(fake), "errors": errors,
                      "authoritative_available": False, "evidence_kind": "fixture"}
            (folder / "result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
            return result
        # 快检是反馈；权威结果决定CPR，不把方言差异误算作权威编译失败。
        fast = self._fast(source, tag)
        authority = self._authority(source, tag)
        return {"status": authority["status"], "fast": fast, "authoritative": authority,
                "errors": authority["errors"], "authoritative_available": bool(self.config.get("authoritative", {}).get("command")),
                "evidence_kind": "live"}

    def test(self, source: str, tag: str) -> dict:
        if self.mode == "fixture":
            folder, _, _ = self._paths(source, tag, "fixture_test")
            good = 1 if "FIXTURE_TEST_FAIL" in source else 3
            result = {"status": "pass" if good == 3 else "fail", "total": 3, "passed": good,
                      "passed_ids": ["fixture_case_" + str(i + 1) for i in range(good)],
                      "failures": [] if good == 3 else [{"case_id": "fixture_case_2", "cycle": 2, "signal": "fixture_signal", "expected": True, "actual": False}],
                      "evidence_kind": "fixture"}
            (folder / "result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
            return result
        if not self.config.get("test", {}).get("command"):
            return {"status": "skipped", "total": 0, "passed": 0, "passed_ids": [], "failures": [], "evidence_kind": "live", "reason": "test command not configured"}
        run = self._external(source, tag, "test", 90)
        process, payload = run["process"], run["payload"]
        status = process["status"]
        empty = {"status": status, "total": 0, "passed": 0, "passed_ids": [], "failures": [], "evidence_kind": "live"}
        if status in ("timeout", "tool_error"):
            return dict(empty, reason=process["stderr"])
        try:
            if payload is None or payload.get("status") not in ("pass", "fail", "timeout", "tool_error", "skipped"):
                raise ValueError("test bridge must write valid status")
            total, passed = payload.get("total"), payload.get("passed")
            if type(total) is not int or type(passed) is not int or not 0 <= passed <= total:
                raise ValueError("invalid test counts")
            ids = payload.get("passed_ids")
            if not isinstance(ids, list) or len(ids) != passed or len(set(ids)) != passed or not all(isinstance(x, str) for x in ids):
                raise ValueError("passed_ids must contain exactly passed unique case IDs")
            failures = payload.get("failures")
            if not isinstance(failures, list):
                raise ValueError("failures must be an array")
            if payload["status"] == "pass" and (total == 0 or passed != total or process["returncode"] != 0):
                raise ValueError("pass requires nonempty all-passed cases and process rc=0")
            if payload["status"] == "fail" and (total == 0 or passed == total):
                raise ValueError("fail requires at least one failed case")
            return dict(empty, status=payload["status"], total=total, passed=passed, passed_ids=ids, failures=failures)
        except (ValueError, TypeError) as exc:
            return dict(empty, status="tool_error", reason="invalid test result: " + str(exc))

    def verify(self, source: str, tag: str) -> dict:
        if self.mode == "fixture" or not self.config.get("verify", {}).get("command"):
            return {"status": "skipped", "reason": "fixture is not formal verification" if self.mode == "fixture" else "verify command not configured", "evidence_kind": self.mode}
        run = self._external(source, tag, "verify", 90)
        process, payload = run["process"], run["payload"]
        if process["status"] in ("timeout", "tool_error"):
            return {"status": process["status"], "evidence_kind": "live", "reason": process["stderr"]}
        if not payload or payload.get("status") not in ("pass", "violated", "timeout", "skipped"):
            return {"status": "tool_error", "evidence_kind": "live", "reason": "invalid verification result JSON"}
        if payload["status"] == "pass" and process["returncode"] != 0:
            return {"status": "tool_error", "evidence_kind": "live", "reason": "verification pass contradicts process return code"}
        return dict(payload, evidence_kind="live")

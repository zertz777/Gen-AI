"""标准 Python 启动器：复制模板，启动 CODESYS 脚本，写严格 JSON 结果。

本脚本本身不提供 CODESYS 安装、设备包或模板工程。配置完成后才可用于实测。
外层 Toolchain 负责硬超时和进程树回收。
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from agent.src.tools import process_command


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("source", "result", "exe", "profile", "template"):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--application", default="Application")
    parser.add_argument("--task-card", default="")
    parser.add_argument("--additionalfolder", default="")
    args = parser.parse_args()
    result = Path(args.result).resolve()
    result.parent.mkdir(parents=True, exist_ok=True)
    try:
        source, template = Path(args.source).resolve(), Path(args.template).resolve()
        if not source.is_file() or not template.is_file() or not Path(args.exe).is_file():
            raise ValueError("source, CODESYS executable and template must exist")
        local_project = result.parent / "compile.project"
        if local_project == template:
            raise ValueError("template must not be the per-run working project")
        shutil.copy2(template, local_project)
        request = {"source": str(source), "result": str(result), "project": str(local_project),
                   "application": args.application, "task_card": args.task_card,
                   "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest()}
        request_path = result.parent / "codesys_request.json"
        request_path.write_text(json.dumps(request, ensure_ascii=True, indent=2), encoding="utf-8")
        env = dict(os.environ, PLC_AGENT_REQUEST=str(request_path))
        native_script = Path(__file__).with_name("codesys_compile.py").resolve()
        command = [args.exe, "--profile=" + args.profile, "--runscript=" + str(native_script), "--noUI"]
        if args.additionalfolder:
            command.append("--additionalfolder=" + args.additionalfolder)
        completed = subprocess.run(process_command(command), env=env, check=False)
        if not result.is_file():
            raise RuntimeError("CODESYS exited without structured result (rc=" + str(completed.returncode) + ")")
        return completed.returncode
    except Exception as exc:
        payload = {"status": "tool_error", "errors": [{"code": "E_BRIDGE", "severity": "error", "line": None, "message": str(exc), "raw": str(exc)}]}
        result.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

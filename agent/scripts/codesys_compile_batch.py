# encoding: utf-8
"""在一个真实CODESYS脚本进程中逐项编译；单项异常不会丢失已完成证据。"""
from __future__ import print_function
import io
import json
import os
import runpy
import time

try:
    text_type = unicode
except NameError:
    text_type = str


def write_json(path, value):
    with io.open(path, "w", encoding="utf-8") as stream:
        stream.write(text_type(json.dumps(value, ensure_ascii=False, indent=2)))


def execute_batch(batch):
    native = os.path.join(os.path.dirname(os.path.abspath(__file__)), "codesys_compile.py")
    namespace = runpy.run_path(native, init_globals={"projects": projects, "system": system},
                               run_name="codesys_shared")
    compile_request = namespace["compile_request"]
    completed = []
    started = time.time()
    for request in batch["cases"]:
        began = time.time()
        try:
            result = compile_request(request)
        except Exception as exc:
            result = {"status": "tool_error", "code_generated": False,
                      "compiler": "CODESYS", "source_sha256": request["source_sha256"],
                      "errors": [{"code": "E_BRIDGE", "severity": "error", "line": None,
                                  "message": text_type(exc), "raw": text_type(exc)}]}
        result.update(case_id=request["case_id"], elapsed_s=max(0.0, time.time() - began),
                      evidence_kind="live")
        write_json(request["result"], result)
        completed.append({"case_id": request["case_id"], "status": result["status"],
                          "code_generated": result.get("code_generated", False),
                          "elapsed_s": result["elapsed_s"]})
        # 每例均更新索引。即使随后某例挂起，父进程还能读取已完成证据。
        write_json(batch["summary"], {"status": "running", "evidence_kind": "live",
            "cases_completed": completed, "elapsed_s": max(0.0, time.time() - started)})
    result = {"status": "completed", "evidence_kind": "live", "cases_completed": completed,
              "elapsed_s": max(0.0, time.time() - started)}
    write_json(batch["summary"], result)
    return result


def main():
    path = os.environ.get("PLC_BATCH_REQUEST")
    if not path:
        raise ValueError("PLC_BATCH_REQUEST is required")
    with io.open(path, "r", encoding="utf-8-sig") as stream:
        batch = json.load(stream)
    try:
        result = execute_batch(batch)
    except Exception as exc:
        result = {"status": "tool_error", "evidence_kind": "live", "cases_completed": [],
                  "error": text_type(exc)}
        write_json(batch["summary"], result)
    print("CODESYS batch result: " + result["status"])


if __name__ == "__main__":
    main()

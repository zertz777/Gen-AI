# encoding: utf-8
"""仅由 CODESYS --runscript 执行；保持 IronPython 2.7 兼容。

官方API实现，已在CODESYS 3.5.22.40/Scripting 4.2中实测；换profile需重新验收。
"""
from __future__ import print_function
import hashlib
import io
import json
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from st_bundle import split_source

try:
    text_type = unicode
except NameError:
    text_type = str


def write_result(path, data):
    with io.open(path, "w", encoding="utf-8") as stream:
        stream.write(text_type(json.dumps(data, ensure_ascii=False, indent=2)))


def diagnostic_source_line(mapping, object_name, position):
    """Map only a known imported object and its measured Decl/Impl partition."""
    if not mapping or not object_name or not position:
        return None
    lower = position.lower()
    part = "implementation" if "(impl)" in lower else "declaration" if "(decl)" in lower else None
    if part is None:
        return None
    match = re.search(u"(?:[Ll]ine\\s*|\u884c\\s*)(\\d+)|(\\d+)\\s*\u884c", position)
    if not match:
        return None
    native_line = int(match.group(1) or match.group(2))
    spans = [entry for entry in mapping["imported_text_spans"]
             if entry["object_name"] == object_name and
             (entry["part"] == part or part == "declaration" and entry["part"] == "type_declaration")]
    if len(spans) != 1 or spans[0]["source_start_line"] is None:
        return None
    span = spans[0]
    line = span["source_start_line"] + native_line - 1 - span["imported_prefix_lines"]
    return line if span["source_start_line"] <= line <= span["source_end_line"] else None


def collect_messages(system_api, stage, mapping=None):
    """Snapshot native diagnostics without guessing object-local source line numbers."""
    errors, messages = [], []
    for category in system_api.get_message_categories(True):
        for message in system_api.get_message_objects(category):
            severity = text_type(message.severity).lower()
            raw = text_type(message.text)
            position = text_type(message.position_text or "")
            item = {"stage": stage, "severity": severity, "raw": raw,
                    "position_text": position, "category": text_type(category)}
            object_name = None
            positioned_object = getattr(message, "object", None)
            if positioned_object is not None:
                object_name = text_type(positioned_object.get_name())
                item["object_name"] = object_name
            number = getattr(message, "number", None)
            prefix = getattr(message, "prefix", None)
            if number is not None:
                item["native_number"] = int(number)
            if prefix is not None:
                item["native_prefix"] = text_type(prefix)
            messages.append(item)
            if "error" in severity or "warning" in severity:
                # Match only an identified imported object and its calibrated partition.
                code = "W_COMPILE" if "warning" in severity else "E_COMPILE"
                if text_type(prefix) == "C" and "error" in severity:
                    code = {6: "E_SYNTAX", 32: "E_TYPE", 46: "E_UNDECLARED", 77: "E_TYPE"}.get(number, code)
                errors.append({"code": code,
                               "severity": "warning" if "warning" in severity else "error",
                               "line": diagnostic_source_line(mapping, object_name, position),
                               "message": raw, "raw": raw})
    return errors, messages


def clear_messages(system_api):
    for category in system_api.get_message_categories(False):
        system_api.clear_messages(category)


def run_stage(system_api, name, action, mapping=None):
    clear_messages(system_api)
    started = time.time()
    exception = None
    try:
        action()
    except Exception as exc:
        exception = text_type(exc)
    errors, messages = collect_messages(system_api, name, mapping)
    if exception is not None:
        errors.append({"code": "E_BRIDGE_STAGE", "severity": "error", "line": None,
                       "message": name + ": " + exception, "raw": exception})
    status = "tool_error" if exception is not None else "fail" if any(e["severity"] == "error" for e in errors) else "pass"
    return {"status": status, "errors": errors, "messages": messages,
            "elapsed_s": max(0.0, time.time() - started)}


def source_spans(source, bundle):
    """Record imported spans, including the attribute prefix in the POU declaration."""
    spans = []
    entries = [(entry["name"], "type_declaration", entry["declaration"]) for entry in bundle["types"]]
    entries.extend([(bundle["name"], "declaration", bundle["declaration"]),
                    (bundle["name"], "implementation", bundle["implementation"])])
    for name, part, text in entries:
        # Empty or duplicate text is intentionally unresolved.
        offset = source.find(text) if text and source.count(text) == 1 else -1
        spans.append({"object_name": name, "part": part,
                      "source_start_line": source[:offset].count("\n") + 1 if offset >= 0 else None,
                      "source_end_line": source[:offset].count("\n") + len(text.splitlines()) if offset >= 0 else None,
                      "imported_prefix_lines": 1 if part == "declaration" else 0})
    return {"status": "known_object_partitions_calibrated", "imported_text_spans": spans,
            "note": "Decl/Impl line mapping calibrated with native diagnostics; unknown objects/positions remain null"}


def compile_request(request):
    # projects and system are supplied by the CODESYS script engine.
    # Match the outer bridge's original-byte checksum. Text mode would normalize CRLF
    # and strip BOM, so source text must not be re-encoded for provenance checking.
    with open(request["source"], "rb") as stream:
        source_bytes = stream.read()
    if hashlib.sha256(source_bytes).hexdigest() != request["source_sha256"]:
        raise ValueError("Source checksum changed before CODESYS import")
    source = source_bytes.decode("utf-8-sig")
    bundle = split_source(source)
    project = projects.open(request["project"])
    try:
        apps = project.find(request["application"], recursive=True)
        if len(apps) != 1:
            raise ValueError("Expected one named application in template")
        application = apps[0]
        # Templates are dedicated empty compile projects. Never replace existing objects.
        for entry in bundle["types"]:
            if application.find(entry["name"], recursive=True):
                raise ValueError("Template type name collision: " + entry["name"])
            obj = application.create_dut(entry["name"])
            obj.textual_declaration.replace(new_text=entry["declaration"])
        if application.find(bundle["name"], recursive=True):
            raise ValueError("Template POU name collision: " + bundle["name"])
        if bundle["kind"] == "FUNCTION_BLOCK":
            pou = application.create_function_block(bundle["name"])
        elif bundle["kind"] == "FUNCTION":
            first = bundle["declaration"].splitlines()[0]
            return_type = first.split(":", 1)[1].strip() if ":" in first else ""
            if not return_type:
                raise ValueError("FUNCTION requires return type")
            pou = application.create_function(bundle["name"], return_type)
        else:
            pou = application.create_program(bundle["name"])
        declaration = "{attribute 'linkalways'}\n" + bundle["declaration"]
        pou.textual_declaration.replace(new_text=declaration)
        pou.textual_implementation.replace(new_text=bundle["implementation"])
        mapping = source_spans(source, bundle)
        build = run_stage(system, "build", application.rebuild, mapping)
        # A successful syntax build alone does not establish successful target codegen.
        if build["status"] == "pass":
            generate = run_stage(system, "generate", application.generate_code, mapping)
        else:
            generate = {"status": "skipped", "reason": "build_" + build["status"],
                        "errors": [], "messages": [], "elapsed_s": 0.0}
        phases = {"build": build, "generate": generate}
        errors = build["errors"] + generate["errors"]
        all_messages = build["messages"] + generate["messages"]
        if any(item["status"] == "tool_error" for item in phases.values()):
            status = "tool_error"
        elif all(item["status"] == "pass" for item in phases.values()):
            status = "pass"
        else:
            status = "fail"
        project.save()
        return {"status": status, "errors": errors, "messages": all_messages,
                "stages": phases, "compiler": "CODESYS", "code_generated": generate["status"] == "pass",
                "source_line_mapping": mapping,
                "source_sha256": request["source_sha256"], "linked_pou": bundle["name"]}
    finally:
        project.close()


def main():
    request_path = os.environ.get("PLC_AGENT_REQUEST")
    if not request_path:
        raise ValueError("PLC_AGENT_REQUEST is required; use codesys_bridge.py")
    with io.open(request_path, "r", encoding="utf-8") as stream:
        request = json.load(stream)
    try:
        result = compile_request(request)
    except Exception as exc:
        result = {"status": "tool_error", "code_generated": False,
                  "errors": [{"code": "E_BRIDGE", "severity": "error", "line": None,
                              "message": text_type(exc), "raw": text_type(exc)}]}
    write_result(request["result"], result)
    print("CODESYS compile result: " + result["status"])


if __name__ == "__main__":
    main()

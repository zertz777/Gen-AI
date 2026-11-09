# encoding: utf-8
"""CODESYS --runscript 用的模板建立/设备枚举脚本（IronPython 2.7兼容）。

通过PLC_TEMPLATE_REQUEST环境变量或--request=<JSON文件>取得请求。
仅使用公开ScriptEngine API；不猜测设备ID/版本，不连接、下载或启动PLC。

首选template=<真实标准.project文件>；从空工程创建时必须给出已安装
device的type/id/version。若设备描述未自动创建Application，还须提供从
同版标准工程导出的application_native，不能虚构create_application API。
"""
from __future__ import print_function
import io
import json
import os
import re
import sys

try:
    text_type = unicode
except NameError:
    text_type = str


def write_json(path, data):
    parent = os.path.dirname(os.path.abspath(path))
    if not os.path.isdir(parent):
        os.makedirs(parent)
    with io.open(path, "w", encoding="utf-8") as stream:
        stream.write(text_type(json.dumps(data, ensure_ascii=False, indent=2)))


def device_key(value):
    return (int(value.type), text_type(value.id), text_type(value.version))


def enumerate_devices(name_filter=""):
    # get_all_devices有多个重载，官方建议使用命名参数。
    found = device_repository.get_all_devices(name=name_filter, source=None)
    result = []
    for entry in found:
        did = entry.device_id
        result.append({"type": int(did.type), "id": text_type(did.id),
                       "version": text_type(did.version),
                       "name": text_type(entry.device_info.name),
                       "vendor": text_type(entry.device_info.vendor)})
    return sorted(result, key=lambda item: (item["name"], item["version"], item["id"]))


def enumerate_libraries():
    return [{"displayname": text_type(item.displayname), "title": text_type(item.title),
             "version": text_type(item.version), "company": text_type(item.company)}
            for item in librarymanager.get_all_libraries(exclude_shadowed_libs=True)]


def _identifier(value):
    if not isinstance(value, (str, text_type)) or not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", value):
        raise ValueError("Expected an IEC identifier")
    return value


def _one(items, description):
    if len(items) != 1:
        raise ValueError("Expected exactly one " + description + "; found " + str(len(items)))
    return items[0]


def _applications(project, name):
    return [item for item in project.get_children(recursive=True)
            if getattr(item, "is_application", False) and item.get_name() == name]


def _assert_device_installed(selection, inventory):
    if not isinstance(selection, dict) or not all(key in selection for key in ("type", "id", "version")):
        raise ValueError("device must contain exact installed type/id/version from action=enumerate")
    wanted = (int(selection["type"]), text_type(selection["id"]), text_type(selection["version"]))
    matches = [row for row in inventory if (row["type"], row["id"], row["version"]) == wanted]
    if not matches:
        raise ValueError("Requested device type/id/version is not installed; enumerate this profile first")
    return matches[0]


def _messages():
    rows = []
    for category in system.get_message_categories(True):
        for message in system.get_message_objects(category):
            rows.append({"severity": text_type(message.severity).lower(),
                         "raw": text_type(message.text),
                         "position_text": text_type(message.position_text or "")})
    return rows


def _ensure_libraries(application, request):
    manager = application.get_library_manager()  # 官方API会在没有对象时创建LibraryManager。
    updates = []
    for title, replacement in request.get("library_overrides", {}).items():
        found = librarymanager.find_library(replacement)
        if not found:
            raise ValueError("Explicit replacement library is not installed: " + replacement)
        for old in list(manager.get_libraries(recursive=False)):
            old = text_type(old)
            if old.split(",", 1)[0].strip() == title and old != replacement:
                manager.remove_library(old)
                updates.append({"old": old, "new": replacement})
        if replacement not in [text_type(value) for value in manager.get_libraries(recursive=False)]:
            manager.add_library(found[0])
    request["_library_updates"] = updates
    for displayname in request.get("libraries", []):
        existing = [text_type(value) for value in manager.get_libraries(recursive=False)]
        if displayname in existing:
            continue
        found = librarymanager.find_library(displayname)
        if not found:
            raise ValueError("Requested library is not installed: " + displayname)
        manager.add_library(found[0])
    names = [text_type(value) for value in manager.get_libraries(recursive=False)]
    if request.get("require_standard_library", True) and not any(
            value.split(",", 1)[0].strip().lstrip("#") == "Standard" for value in names):
        raise ValueError("Template needs Standard library. Pass exact installed displayname in libraries or clone a Standard Project")
    return names


def _ensure_program_and_task(application, request):
    program_name = _identifier(request.get("program", "PLC_PRG"))
    matches = application.find(program_name, recursive=True)
    # Recursive find also returns task call objects with the same POU name.
    programs = [item for item in matches if getattr(item, "has_textual_implementation", False)]
    if programs:
        program = _one(programs, program_name)
        if not getattr(program, "has_textual_implementation", False):
            raise ValueError("Template program must have an ST implementation")
    else:
        if matches:
            raise ValueError("Template program must have an ST implementation")
        program = application.create_program(program_name)
    # 克隆原文件不被改动；要覆盖模板内已有逻辑仍须显式声明这是可替换模板。
    implementation = text_type(program.textual_implementation.text)
    without_comments = re.sub(r"\(\*.*?\*\)|//[^\r\n]*", "", implementation, flags=re.S)
    if without_comments.strip() and not request.get("replace_program", False):
        raise ValueError("Seed program contains logic; use a dedicated empty template or explicit replace_program=true")
    program.textual_declaration.replace(new_text="PROGRAM " + program_name +
        "\nVAR\n    _agent_template_alive : BOOL;\nEND_VAR")
    program.textual_implementation.replace(new_text="_agent_template_alive := TRUE;")
    configs = [item for item in application.get_children(recursive=True)
               if getattr(item, "is_task_configuration", False)]
    config = _one(configs, "Task Configuration") if configs else application.create_task_configuration()
    task_name = _identifier(request.get("task", "MainTask"))
    tasks = [item for item in config.find(task_name, recursive=False) if getattr(item, "is_task", False)]
    task = _one(tasks, task_name) if tasks else config.create_task(task_name)
    task.kind_of_task = KindOfTask.Cyclic
    task.interval = text_type(request.get("task_interval", "20"))
    task.interval_unit = text_type(request.get("task_interval_unit", "ms"))
    # find包含任务调用的瞬态对象；只有缺失该调用时才新增，避免标准模板重复调用。
    if not task.find(program_name, recursive=False):
        task.pous.add(program_name)
    return {"program": program_name, "task": task_name, "interval": text_type(task.interval),
            "interval_unit": text_type(task.interval_unit)}


def create_template(request):
    """创建实际目标工程；pass只在本机CODESYS rebuild返回且无error时写出。"""
    inventory = enumerate_devices()
    if request.get("action", "create") == "enumerate":
        return {"status": "pass", "action": "enumerate", "devices": inventory,
                "libraries": enumerate_libraries(), "template_created": False}
    output = os.path.abspath(request["output"])
    if not output.lower().endswith(".project"):
        raise ValueError("output must end with .project")
    if os.path.exists(output):
        raise ValueError("output already exists; choose a fresh path")
    parent = os.path.dirname(output)
    if not os.path.isdir(parent):
        os.makedirs(parent)
    if projects.primary:
        raise ValueError("Use a dedicated noUI CODESYS process with no open primary project")
    selected = _assert_device_installed(request["device"], inventory) if request.get("device") else None
    seed = request.get("template")
    project = None
    try:
        if seed:
            seed = os.path.abspath(seed)
            if not os.path.isfile(seed):
                raise ValueError("Provided standard project template does not exist")
            project = projects.open(seed, primary=True)
            project.save_as(output)
            mode = "clone"
        else:
            if selected is None:
                raise ValueError("Without template, an exact installed device type/id/version is required")
            project = projects.create(output, primary=True)
            name = _identifier(request.get("device_node", "Device"))
            project.add(name=name, type=selected["type"], id=selected["id"], version=selected["version"])
            mode = "empty_project_device"
        devices = [item for item in project.get_children(recursive=False)
                   if getattr(item, "is_device", False)]
        if request.get("device_node"):
            devices = [item for item in devices if item.get_name() == request["device_node"]]
        device = _one(devices, "top-level PLC device")
        if selected is not None and device_key(device.get_device_identification()) != (
                selected["type"], selected["id"], selected["version"]):
            device.update(type=selected["type"], id=selected["id"], version=selected["version"])
        actual_id = device.get_device_identification()
        actual = _assert_device_installed({"type": actual_id.type, "id": actual_id.id,
                                           "version": actual_id.version}, inventory)
        application_name = _identifier(request.get("application", "Application"))
        applications = _applications(project, application_name)
        if not applications and request.get("application_native"):
            native = os.path.abspath(request["application_native"])
            if not os.path.isfile(native):
                raise ValueError("application_native does not exist")
            logic = _one(device.find(request.get("plc_logic_name", "PLC Logic"), recursive=True), "PLC Logic node")
            logic.import_native(filenames=native)
            applications = _applications(project, application_name)
        if not applications:
            raise ValueError("Device did not create Application. Supply a standard project template or an exported application_native seed; no undocumented create_application API is used")
        application = _one(applications, application_name)
        project.active_application = application
        libraries = _ensure_libraries(application, request)
        task = _ensure_program_and_task(application, request)
        for category in system.get_message_categories(False):
            system.clear_messages(category)
        application.rebuild()
        messages = _messages()
        failed = any("error" in row["severity"] for row in messages)
        project.save()
        return {"status": "fail" if failed else "pass", "action": "create", "mode": mode,
                "template_created": True, "template_ready": not failed, "output": output,
                "device": actual, "application": application_name, "libraries": libraries,
                "library_updates": request.get("_library_updates", []),
                "task": task, "messages": messages, "compiler": "CODESYS",
                "scope": "offline template rebuild only; no PLC login/download/start"}
    finally:
        if project is not None:
            project.close()


def main():
    request_path = os.environ.get("PLC_TEMPLATE_REQUEST")
    for arg in sys.argv[1:]:
        if arg.startswith("--request="):
            request_path = arg.split("=", 1)[1]
    if not request_path:
        raise ValueError("PLC_TEMPLATE_REQUEST or --request=<JSON file> is required")
    with io.open(request_path, "r", encoding="utf-8-sig") as stream:
        request = json.load(stream)
    try:
        result = create_template(request)
    except Exception as exc:
        result = {"status": "tool_error", "template_created": False, "template_ready": False,
                  "errors": [{"code": "E_TEMPLATE", "message": text_type(exc)}]}
    write_json(request["result"], result)
    print("CODESYS template result: " + result["status"])


if __name__ == "__main__":
    main()

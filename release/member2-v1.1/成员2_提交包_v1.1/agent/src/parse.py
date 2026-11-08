"""读取成员1题面，保留原始契约并显式暴露不能自行消解的歧义。"""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import re
from typing import Any


REQUIRED_FIELDS = (
    "task_id", "title", "difficulty", "category", "requirement", "io_table",
    "initial_state", "constraints", "provenance", "spec_ref",
)
_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_ELEMENTARY_TYPES = set((
    "BOOL BYTE WORD DWORD LWORD SINT INT DINT LINT USINT UINT UDINT ULINT "
    "REAL LREAL TIME LTIME DATE LDATE TOD LTOD DT LDT STRING WSTRING VARIANT"
).split())


def _read_yaml(text: str) -> Any:
    """优先使用通用安全读取器；没有依赖时使用成员1的受控子集读取器。"""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    try:
        import yaml
    except ImportError:
        reader_path = Path(__file__).resolve().parents[2] / "tools" / "yaml_io.py"
        spec = importlib.util.spec_from_file_location("member1_yaml_reader", reader_path)
        if spec is None or spec.loader is None:
            raise ValueError("找不到随包附带的 YAML 读取器")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module.loads(text)
    else:
        return yaml.safe_load(text)


def _project_root(path: Path, root: str | Path | None) -> Path:
    if root is not None:
        return Path(root).resolve()
    for ancestor in path.parents:
        if (ancestor / "data" / "tasks").is_dir():
            return ancestor
    return path.parent


def _public_path(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        # 产物不泄露本机绝对路径；外部输入以文件名和哈希识别。
        return path.name


def _semantic_warnings(task: dict, spec_text: str) -> list[dict]:
    """只提示已定位的上游矛盾，不替成员1修改题意或选择优先级。"""
    warnings: list[dict] = []
    tid = task.get("task_id")
    raw_constraints = task.get("constraints", [])
    constraints = "\n".join(str(v) for v in raw_constraints) if isinstance(raw_constraints, list) else ""
    if tid == "P08" and "停止处理后续通道" in constraints:
        warnings.append({
            "code": "DATA_P08_ERROR_HANDLING_CONFLICT",
            "message": "英文需求逐通道跳过非法模式/量程；K5要求遇错停止后续通道。须由数据负责人确认，框架保留两者。",
            "evidence": ["requirement 第6/7项", "constraints K5"],
        })
    if tid == "P08" and "count > 32" in spec_text:
        warnings.append({
            "code": "DATA_P08_SPEC_BOUNDS_CONFLICT",
            "message": "题面按调用方两数组长度确定count上界；LTL C2b另引入32路上限，且首周期/未使能输出要求与题面未统一。",
            "evidence": ["requirement 第1项", "spec C1/C2b/C10"],
        })
    if tid == "P17" and "16#8001（配方不存在）" in constraints:
        warnings.append({
            "code": "DATA_P17_STATUS_CONFLICT",
            "message": "英文需求删除/修改不存在编号分别返回16#8004/16#8005；K3统一要求16#8001。请先确认统一判据。",
            "evidence": ["requirement 第4/5项", "constraints K3"],
        })
    if tid == "P19":
        rows = task.get("io_table", [])
        emergency = next((v for v in (rows if isinstance(rows, list) else [])
                          if isinstance(v, dict) and v.get("name") == "EmergencyStop"), {})
        if "FALSE: Emergency stop triggered" in str(emergency.get("description", "")) and "EmergencyStop = TRUE" in constraints:
            warnings.append({
                "code": "DATA_P19_ESTOP_POLARITY_CONFLICT",
                "message": "I/O说明EmergencyStop=FALSE表示急停；K4与LTL C1/C2按TRUE急停解释。安全相关极性不能由生成器猜测。",
                "evidence": ["io_table EmergencyStop.description", "constraints K4", "spec C1/C2"],
            })
    if tid == "P14" and "返回状态区分" in constraints:
        warnings.append({
            "code": "DATA_P14_STATUS_NOT_IN_INTERFACE",
            "message": "K4提到靠返回状态区分非法输入与0.0.0.0，但I/O仅有ipText/ipValue；不能擅自新增状态参数。",
            "evidence": ["constraints K4", "io_table"],
        })
    return warnings


def _interface_projection(task: dict, warnings: list[str]) -> tuple[list, str, dict, list]:
    """按题面明确声明的结构类型投影接口，原始io_table始终不变。"""
    io = task.get("io_table", [])
    if not isinstance(io, list):
        return [], "", {}, []
    registry = {
        "ST_Pump": ("priority", "selection", "RunComd"),
        "ST_Recipe": ("recipeID", "ingredientType", "ingredientRatio", "productionTemperature"),
    }
    all_rows = [r for r in io if isinstance(r, dict)]
    usable_fields = [r for r in all_rows
                     if isinstance(r.get("name"), str)
                     and isinstance(r.get("data_type"), str)
                     and re.fullmatch(r"[A-Za-z0-9_\s\[\]*.,():]+", r["data_type"] or "")]
    declared_type_text = " ".join(str(r.get("data_type", "")) for r in all_rows)
    types: dict[str, list[dict]] = {}
    member_names: set[str] = set()
    origins: dict[str, Any] = {}
    for type_name, names in registry.items():
        if re.search(r"\b" + re.escape(type_name) + r"\b", declared_type_text):
            fields = [r for name in names for r in usable_fields if r.get("name") == name]
            if len(fields) == len(names):
                types[type_name] = fields
                member_names.update(names)
                origins[type_name] = {
                    "evidence": "requirement中的结构说明 + io_table字段类型",
                    "fields": [r["name"] for r in fields],
                }
            else:
                warnings.append(f"结构类型{type_name}的成员字段不完整，未猜测补全")
    # P08将字段名写作channels[].x；声明时只声明channels数组与其STRUCT成员。
    for row in usable_fields:
        name = str(row.get("name", ""))
        match = re.fullmatch(r"([A-Za-z_]\w*)\[\]\.(\w+)", name)
        if not match:
            continue
        parent = next((r for r in all_rows if r.get("name") == match.group(1)), None)
        if parent is None:
            warnings.append(f"{name}无对应父数组，无法投影为接口声明")
            continue
        type_match = re.search(r"\bOF\s+([A-Za-z_]\w*)\s*$", str(parent.get("data_type", "")), re.I)
        if not type_match:
            warnings.append(f"{name}的父数组未声明元素类型")
            continue
        type_name = type_match.group(1)
        field = dict(row, name=match.group(2))
        types.setdefault(type_name, []).append(field)
        member_names.add(name)
        origins.setdefault(type_name, {"evidence": "io_table显式数组成员路径", "fields": []})["fields"].append(name)

    projected = []
    seen = set()
    for row in all_rows:
        name = str(row.get("name", ""))
        if name in member_names:
            continue
        if not _IDENTIFIER.fullmatch(name):
            warnings.append(f"I/O名称{name!r}不是可独立声明的ST标识符")
            continue
        if name.lower() in seen:
            warnings.append(f"I/O名称{name!r}重复（ST标识符不区分大小写）")
            continue
        if row.get("direction") not in {"IN", "OUT", "INOUT"}:
            warnings.append(f"I/O {name}方向缺失或非法")
            continue
        data_type = row.get("data_type")
        if not isinstance(data_type, str) or not data_type.strip():
            warnings.append(f"I/O {name}类型缺失")
            continue
        # 题面是数据而非指令；防止类型文本注入额外ST声明/实现。
        if not re.fullmatch(r"[A-Za-z0-9_\s\[\]*.,():]+", data_type):
            warnings.append(f"I/O {name}类型包含不支持的声明字符")
            continue
        seen.add(name.lower())
        projected.append(dict(row))

    chunks = []
    for type_name, fields in types.items():
        lines = [f"TYPE {type_name} :", "STRUCT"]
        lines += [f"    {r['name']} : {r['data_type']};" for r in fields]
        lines += ["END_STRUCT", "END_TYPE"]
        chunks.append("\n".join(lines))

    dialect = []
    if "ARRAY[*]" in declared_type_text.replace(" ", "").upper():
        dialect.append("可变长ARRAY[*]仅用于VAR_IN_OUT，需要支持开放数组的编译profile")
    if re.search(r"\bVARIANT\b", declared_type_text, re.I):
        dialect.append("VARIANT为厂商扩展；需要目标profile的真实泛型/引用支持，不转换为固定数组或整数")
    if re.search(r"\bLTIME\b", declared_type_text, re.I):
        dialect.append("LTIME需要编译profile支持长时间类型")
    for row in projected:
        base = re.sub(r"^ARRAY\s*\[.*?\]\s*OF\s*", "", row["data_type"], flags=re.I)
        base = re.sub(r"\(.*\)$", "", base).strip()
        if base.upper() not in _ELEMENTARY_TYPES and base not in types:
            warnings.append(f"未提供自定义类型{base}的定义，骨架需补充真实类型声明")
    return projected, "\n\n".join(chunks), origins, dialect


def parse_task(path: str | Path, root: str | Path | None = None) -> dict:
    """返回可序列化任务卡。缺字段不猜测；无法读取的语法错误显式抛出。"""
    path = Path(path).resolve()
    source = path.read_bytes()
    task = _read_yaml(source.decode("utf-8-sig"))
    if not isinstance(task, dict):
        raise ValueError("题面顶层必须是映射")
    project_root = _project_root(path, root)
    missing = [key for key in REQUIRED_FIELDS if key not in task or task[key] in (None, "", [])]
    warnings: list[str] = []
    for name in ("task_id", "title", "difficulty", "category", "requirement", "initial_state", "provenance", "spec_ref"):
        if name in task and not isinstance(task[name], str):
            warnings.append(f"字段{name}必须为字符串；未自动转换或猜测")
    for name in ("io_table", "constraints"):
        if name in task and not isinstance(task[name], list):
            warnings.append(f"字段{name}必须为列表；未自动改写原数据")
    io = task.get("io_table") if isinstance(task.get("io_table"), list) else []
    for index, row in enumerate(io):
        if not isinstance(row, dict):
            warnings.append(f"io_table[{index}]必须为映射")
        else:
            absent = [key for key in ("name", "direction", "data_type", "description") if not row.get(key)]
            if absent:
                warnings.append(f"io_table[{index}]缺少{','.join(absent)}")
    task_id = task.get("task_id")
    if task_id is not None and not re.fullmatch(r"[PS]\d{2}", str(task_id)):
        warnings.append("task_id必须使用P/S加两位数字，不自动改编号")
    spec_text = ""
    spec_path = None
    if isinstance(task.get("spec_ref"), str) and task["spec_ref"]:
        spec_ref = Path(task["spec_ref"])
        candidate = (project_root / spec_ref).resolve()
        if not candidate.is_relative_to(project_root):
            warnings.append("spec_ref越出项目根目录，未读取")
        elif candidate.is_file():
            spec_path = candidate
            spec_text = candidate.read_text(encoding="utf-8-sig")
        else:
            warnings.append(f"spec_ref指向的文件不存在：{task['spec_ref']}")
    if not spec_text.strip():
        missing.append("spec_text")
    semantic = _semantic_warnings(task, spec_text)
    projection, types, origins, dialect = _interface_projection(task, warnings)
    card = {key: task.get(key) for key in REQUIRED_FIELDS}
    card.update({
        "error_examples": task.get("error_examples", []),
        "notes": task.get("notes", ""),
        "spec_text": spec_text,
        "spec_sha256": hashlib.sha256(spec_path.read_bytes()).hexdigest() if spec_path else None,
        "task_version": hashlib.sha256(source).hexdigest()[:8],
        "task_sha256": hashlib.sha256(source).hexdigest(),
        "source_path": _public_path(path, project_root),
        "degraded": bool(missing or warnings or semantic),
        "missing_fields": sorted(set(missing)),
        "warnings": warnings,
        "semantic_warnings": semantic,
        "interface_io_table": projection,
        "type_declarations": types,
        "type_origins": origins,
        "pou_name": f"FB_{task_id}" if isinstance(task_id, str) and _IDENTIFIER.fullmatch(task_id) else None,
        "pou_kind": "FUNCTION_BLOCK",
        "dialect_requirements": dialect,
        "skeleton_compiled": False,
        "scan_cycle_ms": 20,
    })
    return card

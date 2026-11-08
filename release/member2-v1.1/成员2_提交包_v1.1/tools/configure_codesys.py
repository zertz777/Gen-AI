"""只读发现CODESYS，并为已经安装的IDE和现有工程生成本机配置。

不安装软件、不启动IDE、不联网，不修改PATH、环境变量或注册表。
输出仅表示路径已核对；真正的编译结果由codesys_bridge另行产生。
"""
from __future__ import annotations

import argparse
import base64
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PLACEHOLDER = re.compile(
    r"replace[_ -]*with|placeholder|your[_ -]+(?:profile|path|template|exe)|"
    r"\b(?:todo|tbd)\b|未配置|待填写|请替换|示例路径|[<>{}]", re.I)


def require_value(value: str, label: str) -> str:
    value = str(value).strip()
    if not value or PLACEHOLDER.search(value):
        raise ValueError(label + "缺失或仍为占位符，请填写实际值")
    if any(ord(char) < 32 for char in value):
        raise ValueError(label + "包含控制字符")
    return value


def resolve_input(value: str, root: Path, label: str, extension: str) -> Path:
    path = Path(require_value(value, label)).expanduser()
    path = (root / path).resolve() if not path.is_absolute() else path.resolve()
    if not path.is_file():
        raise ValueError(label + "文件不存在：" + str(path))
    if path.suffix.lower() != extension:
        raise ValueError(label + "须为" + extension + "文件")
    return path


def portable_path(path: Path, root: Path) -> str:
    """项目内路径相对化；安装目录等外部路径只存本机local配置。"""
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def windows_file_version(path: Path) -> str | None:
    """使用只读Win32版本资源，不执行被检查文件。无版本资源则返回None。"""
    if os.name != "nt":
        return None
    try:
        import ctypes
        from ctypes import wintypes
        version = ctypes.WinDLL("version", use_last_error=True)
        size_fn = version.GetFileVersionInfoSizeW
        size_fn.argtypes = [wintypes.LPCWSTR, ctypes.POINTER(wintypes.DWORD)]
        size_fn.restype = wintypes.DWORD
        data_fn = version.GetFileVersionInfoW
        data_fn.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, ctypes.c_void_p]
        data_fn.restype = wintypes.BOOL
        query_fn = version.VerQueryValueW
        query_fn.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR,
                             ctypes.POINTER(ctypes.c_void_p), ctypes.POINTER(wintypes.UINT)]
        query_fn.restype = wintypes.BOOL
        ignored = wintypes.DWORD(0)
        size = size_fn(str(path), ctypes.byref(ignored))
        if not size:
            return None
        buffer = ctypes.create_string_buffer(size)
        if not data_fn(str(path), 0, size, buffer):
            return None
        pointer, length = ctypes.c_void_p(), wintypes.UINT()
        if not query_fn(buffer, "\\", ctypes.byref(pointer), ctypes.byref(length)) or length.value < 16:
            return None
        # VS_FIXEDFILEINFO first four DWORDs are signature, structure version, MS, LS.
        fixed = ctypes.cast(pointer, ctypes.POINTER(wintypes.DWORD))
        if fixed[0] != 0xFEEF04BD:
            return None
        ms, ls = fixed[2], fixed[3]
        return ".".join(str(n) for n in (ms >> 16, ms & 0xffff, ls >> 16, ls & 0xffff))
    except (OSError, AttributeError, ValueError):
        return None


def inspect_signature(path: Path) -> dict[str, Any]:
    """可选、只读Authenticode查询。失败不等于已经验证签名。"""
    if os.name != "nt":
        return {"status": "not_checked", "reason": "Windows Authenticode检查仅支持Windows"}
    shell = shutil.which("pwsh.exe") or shutil.which("powershell.exe")
    if not shell:
        return {"status": "not_checked", "reason": "未发现PowerShell"}
    # 路径先编码为纯base64文本，再整体编码命令；不把文件名当PowerShell代码。
    encoded_path = base64.b64encode(str(path).encode("utf-8")).decode("ascii")
    script = (
        "$ErrorActionPreference='Stop'; [Console]::OutputEncoding=[Text.Encoding]::UTF8; "
        "$p=[Text.Encoding]::UTF8.GetString([Convert]::FromBase64String('" + encoded_path + "')); "
        "$s=Get-AuthenticodeSignature -LiteralPath $p; "
        "[pscustomobject]@{status=[string]$s.Status; "
        "subject=if($s.SignerCertificate){$s.SignerCertificate.Subject}else{$null}; "
        "thumbprint=if($s.SignerCertificate){$s.SignerCertificate.Thumbprint}else{$null}} "
        "| ConvertTo-Json -Compress"
    )
    try:
        encoded_command = base64.b64encode(script.encode("utf-16-le")).decode("ascii")
        completed = subprocess.run(
            [shell, "-NoLogo", "-NoProfile", "-NonInteractive", "-EncodedCommand", encoded_command],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30,
            check=False)
        if completed.returncode != 0:
            return {"status": "not_checked", "reason": "PowerShell签名查询失败",
                    "returncode": completed.returncode}
        result = json.loads(completed.stdout.lstrip("\ufeff").strip())
        if not isinstance(result, dict) or "status" not in result:
            raise ValueError("signature response is not a mapping")
        return result
    except (OSError, subprocess.TimeoutExpired, ValueError):
        return {"status": "not_checked", "reason": "签名查询不可用或结果无效"}


def default_search_roots() -> list[Path]:
    roots = []
    for name in ("ProgramFiles", "ProgramFiles(x86)", "ProgramData"):
        if os.environ.get(name):
            roots.append(Path(os.environ[name]))
    if os.name == "nt":
        roots.extend((Path("C:/CODESYS"), Path("D:/CODESYS")))
    return roots


def probe(roots: list[Path], max_depth: int = 6, check: bool = False) -> dict[str, Any]:
    """有限深度只读遍历；不跟随链接、不读配置正文、不访问网络。"""
    if not 0 <= max_depth <= 12:
        raise ValueError("max-depth必须在0..12之间")
    exe_paths: set[Path] = set()
    profile_paths: set[Path] = set()
    searched, missing, inaccessible = [], [], []
    seen: set[str] = set()
    for raw in roots:
        root = raw.expanduser().resolve()
        key = str(root).casefold()
        if key in seen:
            continue
        seen.add(key)
        if not root.is_dir():
            missing.append(str(root))
            continue
        searched.append(str(root))

        def on_error(error: OSError) -> None:
            inaccessible.append(str(getattr(error, "filename", "")))

        for current, dirs, files in os.walk(root, followlinks=False, onerror=on_error):
            current_path = Path(current)
            depth = len(current_path.relative_to(root).parts)
            dirs[:] = sorted(name for name in dirs
                             if not (current_path / name).is_symlink()) if depth < max_depth else []
            for name in files:
                candidate = current_path / name
                if candidate.is_symlink():
                    continue
                if name.casefold() == "codesys.exe":
                    exe_paths.add(candidate.resolve())
                elif name.casefold().endswith((".profile", ".profile.xml")):
                    profile_paths.add(candidate.resolve())
    executables = []
    for path in sorted(exe_paths):
        entry: dict[str, Any] = {"path": str(path), "file_version": windows_file_version(path)}
        if check:
            entry["signature"] = inspect_signature(path)
        executables.append(entry)
    return {"operation": "read_only_probe", "searched_roots": searched,
            "missing_roots": missing, "inaccessible_paths": sorted(set(inaccessible)),
            "max_depth": max_depth, "executables": executables,
            "profiles": [{"path": str(path), "possible_profile_name": path.name[:-12] if path.name.lower().endswith('.profile.xml') else path.stem,
                          "profile_name_verified": False} for path in sorted(profile_paths)],
            "compile_status": "not_run", "network_access": False,
            "note": "profile名称仅由文件名发现；需在IDE帮助/关于核实，未启动编译或验证工程"}


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(temp, path)


def configure(exe: str, profile: str, template: str, *, root: Path = ROOT,
              out: str | None = None, application: str = "Application",
              additionalfolder: str | None = None, check: bool = False) -> dict[str, Any]:
    root = root.resolve()
    profile = require_value(profile, "profile名称")
    application = require_value(application, "Application名称")
    exe_path = resolve_input(exe, root, "CODESYS可执行程序", ".exe")
    template_path = resolve_input(template, root, "CODESYS模板工程", ".project")
    if exe_path.name.casefold() != "codesys.exe":
        raise ValueError("请指定安装目录内的CODESYS.exe，不要指定Installer或其他可执行文件")
    with exe_path.open("rb") as stream:
        header = stream.read(64)
        if len(header) < 64 or header[:2] != b"MZ":
            raise ValueError("CODESYS.exe缺少Windows PE文件头，未生成配置")
        pe_offset = int.from_bytes(header[60:64], "little")
        if pe_offset < 64 or pe_offset + 4 > exe_path.stat().st_size:
            raise ValueError("CODESYS.exe的PE文件头位置无效，未生成配置")
        stream.seek(pe_offset)
        if stream.read(4) != b"PE\x00\x00":
            raise ValueError("CODESYS.exe缺少有效PE签名，未生成配置")
    if template_path.stat().st_size == 0:
        raise ValueError("模板工程为空文件")
    config_source = root / "agent/configs/default.yaml"
    bridge = root / "agent/scripts/codesys_bridge.py"
    if not bridge.is_file():
        raise ValueError("项目内缺少agent/scripts/codesys_bridge.py")
    try:
        config = json.loads(config_source.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as exc:
        raise ValueError("default.yaml必须是项目提供的JSON格式配置") from exc
    if not isinstance(config, dict) or not isinstance(config.get("tools"), dict):
        raise ValueError("默认配置缺少tools映射")
    local = (root / "local").resolve()
    destination = Path(out) if out else local / "codesys.local.yaml"
    if not destination.is_absolute():
        destination = root / destination
    destination = destination.resolve()
    if not destination.is_relative_to(local):
        raise ValueError("本机路径配置只能保存到项目local目录，请将--out设为local/文件名.yaml")
    if destination == (local / "codesys_environment.json"):
        raise ValueError("配置输出不能覆盖环境登记文件")
    extra_path = None
    if additionalfolder:
        extra_path = Path(require_value(additionalfolder, "additionalfolder")).expanduser()
        extra_path = (root / extra_path).resolve() if not extra_path.is_absolute() else extra_path.resolve()
        if not extra_path.is_dir():
            raise ValueError("additionalfolder目录不存在")
    command = [portable_path(Path(sys.executable), root), "agent/scripts/codesys_bridge.py",
               "--source", "{source}", "--result", "{result}", "--task-card", "{task_card}",
               "--exe", portable_path(exe_path, root), "--profile", profile,
               "--template", portable_path(template_path, root), "--application", application]
    if extra_path:
        command.extend(("--additionalfolder", portable_path(extra_path, root)))
    config["tools"]["authoritative"] = {
        **config["tools"].get("authoritative", {}), "command": command}
    environment: dict[str, Any] = {
        "schema_version": "1.0", "recorded_at": datetime.now(timezone.utc).isoformat(),
        "configuration_status": "paths_checked_compilation_not_run", "compile_status": "not_run",
        "config_path": portable_path(destination, root),
        "codesys": {"executable": portable_path(exe_path, root),
                    "file_version": windows_file_version(exe_path), "sha256": sha256_file(exe_path),
                    "profile": profile, "profile_verified_in_ide": False,
                    "additionalfolder": portable_path(extra_path, root) if extra_path else None},
        "template": {"path": portable_path(template_path, root),
                     "sha256": sha256_file(template_path), "size_bytes": template_path.stat().st_size,
                     "application": application, "opened_in_codesys": False},
        "python": {"executable": portable_path(Path(sys.executable), root),
                   "version": platform.python_version()},
        "os": {"system": platform.system(), "release": platform.release(),
               "version": platform.version(), "architecture": platform.machine()},
        "network_access": False,
        "limitations": ["文件存在与哈希不证明工程有效、profile匹配或编译通过",
                        "设备/库/编译器精确版本需在真实IDE中补录",
                        "未验证API、快检、功能测试或跨机复现"],
    }
    if check:
        environment["codesys"]["signature"] = inspect_signature(exe_path)
    else:
        environment["codesys"]["signature"] = {"status": "not_checked", "reason": "未指定--check"}
    # 校验全部通过后再写local；默认配置、模板、安装文件始终只读。
    write_json(destination, config)
    write_json(local / "codesys_environment.json", environment)
    return {"config": portable_path(destination, root),
            "environment": "local/codesys_environment.json", "compile_status": "not_run",
            "profile": profile, "file_version": environment["codesys"]["file_version"]}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", help="已安装CODESYS.exe；不是Installer")
    parser.add_argument("--profile", help="IDE帮助/关于中核实的完整profile名称")
    parser.add_argument("--template", help="现有真实.project模板工程")
    parser.add_argument("--application", default="Application")
    parser.add_argument("--additionalfolder", help="可选CODESYS安装实例附加目录")
    parser.add_argument("--out", help="本机配置输出；默认local/codesys.local.yaml")
    parser.add_argument("--probe", action="store_true", help="只读发现可能安装路径及.profile文件，不写配置")
    parser.add_argument("--search-root", action="append", default=[], help="probe搜索根目录，可重复")
    parser.add_argument("--max-depth", type=int, default=6, help="probe最大目录层数0..12，默认6")
    parser.add_argument("--check", action="store_true", help="附加只读Authenticode签名检查")
    args = parser.parse_args(argv)
    try:
        if args.probe:
            if args.exe or args.profile or args.template or args.out or args.additionalfolder:
                parser.error("--probe只读模式不要同时填写配置参数")
            roots = [Path(value) for value in args.search_root] or default_search_roots()
            result = probe(roots, args.max_depth, args.check)
        else:
            if args.search_root:
                parser.error("--search-root只用于--probe")
            if not all((args.exe, args.profile, args.template)):
                parser.error("生成配置需要--exe、--profile、--template；只读发现请用--probe")
            result = configure(args.exe, args.profile, args.template, out=args.out,
                               application=args.application, additionalfolder=args.additionalfolder,
                               check=args.check)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

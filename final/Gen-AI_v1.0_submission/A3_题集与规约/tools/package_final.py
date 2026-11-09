"""Build final A1-A7 submission tree and zip from the frozen repository."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FINAL = ROOT / "final"
TREE = FINAL / "Gen-AI_v1.0_submission"
ZIP_PATH = FINAL / "Gen-AI_v1.0_submission.zip"
LOCAL_ABSOLUTE = re.compile(
    r"(?<![A-Za-z])[A-Z]:[\\/](?:Users|Documents|Program Files|Windows|MWORKS)[^\"'\r\n]*",
    re.IGNORECASE,
)
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


def copy_tree(source: Path, destination: Path, *, sanitize: bool = True) -> None:
    if not source.exists():
        raise FileNotFoundError(source)
    for path in source.rglob("*"):
        if not path.is_file():
            continue
        if "__pycache__" in path.parts or path.suffix.lower() in {".pyc", ".pyo", ".tmp", ".bak"}:
            continue
        relative = path.relative_to(source)
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if sanitize and path.suffix.lower() in TEXT_SUFFIXES:
            text = path.read_text(encoding="utf-8", errors="ignore")
            target.write_text(LOCAL_ABSOLUTE.sub("<LOCAL_PATH>", text), encoding="utf-8")
        else:
            shutil.copy2(path, target)


def copy_file(source: Path, destination: Path) -> None:
    if not source.is_file():
        raise FileNotFoundError(source)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if source.suffix.lower() in TEXT_SUFFIXES:
        text = source.read_text(encoding="utf-8", errors="ignore")
        destination.write_text(LOCAL_ABSOLUTE.sub("<LOCAL_PATH>", text), encoding="utf-8")
    else:
        shutil.copy2(source, destination)


def build_readme() -> str:
    return """GenAI 赋能工业编程期末大作业 A1-A7 提交包

解压后在根目录按 README.md 的三条命令先做无费用 fixture 验收。
真实模型与 CODESYS 复现需要额外配置，见 docs/env.md、docs/codesys_setup.md 和 docs/toolchain.md。

目录：
A1_报告：Word 与 PDF
A2_框架源码：自研 Agent、Aider 适配层、配置与示例日志
A3_题集与规约：34 份题面与 LTL
A4_测试与验证：用例、执行器、缺陷单、变异测试与 PLCVerif 材料
A5_实验原始数据：136 个最终 run、32 个修订 run、原始批次、汇总与 4 图
A6_运行说明：README、环境、工具链与问答
A7_汇报材料：15 页 PPT、讲稿与主问答

实验结果的已知限制：
- E3 有 24 题受预算终止影响，其中存在 token 预算实现问题。
- P19、S11、S05-06 的判据争议不能作为框架或模型优劣的决定性证据。
- 精简实验包只保留结果、候选评估和最终 ST，不包含完整逐拍 actual 中间文件。
- 换机复现模型、CODESYS 和 Aider 尚未验证。

本包不含 API Key、本机绝对路径或临时文件。

备份建议：
- 将本 ZIP 上传云盘并保留一份本地硬盘副本。
- 将 A1 的 PDF与 A7 的 PPT 另存到演示 U 盘。
- 现场演示使用本包内 PPT；完整 CODESYS 逐拍重放仍需实验机原始批次。
"""


def build() -> tuple[Path, Path]:
    if not TREE.resolve().is_relative_to((ROOT / "final").resolve()):
        raise RuntimeError(f"Refusing to replace path outside final/: {TREE}")
    if TREE.exists():
        shutil.rmtree(TREE)
    TREE.mkdir(parents=True)

    a1 = TREE / "A1_报告"
    copy_file(ROOT / "docs" / "report" / "report_v3.docx", a1 / "report_v3.docx")
    copy_file(ROOT / "docs" / "report" / "report_v3.pdf", a1 / "report_v3.pdf")

    a2 = TREE / "A2_框架源码"
    copy_tree(ROOT / "agent", a2 / "agent")
    copy_tree(ROOT / "baseline", a2 / "baseline")
    copy_tree(ROOT / "tests_unit", a2 / "tests_unit")
    for name in ("requirements.txt", "requirements-baseline.txt"):
        copy_file(ROOT / name, a2 / name)
    for name in ("env.md", "framework.md", "toolchain.md", "codesys_setup.md", "codesys_validation.md"):
        copy_file(ROOT / "docs" / name, a2 / "docs" / name)
    copy_file(ROOT / "docs" / "qa" / "member2.md", a2 / "docs" / "qa" / "member2.md")

    a3 = TREE / "A3_题集与规约"
    copy_tree(ROOT / "data", a3 / "data")
    copy_tree(ROOT / "refs", a3 / "refs")
    copy_tree(ROOT / "tools", a3 / "tools")

    a4 = TREE / "A4_测试与验证"
    copy_tree(ROOT / "tests", a4 / "tests")
    copy_tree(ROOT / "verify", a4 / "verify")
    copy_tree(ROOT / "examples", a4 / "examples")

    a5 = TREE / "A5_实验原始数据"
    copy_tree(ROOT / "experiments", a5 / "experiments")
    copy_tree(ROOT / "figures", a5 / "figures")

    a6 = TREE / "A6_运行说明"
    for name in ("README.md", "requirements.txt", "requirements-baseline.txt"):
        copy_file(ROOT / name, a6 / name)
    for name in (
        "env.md",
        "codesys_setup.md",
        "codesys_validation.md",
        "framework.md",
        "toolchain.md",
        "tasks_note.md",
        "standup.md",
        "check.md",
    ):
        copy_file(ROOT / "docs" / name, a6 / "docs" / name)
    copy_file(ROOT / "checklist.md", a6 / "checklist.md")

    a7 = TREE / "A7_汇报材料"
    copy_file(ROOT / "docs" / "slides" / "deck.pptx", a7 / "deck.pptx")
    copy_file(ROOT / "docs" / "slides" / "script.md", a7 / "script.md")
    for path in sorted((ROOT / "docs" / "qa").glob("member*.md")):
        copy_file(path, a7 / "qa" / path.name)

    (TREE / "README.txt").write_text(build_readme(), encoding="utf-8")

    manifest = []
    for path in sorted(TREE.rglob("*")):
        if path.is_file():
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            manifest.append(
                {
                    "path": path.relative_to(TREE).as_posix(),
                    "bytes": path.stat().st_size,
                    "sha256": digest,
                }
            )
    (TREE / "MANIFEST.json").write_text(
        json.dumps(
            {"file_count": len(manifest), "total_bytes": sum(item["bytes"] for item in manifest), "files": manifest},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    if ZIP_PATH.exists():
        ZIP_PATH.unlink()
    with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(TREE.rglob("*")):
            if path.is_file():
                archive.write(path, f"{TREE.name}/{path.relative_to(TREE).as_posix()}")
    digest_lines = []
    for path in (
        ZIP_PATH,
        ROOT / "docs" / "report" / "report_v3.docx",
        ROOT / "docs" / "report" / "report_v3.pdf",
        ROOT / "docs" / "slides" / "deck.pptx",
    ):
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        digest_lines.append(f"{digest}  {path.relative_to(ROOT).as_posix()}")
    (FINAL / "FINAL_SHA256SUMS.txt").write_text(
        "\n".join(digest_lines) + "\n", encoding="utf-8"
    )
    return TREE, ZIP_PATH


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    tree, archive = build()
    print(f"tree: {tree}")
    print(f"zip: {archive}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

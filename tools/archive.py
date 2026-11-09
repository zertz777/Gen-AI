"""Create a deterministic source snapshot with SHA-256 evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXCLUDED_PARTS = {
    ".git",
    "__pycache__",
    ".pytest_cache",
    "local",
    "runs",
    "release",
    "final",
    "tmp",
    "rendered",
}
EXCLUDED_SUFFIXES = {".pyc", ".pyo", ".tmp", ".bak", ".swp"}
MAX_FILE_BYTES = 20 * 1024 * 1024


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def should_include(path: Path) -> bool:
    relative = path.relative_to(ROOT)
    if any(part in EXCLUDED_PARTS for part in relative.parts):
        return False
    if path.suffix.lower() in EXCLUDED_SUFFIXES:
        return False
    return path.is_file()


def create_snapshot(output_dir: Path, version: str) -> tuple[Path, Path, Path]:
    files = sorted(path for path in ROOT.rglob("*") if should_include(path))
    oversized = [
        (path.relative_to(ROOT).as_posix(), path.stat().st_size)
        for path in files
        if path.stat().st_size > MAX_FILE_BYTES
    ]
    if oversized:
        raise ValueError(f"Files over 20 MB must use a release asset: {oversized}")

    output_dir.mkdir(parents=True, exist_ok=True)
    archive_path = output_dir / f"Gen-AI_{version}_source.zip"
    hashes_path = output_dir / "SHA256SUMS.txt"
    manifest_path = output_dir / "MANIFEST.json"

    records = []
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            relative = path.relative_to(ROOT).as_posix()
            digest = sha256(path)
            records.append({"path": relative, "bytes": path.stat().st_size, "sha256": digest})
            archive.write(path, relative)

    manifest = {
        "version": version,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "source_root": ".",
        "file_count": len(records),
        "total_bytes": sum(record["bytes"] for record in records),
        "excluded": sorted(EXCLUDED_PARTS),
        "largest_file_limit_bytes": MAX_FILE_BYTES,
        "files": records,
    }
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    hashes_path.write_text(
        "".join(f"{record['sha256']}  {record['path']}\n" for record in records),
        encoding="utf-8",
    )
    return archive_path, hashes_path, manifest_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=ROOT / "release" / "v1.0")
    parser.add_argument("--version", default="v1.0")
    args = parser.parse_args()
    archive, hashes, manifest = create_snapshot(args.out, args.version)
    print(f"archive: {archive}")
    print(f"hashes: {hashes}")
    print(f"manifest: {manifest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

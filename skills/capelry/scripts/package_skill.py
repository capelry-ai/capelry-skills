#!/usr/bin/env python3
"""Create a deterministic Capelry skill archive from an explicit source allowlist."""

from __future__ import annotations

import argparse
import re
import tempfile
import zipfile
from pathlib import Path

ROOT_FILES = ("capability.yaml", "SKILL.md", "BOOTSTRAP.md", "ai-catalog.json")
RESOURCE_DIRS = ("agents", "scripts", "references", "assets")
EXCLUDED_PARTS = {"__pycache__"}
EXCLUDED_SUFFIXES = {".bak", ".orig", ".pyc", ".pyo", ".swp", ".tmp", ".zip"}


def manifest_version(skill_dir: Path) -> str:
    manifest = skill_dir / "capability.yaml"
    text = manifest.read_text(encoding="utf-8")
    match = re.search(r"^\s{2}version:\s*[\"']?(?P<version>\d+\.\d+\.\d+)[\"']?\s*$", text, re.MULTILINE)
    if not match:
        raise SystemExit(f"Unable to read metadata.version from {manifest}")
    return match.group("version")


def archive_members(skill_dir: Path) -> list[Path]:
    skill_root = skill_dir.resolve()
    members = []
    for relative in ROOT_FILES:
        path = skill_dir / relative
        if path.is_symlink():
            raise SystemExit(f"Refusing to package symlink: {relative}")
        if not path.is_file():
            raise SystemExit(f"Required package file is missing: {path}")
        try:
            path.resolve().relative_to(skill_root)
        except ValueError as error:
            raise SystemExit(f"Package file escapes skill directory: {relative}") from error
        members.append(path)
    for directory_name in RESOURCE_DIRS:
        directory = skill_dir / directory_name
        if directory.is_symlink():
            raise SystemExit(f"Refusing to package symlink: {directory_name}")
        if not directory.exists():
            continue
        for path in directory.rglob("*"):
            relative = path.relative_to(skill_dir)
            if path.is_symlink():
                raise SystemExit(f"Refusing to package symlink: {relative}")
            if not path.is_file():
                continue
            try:
                path.resolve().relative_to(skill_root)
            except ValueError as error:
                raise SystemExit(f"Package file escapes skill directory: {relative}") from error
            if any(part.startswith(".") or part in EXCLUDED_PARTS for part in relative.parts):
                continue
            if path.name.endswith("~") or path.suffix.lower() in EXCLUDED_SUFFIXES:
                continue
            members.append(path)
    return sorted(set(members), key=lambda path: path.relative_to(skill_dir).as_posix())


def write_archive(skill_dir: Path, output: Path) -> list[str]:
    members = archive_members(skill_dir)
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(prefix=f".{output.name}.", suffix=".tmp", dir=output.parent, delete=False) as handle:
        temporary = Path(handle.name)
    try:
        with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            for path in members:
                relative = path.relative_to(skill_dir).as_posix()
                info = zipfile.ZipInfo(relative, date_time=(1980, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = (0o755 if path.suffix == ".py" else 0o644) << 16
                archive.writestr(info, path.read_bytes())
        temporary.replace(output)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise
    return [path.relative_to(skill_dir).as_posix() for path in members]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Package the Capelry skill without caches or repository-only files")
    parser.add_argument("--skill-dir", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path, help="Archive path (default: ./capelry-X.Y.Z.zip)")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    skill_dir = args.skill_dir.resolve()
    version = manifest_version(skill_dir)
    output = (args.output or Path.cwd() / f"capelry-{version}.zip").resolve()
    members = write_archive(skill_dir, output)
    print(f"Created {output} with {len(members)} source files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

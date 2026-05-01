#!/usr/bin/env python3
"""Small stdlib-only client for the Capelry capability registry."""

from __future__ import annotations

import argparse
import io
import json
import os
import re
import shutil
import sys
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path
from typing import Any

DEFAULT_REGISTRY = "https://capelry.com"

TARGET_ROOTS = {
    "agents-project": ".agents/skills",
    "pi-project": ".pi/skills",
    "claude-project": ".claude/skills",
    "codex-project": ".codex/skills",
    "agents-global": "~/.agents/skills",
    "pi-global": "~/.pi/agent/skills",
    "claude-global": "~/.claude/skills",
    "codex-global": "~/.codex/skills",
}


def eprint(*parts: object) -> None:
    print(*parts, file=sys.stderr)


def registry_base(args: argparse.Namespace) -> str:
    return (args.registry or os.environ.get("CAPELRY_REGISTRY_URL") or DEFAULT_REGISTRY).rstrip("/")


def api_url(base: str, path: str) -> str:
    return f"{base}{path if path.startswith('/') else '/' + path}"


def fetch_bytes(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "capelry-skill/0.1"})
    try:
        with urllib.request.urlopen(request) as response:
            return response.read()
    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8", errors="replace")
        raise SystemExit(f"HTTP {error.code} for {url}\n{body}") from error
    except urllib.error.URLError as error:
        raise SystemExit(f"Unable to reach {url}: {error.reason}") from error


def fetch_json(url: str) -> Any:
    return json.loads(fetch_bytes(url).decode("utf-8"))


def parse_ref(value: str) -> tuple[str, str, str | None]:
    ref, _, version = value.partition("@")
    if "/" not in ref:
        raise SystemExit("Capability ref must be namespace/name, optionally namespace/name@version")
    namespace, name = ref.split("/", 1)
    if not namespace or not name:
        raise SystemExit("Capability ref must be namespace/name")
    return namespace, name, version or None


def capability_detail(base: str, ref: str) -> dict[str, Any]:
    namespace, name, _ = parse_ref(ref)
    return fetch_json(api_url(base, f"/api/capabilities/{namespace}/{name}"))["capability"]


def latest_version(capability: dict[str, Any]) -> str:
    latest = capability.get("latestVersion") or {}
    version = latest.get("version")
    if not isinstance(version, str) or not version:
        raise SystemExit("Capability has no latest version")
    return version


def command_search(args: argparse.Namespace) -> None:
    base = registry_base(args)
    query = urllib.parse.urlencode({"q": args.query})
    payload = fetch_json(api_url(base, f"/api/capabilities?{query}"))
    capabilities = payload.get("capabilities", [])
    if not capabilities:
        print("No capabilities found.")
        return

    for item in capabilities[: args.limit]:
        latest = item.get("latestVersion") or {}
        ref = f"{item.get('namespace')}/{item.get('name')}"
        version = latest.get("version", "?")
        package_type = item.get("packageType", "capability")
        summary = item.get("summary") or item.get("description") or ""
        print(f"{ref}@{version} [{package_type}] {summary}")


def command_info(args: argparse.Namespace) -> None:
    base = registry_base(args)
    capability = capability_detail(base, args.ref)
    latest = capability.get("latestVersion") or {}
    source = capability.get("source") or {}

    print(f"{capability['namespace']}/{capability['name']}@{latest.get('version', '?')}")
    print(f"type: {capability.get('packageType', 'capability')}")
    print(f"status: {latest.get('validationStatus', '?')}")
    if capability.get("summary"):
        print(f"summary: {capability['summary']}")
    if capability.get("description"):
        print(f"description: {capability['description']}")
    if source.get("repository"):
        print(f"source: {source['repository']}")
    if source.get("path"):
        print(f"source path: {source['path']}")
    print(f"page: {base}/{capability['namespace']}/{capability['name']}")
    if latest.get("checksumSha256"):
        print(f"checksum: {latest['checksumSha256']}")


def safe_zip_members(zf: zipfile.ZipFile):
    for member in zf.infolist():
        if member.is_dir():
            continue
        path = Path(member.filename)
        if path.is_absolute() or ".." in path.parts:
            raise SystemExit(f"Unsafe archive path: {member.filename}")
        yield member


def skill_prefix_in_archive(zf: zipfile.ZipFile) -> str | None:
    names = [member.filename.rstrip("/") for member in safe_zip_members(zf)]
    if "SKILL.md" in names:
        return ""
    skill_files = [name for name in names if name.endswith("/SKILL.md")]
    if len(skill_files) == 1:
        return skill_files[0][: -len("SKILL.md")]
    return None


def prepare_dest(dest: Path, force: bool) -> None:
    if dest.exists():
        if not force:
            raise SystemExit(f"Destination already exists: {dest}\nUse --force to replace it.")
        shutil.rmtree(dest)
    dest.mkdir(parents=True, exist_ok=True)


def extract_skill_archive(archive: bytes, dest: Path, force: bool) -> bool:
    with zipfile.ZipFile(io.BytesIO(archive)) as zf:
        prefix = skill_prefix_in_archive(zf)
        if prefix is None:
            return False
        prepare_dest(dest, force)
        for member in safe_zip_members(zf):
            filename = member.filename
            if prefix:
                if not filename.startswith(prefix):
                    continue
                rel = filename[len(prefix) :].lstrip("/")
            else:
                rel = filename
            if not rel:
                continue
            out = dest / rel
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(zf.read(member))
    return True


def github_parts(repository: str) -> tuple[str, str] | None:
    match = re.search(r"github\.com[:/](?P<owner>[^/]+)/(?P<repo>[^/]+?)(?:\.git)?/?$", repository)
    if not match:
        return None
    return match.group("owner"), match.group("repo")


def github_api_url(owner: str, repo: str, path: str, ref: str) -> str:
    quoted_path = urllib.parse.quote(path.strip("/"))
    return f"https://api.github.com/repos/{owner}/{repo}/contents/{quoted_path}?ref={urllib.parse.quote(ref)}"


def source_relative_path(entry_path: str, root_path: str) -> str:
    if entry_path == root_path:
        return Path(entry_path).name
    try:
        return Path(entry_path).relative_to(root_path).as_posix()
    except ValueError:
        return Path(entry_path).name


def download_github_path(
    owner: str,
    repo: str,
    path: str,
    ref: str,
    dest: Path,
    root_path: str | None = None,
) -> None:
    root_path = root_path or path.rstrip("/")
    payload = fetch_json(github_api_url(owner, repo, path, ref))
    if isinstance(payload, dict):
        if payload.get("type") != "file":
            raise SystemExit(f"Unsupported GitHub content type at {path}: {payload.get('type')}")
        target = dest / source_relative_path(path, root_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(fetch_bytes(payload["download_url"]))
        return

    if not isinstance(payload, list):
        raise SystemExit(f"Unexpected GitHub API response for {path}")

    for entry in payload:
        entry_type = entry.get("type")
        entry_path = entry.get("path")
        if not isinstance(entry_path, str):
            continue
        rel = source_relative_path(entry_path, root_path)
        if entry_type == "file":
            out = dest / rel
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(fetch_bytes(entry["download_url"]))
        elif entry_type == "dir":
            download_github_path(owner, repo, entry_path, ref, dest, root_path)


def install_from_github_source(capability: dict[str, Any], dest: Path, force: bool) -> bool:
    source = capability.get("source") or {}
    repository = source.get("repository")
    source_path = source.get("path")
    branch = source.get("defaultBranch") or "main"
    if not isinstance(repository, str) or not isinstance(source_path, str):
        return False
    parts = github_parts(repository)
    if parts is None:
        return False

    owner, repo = parts
    prepare_dest(dest, force)
    download_github_path(owner, repo, source_path, branch, dest)
    if not (dest / "SKILL.md").exists():
        shutil.rmtree(dest, ignore_errors=True)
        raise SystemExit("GitHub source fallback completed but did not produce SKILL.md")
    return True


def resolve_install_dest(args: argparse.Namespace, capability_name: str) -> Path:
    if args.dest:
        return Path(args.dest).expanduser()
    root = TARGET_ROOTS[args.target]
    return Path(root).expanduser() / (args.name or capability_name)


def installed_skill_name(dest: Path) -> str:
    skill_file = dest / "SKILL.md"
    try:
        text = skill_file.read_text(encoding="utf-8")
    except OSError:
        return dest.name
    match = re.search(r"(?m)^name:\s*['\"]?([a-z0-9][a-z0-9-]*)['\"]?\s*$", text)
    return match.group(1) if match else dest.name


def command_install(args: argparse.Namespace) -> None:
    base = registry_base(args)
    namespace, name, version_in_ref = parse_ref(args.ref)
    capability = capability_detail(base, args.ref)
    version = args.version or version_in_ref or latest_version(capability)
    dest = resolve_install_dest(args, name)

    archive_url = api_url(base, f"/api/capabilities/{namespace}/{name}/versions/{version}/download")
    print(f"Downloading {namespace}/{name}@{version} from {base}...")
    archive = fetch_bytes(archive_url)

    if extract_skill_archive(archive, dest, args.force):
        installed_from = "validated Capelry archive"
    elif install_from_github_source(capability, dest, args.force):
        installed_from = "declared GitHub source fallback"
    else:
        raise SystemExit("Package did not contain SKILL.md and no supported source fallback was available")

    skill_name = installed_skill_name(dest)
    print(f"Installed {namespace}/{name}@{version} to {dest}")
    print(f"source: {installed_from}")
    print("Next: reload or restart your agent. In Pi, run /reload and then /skill:" + skill_name)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Search and install skills from Capelry")
    parser.add_argument("--registry", help=f"Registry base URL (default: {DEFAULT_REGISTRY} or CAPELRY_REGISTRY_URL)")
    subparsers = parser.add_subparsers(dest="command", required=True)

    search = subparsers.add_parser("search", help="Search capabilities")
    search.add_argument("query")
    search.add_argument("--limit", type=int, default=20)
    search.set_defaults(func=command_search)

    info = subparsers.add_parser("info", help="Show capability details")
    info.add_argument("ref", help="namespace/name")
    info.set_defaults(func=command_info)

    install = subparsers.add_parser("install", help="Install a skill capability")
    install.add_argument("ref", help="namespace/name or namespace/name@version")
    install.add_argument("--version", help="Version override")
    install.add_argument("--target", choices=sorted(TARGET_ROOTS), default="agents-project")
    install.add_argument("--dest", help="Exact destination directory")
    install.add_argument("--name", help="Install directory name override")
    install.add_argument("--force", action="store_true", help="Replace an existing destination")
    install.set_defaults(func=command_install)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

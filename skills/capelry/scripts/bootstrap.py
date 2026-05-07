#!/usr/bin/env python3
"""OS-neutral bootstrap installer for the Capelry skill.

Bootstrapping intentionally installs the skill from GitHub source, not from
Capelry.com, so a fresh project can acquire Capelry before it knows how to talk
to the registry. After install, normal registry operations still default to
https://capelry.com via scripts/capelry.py.

Defaults:
  source: https://github.com/capelry-ai/capelry-skills
  ref:    main
  paths:  skills/capelry, .pi/skills/capelry
  dest:   .agents/skills/capelry
"""

from __future__ import annotations

import argparse
import io
import os
import re
import shutil
import sys
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path, PurePosixPath
from typing import Iterable

DEFAULT_SOURCE_REPOSITORY = "https://github.com/capelry-ai/capelry-skills"
DEFAULT_SOURCE_REF = "main"
DEFAULT_SOURCE_PATHS = ("skills/capelry", ".pi/skills/capelry")
DEFAULT_SKILLS_DIR = ".agents/skills"
DEFAULT_SKILL_NAME = "capelry"

TARGET_SKILLS_DIRS = {
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


def fetch_bytes(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "capelry-bootstrap/1.1.0"})
    try:
        with urllib.request.urlopen(request) as response:
            return response.read()
    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8", errors="replace")
        raise SystemExit(f"HTTP {error.code} for {url}\n{body}") from error
    except urllib.error.URLError as error:
        raise SystemExit(f"Unable to reach {url}: {error.reason}") from error


def github_owner_repo(repository: str) -> tuple[str, str]:
    match = re.search(r"github\.com[:/](?P<owner>[^/]+)/(?P<repo>[^/]+?)(?:\.git)?/?$", repository)
    if not match:
        raise SystemExit("Bootstrap source repository must be a GitHub repository URL")
    return match.group("owner"), match.group("repo")


def github_archive_url(repository: str, ref: str) -> str:
    owner, repo = github_owner_repo(repository)
    return f"https://codeload.github.com/{owner}/{repo}/zip/{urllib.parse.quote(ref)}"


def normalize_source_path(value: str) -> str:
    normalized = value.strip().replace("\\", "/").strip("/")
    if not normalized:
        raise SystemExit("Source path cannot be empty")
    return normalized


def candidate_source_paths(source_path: str | None) -> tuple[str, ...]:
    if source_path:
        return (normalize_source_path(source_path),)
    return DEFAULT_SOURCE_PATHS


def safe_file_members(zf: zipfile.ZipFile) -> Iterable[zipfile.ZipInfo]:
    for member in zf.infolist():
        if member.is_dir():
            continue
        path = PurePosixPath(member.filename)
        if path.is_absolute() or ".." in path.parts:
            raise SystemExit(f"Unsafe archive path: {member.filename}")
        yield member


def archive_member_rel(member: zipfile.ZipInfo) -> str:
    """Return a member path relative to the GitHub archive root directory."""
    parts = PurePosixPath(member.filename).parts
    if len(parts) <= 1:
        return ""
    return PurePosixPath(*parts[1:]).as_posix()


def read_text(zf: zipfile.ZipFile, member: zipfile.ZipInfo) -> str:
    return zf.read(member).decode("utf-8", errors="replace")


def find_skill_source(
    zf: zipfile.ZipFile,
    candidates: tuple[str, ...],
) -> tuple[str, dict[str, zipfile.ZipInfo]]:
    rel_members: dict[str, zipfile.ZipInfo] = {}
    for member in safe_file_members(zf):
        rel = archive_member_rel(member)
        if rel:
            rel_members[rel] = member

    for candidate in candidates:
        if f"{candidate}/SKILL.md" in rel_members:
            return candidate, rel_members

    capelry_skill_dirs: list[str] = []
    for rel, member in rel_members.items():
        if not rel.endswith("/SKILL.md"):
            continue
        text = read_text(zf, member)
        if re.search(r"(?m)^name:\s*['\"]?capelry['\"]?\s*$", text) or "# Capelry" in text:
            capelry_skill_dirs.append(rel[: -len("/SKILL.md")])

    if len(capelry_skill_dirs) == 1:
        return capelry_skill_dirs[0], rel_members

    found = ", ".join(capelry_skill_dirs) if capelry_skill_dirs else "none"
    expected = ", ".join(candidates)
    raise SystemExit(f"Could not find the Capelry skill in the GitHub archive. Tried: {expected}. Found: {found}")


def prepare_dest(dest: Path, replace: bool) -> None:
    if dest.exists():
        if not replace:
            raise SystemExit(f"Destination already exists: {dest}")
        shutil.rmtree(dest)
    dest.mkdir(parents=True, exist_ok=True)


def install_source_path(
    zf: zipfile.ZipFile,
    rel_members: dict[str, zipfile.ZipInfo],
    source_path: str,
    dest: Path,
    replace: bool,
) -> None:
    prepare_dest(dest, replace)
    prefix = f"{source_path}/"
    for rel, member in rel_members.items():
        if not rel.startswith(prefix):
            continue
        output_rel = rel[len(prefix) :]
        if not output_rel:
            continue
        output = dest / output_rel
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(zf.read(member))

    if not (dest / "SKILL.md").exists():
        shutil.rmtree(dest, ignore_errors=True)
        raise SystemExit("Bootstrap completed but did not produce SKILL.md")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Install the Capelry skill from GitHub source")
    parser.add_argument(
        "--repo",
        "--repository",
        dest="repository",
        default=os.environ.get("CAPELRY_BOOTSTRAP_REPOSITORY", DEFAULT_SOURCE_REPOSITORY),
        help=f"GitHub source repository (default: {DEFAULT_SOURCE_REPOSITORY} or CAPELRY_BOOTSTRAP_REPOSITORY)",
    )
    parser.add_argument(
        "--ref",
        default=os.environ.get("CAPELRY_BOOTSTRAP_REF", DEFAULT_SOURCE_REF),
        help=f"Git ref, branch, tag, or SHA to download (default: {DEFAULT_SOURCE_REF} or CAPELRY_BOOTSTRAP_REF)",
    )
    parser.add_argument(
        "--source-path",
        default=os.environ.get("CAPELRY_BOOTSTRAP_PATH"),
        help="Skill path inside the repository. By default, tries skills/capelry then .pi/skills/capelry.",
    )
    parser.add_argument(
        "--target",
        default=os.environ.get("CAPELRY_BOOTSTRAP_TARGET"),
        choices=sorted(TARGET_SKILLS_DIRS),
        help="Known install target. If omitted, uses --skills-dir or CAPELRY_SKILLS_DIR; default is agents-project.",
    )
    parser.add_argument(
        "--skills-dir",
        default=os.environ.get("CAPELRY_SKILLS_DIR", DEFAULT_SKILLS_DIR),
        help=f"Parent skills directory (default: {DEFAULT_SKILLS_DIR} or CAPELRY_SKILLS_DIR)",
    )
    parser.add_argument(
        "--name",
        default=os.environ.get("CAPELRY_BOOTSTRAP_NAME", DEFAULT_SKILL_NAME),
        help=f"Install directory name under --skills-dir (default: {DEFAULT_SKILL_NAME})",
    )
    parser.add_argument("--dest", help="Exact destination directory; overrides --skills-dir/name")
    parser.add_argument(
        "--no-replace",
        action="store_true",
        help="Fail instead of replacing an existing destination",
    )
    # Backwards-compatible no-op options from older registry-based bootstrap docs.
    parser.add_argument("--registry", help=argparse.SUPPRESS)
    parser.add_argument("--package", help=argparse.SUPPRESS)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.registry or args.package:
        eprint("Note: --registry and --package are ignored; Capelry bootstraps from GitHub source.")

    repository = args.repository.rstrip("/")
    ref = args.ref
    source_candidates = candidate_source_paths(args.source_path)
    if args.target and args.target not in TARGET_SKILLS_DIRS:
        choices = ", ".join(sorted(TARGET_SKILLS_DIRS))
        raise SystemExit(f"Unknown CAPELRY_BOOTSTRAP_TARGET: {args.target}. Expected one of: {choices}")
    skills_dir = TARGET_SKILLS_DIRS[args.target] if args.target else args.skills_dir
    dest = Path(args.dest).expanduser() if args.dest else Path(skills_dir).expanduser() / args.name

    archive_url = github_archive_url(repository, ref)
    print(f"Fetching Capelry skill source from {repository}@{ref}...")
    archive = fetch_bytes(archive_url)

    with zipfile.ZipFile(io.BytesIO(archive)) as zf:
        source_path, rel_members = find_skill_source(zf, source_candidates)
        install_source_path(zf, rel_members, source_path, dest, replace=not args.no_replace)

    print(f"Installed Capelry skill from {repository}@{ref}:{source_path} to {dest}")
    print("Next: reload or restart your agent. In Pi, run /reload then /skill:capelry.")
    print(f"Try: python3 {dest / 'scripts' / 'capelry.py'} search skill")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

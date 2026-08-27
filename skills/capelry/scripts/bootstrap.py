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
import tempfile
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
DEFAULT_HTTP_USER_AGENT = "capelry-client bootstrap"

TARGET_SKILLS_DIRS = {
    "agents-project": ".agents/skills",
    "agents-global": "~/.agents/skills",
    "pi-project": ".pi/skills",
    "pi-global": "~/.pi/agent/skills",
    "claude-project": ".claude/skills",
    "claude-global": "~/.claude/skills",
    "codex-project": ".agents/skills",
    "codex-global": "~/.agents/skills",
    "opencode-project": ".opencode/skills",
    "opencode-global": "~/.config/opencode/skills",
    "gemini-project": ".gemini/skills",
    "gemini-global": "~/.gemini/skills",
    "cursor-project": ".cursor/skills",
    "cursor-global": "~/.cursor/skills",
    "windsurf-project": ".windsurf/skills",
    "windsurf-global": "~/.codeium/windsurf/skills",
    "copilot-project": ".github/skills",
    "copilot-global": "~/.copilot/skills",
    "cline-project": ".cline/skills",
    "cline-global": "~/.cline/skills",
    "roo-project": ".roo/skills",
    "roo-global": "~/.roo/skills",
    "junie-project": ".junie/skills",
    "junie-global": "~/.junie/skills",
    "kiro-project": ".kiro/skills",
    "kiro-global": "~/.kiro/skills",
    "factory-project": ".factory/skills",
    "factory-global": "~/.factory/skills",
}

TARGET_NEXT_STEPS = {
    "agents": "Reload or restart the active harness, then confirm {name} appears in its skills list.",
    "pi": "In Pi, run /reload and then /skill:{name}.",
    "claude": "In Claude Code, invoke /{name}; restart only if the skills directory was created after startup.",
    "codex": "Codex detects skill changes automatically; use /skills or ${name}, and restart only if it is absent.",
    "opencode": "Restart OpenCode if needed, then confirm its skill tool lists {name} and permissions allow it.",
    "gemini": "In Gemini CLI, run /skills reload and then /skills list; activation asks for consent.",
    "cursor": "In Cursor, open Customize > Skills or invoke /{name} in Agent chat.",
    "windsurf": "In Cascade, invoke @{name}; reopen Cascade if the skill is not listed.",
    "copilot": "In Copilot CLI, run /skills reload and /skills info {name}.",
    "cline": "In Cline, confirm {name} is enabled in the Skills menu or invoke /{name}.",
    "roo": "Roo watches SKILL.md changes; confirm {name} is available in the current mode.",
    "junie": "In Junie, invoke /{name} or ${name}; restart the session if it is not suggested.",
    "kiro": "Restart the Kiro agent if needed and invoke /{name}; custom agents must include the skill:// resource.",
    "factory": "Start a new Droid session if needed, then invoke /{name}.",
}

SKILL_NAME_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
YAML_NON_STRING_PLAIN_PATTERN = re.compile(
    r"^[+-]?(?:[0-9][0-9_]*(?:\.[0-9_]*)?(?:[eE][+-]?[0-9_]+)?|"
    r"0[xX][0-9a-fA-F_]+|0[oO][0-7_]+|0[bB][01_]+|\.(?:inf|nan)|"
    r"[0-9]{4}-[0-9]{2}-[0-9]{2}(?:[Tt ].*)?)$",
    re.IGNORECASE,
)


def eprint(*parts: object) -> None:
    print(*parts, file=sys.stderr)


def normalize_header_value(value: str) -> str:
    return " ".join(value.strip().split())


def capelry_user_agent(default: str = DEFAULT_HTTP_USER_AGENT) -> str:
    override = normalize_header_value(os.environ.get("CAPELRY_USER_AGENT", ""))
    if override:
        return override
    suffix = normalize_header_value(os.environ.get("CAPELRY_USER_AGENT_SUFFIX", ""))
    if suffix:
        return f"{default} {suffix}"
    return default


def fetch_bytes(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": capelry_user_agent()})
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


def normalized_archive_path(filename: str) -> PurePosixPath:
    normalized = filename.replace("\\", "/")
    path = PurePosixPath(normalized)
    if (
        "\x00" in normalized
        or path.is_absolute()
        or ".." in path.parts
        or (path.parts and path.parts[0].endswith(":"))
    ):
        raise SystemExit(f"Unsafe archive path: {filename}")
    return path


def safe_file_members(zf: zipfile.ZipFile) -> Iterable[zipfile.ZipInfo]:
    for member in zf.infolist():
        if member.is_dir():
            continue
        normalized_archive_path(member.filename)
        yield member


def archive_member_rel(member: zipfile.ZipInfo) -> str:
    """Return a member path relative to the GitHub archive root directory."""
    parts = normalized_archive_path(member.filename).parts
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


def path_exists(path: Path) -> bool:
    return path.exists() or path.is_symlink()


def remove_path(path: Path) -> None:
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
    else:
        path.unlink(missing_ok=True)


def yaml_scalar(value: str) -> str:
    value = value.strip()
    quoted = len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}
    if not quoted and " #" in value:
        value = value.split(" #", 1)[0].rstrip()
        quoted = len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}
    if quoted:
        inner = value[1:-1]
        return inner.replace("''", "'").strip() if value.startswith("'") else inner.strip()
    return value.strip()


def frontmatter_scalar(lines: list[str], key: str) -> str | None:
    pattern = re.compile(rf"^{re.escape(key)}:\s*(?P<value>.*)$")
    for index, line in enumerate(lines):
        match = pattern.match(line)
        if not match:
            continue
        value = match.group("value").strip()
        continuation: list[str] = []
        for following in lines[index + 1 :]:
            if following and not following.startswith((" ", "\t")):
                break
            if following.strip() and not following.lstrip().startswith("#"):
                continuation.append(following.strip())
        if value and not re.fullmatch(r"[>|][+-]?", value):
            if continuation:
                raise SystemExit(
                    f"Installed SKILL.md field '{key}' cannot continue a non-block scalar; "
                    "use | or > for multiline values"
                )
            quoted = len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}
            if quoted and value.startswith("'") and "'" in value[1:-1].replace("''", ""):
                raise SystemExit(
                    f"Installed SKILL.md field '{key}' contains an unescaped apostrophe in a "
                    "single-quoted YAML scalar; escape it as ''"
                )
            if (value.startswith(("'", '"')) or value.endswith(("'", '"'))) and not quoted:
                raise SystemExit(f"Installed SKILL.md field '{key}' must be a valid YAML string")
            if not quoted and (
                value.startswith(("[", "{"))
                or value.casefold() in {"null", "true", "false", "yes", "no", "on", "off", "y", "n", "~"}
                or YAML_NON_STRING_PLAIN_PATTERN.fullmatch(value)
                or re.search(r":\s", value)
            ):
                raise SystemExit(f"Installed SKILL.md field '{key}' must be a YAML string")
            return yaml_scalar(value)
        if not continuation:
            return ""
        return ("\n" if value.startswith("|") else " ").join(continuation).strip()
    return None


def validate_skill_directory(skill_dir: Path, expected_name: str) -> dict[str, str | int]:
    skill_file = skill_dir / "SKILL.md"
    try:
        text = skill_file.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        raise SystemExit(f"Installed skill has no readable UTF-8 SKILL.md: {error}") from error
    lines = text.lstrip("\ufeff").splitlines()
    if not lines or lines[0].strip() != "---":
        raise SystemExit("Installed SKILL.md must start with YAML frontmatter delimited by ---")
    try:
        closing = next(index for index, line in enumerate(lines[1:], start=1) if line.strip() == "---")
    except StopIteration as error:
        raise SystemExit("Installed SKILL.md frontmatter is missing its closing --- delimiter") from error
    frontmatter = lines[1:closing]
    name = frontmatter_scalar(frontmatter, "name")
    description = frontmatter_scalar(frontmatter, "description")
    if not name or len(name) > 64 or not SKILL_NAME_PATTERN.fullmatch(name):
        raise SystemExit("Installed SKILL.md name must be 1-64 lowercase letters, numbers, or single hyphens")
    if name != expected_name:
        raise SystemExit(f"Installed SKILL.md name '{name}' must match destination directory '{expected_name}'")
    if not description or len(description) > 1024:
        raise SystemExit("Installed SKILL.md description must contain 1-1024 characters")
    return {"name": name, "descriptionLength": len(description)}


def replace_directory(dest: Path, candidate: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    old_parent = Path(tempfile.mkdtemp(prefix=f".{dest.name}.old-", dir=str(dest.parent)))
    old = old_parent / dest.name
    had_old = path_exists(dest)
    preserve_old_temp = False
    if had_old:
        shutil.move(str(dest), str(old))
    try:
        shutil.move(str(candidate), str(dest))
    except BaseException:
        try:
            if path_exists(dest):
                remove_path(dest)
            if had_old and path_exists(old):
                shutil.move(str(old), str(dest))
        except BaseException as rollback_error:
            preserve_old_temp = path_exists(old)
            location = str(old) if preserve_old_temp else "unavailable"
            raise RuntimeError(
                f"Bootstrap replacement and rollback both failed; the previous install is preserved at {location}"
            ) from rollback_error
        raise
    finally:
        if not preserve_old_temp:
            shutil.rmtree(old_parent, ignore_errors=True)


def install_source_path(
    zf: zipfile.ZipFile,
    rel_members: dict[str, zipfile.ZipInfo],
    source_path: str,
    dest: Path,
    replace: bool,
) -> dict[str, str | int]:
    if path_exists(dest) and not replace:
        raise SystemExit(f"Destination already exists: {dest}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=f".{dest.name}.install-", dir=str(dest.parent)) as temp_root:
        candidate = Path(temp_root) / dest.name
        candidate.mkdir()
        prefix = f"{source_path}/"
        for rel, member in rel_members.items():
            if not rel.startswith(prefix):
                continue
            output_rel = rel[len(prefix) :]
            if not output_rel:
                continue
            output = candidate / output_rel
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_bytes(zf.read(member))

        validation = validate_skill_directory(candidate, dest.name)
        replace_directory(dest, candidate)
        return validation


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
        help=f"Install directory name under --skills-dir; must match SKILL.md (default: {DEFAULT_SKILL_NAME})",
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
    if dest.name != DEFAULT_SKILL_NAME:
        raise SystemExit("Capelry must be installed in a directory named 'capelry' for cross-harness compatibility")

    archive_url = github_archive_url(repository, ref)
    print(f"Fetching Capelry skill source from {repository}@{ref}...")
    archive = fetch_bytes(archive_url)

    with zipfile.ZipFile(io.BytesIO(archive)) as zf:
        source_path, rel_members = find_skill_source(zf, source_candidates)
        validation = install_source_path(zf, rel_members, source_path, dest, replace=not args.no_replace)

    print(f"Installed Capelry skill from {repository}@{ref}:{source_path} to {dest}")
    print(f"Validated Agent Skills metadata: {validation['name']} ({validation['descriptionLength']} description characters)")
    target_family = args.target.split("-", 1)[0] if args.target else "agents"
    next_step = TARGET_NEXT_STEPS.get(target_family, TARGET_NEXT_STEPS["agents"]).format(name=validation["name"])
    print(f"Next: {next_step}")
    print(f"Try: python3 {dest / 'scripts' / 'capelry.py'} search skill")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

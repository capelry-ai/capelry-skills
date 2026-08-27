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
from pathlib import Path, PurePosixPath, PureWindowsPath
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
    r"^[+-]?(?:[0-9][0-9_]*(?::[0-5]?[0-9])+(?:\.[0-9_]*)?|"
    r"[0-9][0-9_]*(?:\.[0-9_]*)?(?:[eE][+-]?[0-9_]+)?|"
    r"0[xX][0-9a-fA-F_]+|0[oO][0-7_]+|0[bB][01_]+|\.(?:[0-9_]+(?:[eE][+-]?[0-9_]+)?|inf|nan)|"
    r"[0-9]{4}-[0-9]{2}-[0-9]{2}(?:[Tt ].*)?)$",
    re.IGNORECASE,
)
YAML_BLOCK_SCALAR_PATTERN = re.compile(r"^[>|](?:(?:[1-9][+-]?)|(?:[+-][1-9]?))?$")
YAML_FORBIDDEN_PLAIN_PREFIXES = ("@", "`", "!", "&", "*", "#", "%", ",", "[", "]", "{", "}", "|", ">")


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
        or any(PureWindowsPath(part).drive for part in path.parts)
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


def is_yaml_block_scalar(value: str) -> bool:
    return bool(YAML_BLOCK_SCALAR_PATTERN.fullmatch(strip_yaml_inline_comment(value)))


def yaml_block_scalar_indent(value: str) -> int | None:
    match = re.search(r"[1-9]", strip_yaml_inline_comment(value))
    return int(match.group()) if match else None


def yaml_plain_scalar_has_forbidden_prefix(value: str) -> bool:
    if value.startswith(YAML_FORBIDDEN_PLAIN_PREFIXES):
        return True
    return bool(re.match(r"^[-?:](?:\s|$)", value))


def strip_yaml_inline_comment(value: str) -> str:
    value = value.strip()
    quote: str | None = None
    index = 0
    while index < len(value):
        char = value[index]
        if quote == "'":
            if char == "'" and index + 1 < len(value) and value[index + 1] == "'":
                index += 2
                continue
            if char == "'":
                quote = None
        elif quote == '"':
            if char == "\\" and index + 1 < len(value):
                index += 2
                continue
            if char == '"':
                quote = None
        elif index == 0 and char in {"'", '"'}:
            quote = char
        elif char == "#" and (index == 0 or value[index - 1] in {" ", "\t"}):
            return value[:index].rstrip(" \t")
        index += 1
    return value


def parse_yaml_double_quoted(value: str) -> str:
    escapes = {
        "0": "\0",
        "a": "\a",
        "b": "\b",
        "t": "\t",
        "n": "\n",
        "v": "\v",
        "f": "\f",
        "r": "\r",
        "e": "\x1b",
        " ": " ",
        '"': '"',
        "/": "/",
        "\\": "\\",
        "N": "\x85",
        "_": "\xa0",
        "L": "\u2028",
        "P": "\u2029",
    }
    inner = value[1:-1]
    result: list[str] = []
    index = 0
    while index < len(inner):
        char = inner[index]
        if char == '"':
            raise ValueError("contains an unescaped double quote")
        if char != "\\":
            result.append(char)
            index += 1
            continue
        index += 1
        if index >= len(inner):
            raise ValueError("ends with an incomplete escape")
        escape = inner[index]
        if escape in escapes:
            result.append(escapes[escape])
            index += 1
            continue
        if escape not in "xuU":
            raise ValueError(f"contains unsupported escape \\{escape}")
        width = {"x": 2, "u": 4, "U": 8}[escape]
        digits = inner[index + 1 : index + 1 + width]
        if len(digits) != width or not all(char in "0123456789abcdefABCDEF" for char in digits):
            raise ValueError(f"contains an invalid \\{escape} escape")
        codepoint = int(digits, 16)
        if codepoint > 0x10FFFF or 0xD800 <= codepoint <= 0xDFFF:
            raise ValueError(f"contains an invalid Unicode code point in \\{escape}")
        result.append(chr(codepoint))
        index += width + 1
    return "".join(result)


def valid_yaml_double_quoted(value: str) -> bool:
    try:
        parse_yaml_double_quoted(value)
    except ValueError:
        return False
    return True


def split_yaml_mapping_entry(value: str) -> tuple[str, str] | None:
    quote: str | None = None
    index = 0
    while index < len(value):
        char = value[index]
        if quote == "'":
            if char == "'" and index + 1 < len(value) and value[index + 1] == "'":
                index += 2
                continue
            if char == "'":
                quote = None
        elif quote == '"':
            if char == "\\" and index + 1 < len(value):
                index += 2
                continue
            if char == '"':
                quote = None
        elif char in {"'", '"'} and not value[:index].strip():
            quote = char
        elif char == ":" and (index + 1 == len(value) or value[index + 1].isspace()):
            key = value[:index].strip()
            item_value = value[index + 1 :].strip()
            return (key, item_value) if key and item_value else None
        index += 1
    return None


def yaml_scalar(value: str) -> str:
    value = strip_yaml_inline_comment(value)
    if len(value) >= 2 and value[0] == value[-1] == "'":
        return value[1:-1].replace("''", "'")
    if len(value) >= 2 and value[0] == value[-1] == '"':
        return parse_yaml_double_quoted(value)
    return value


def render_yaml_block_scalar(marker: str, continuation: list[str]) -> str:
    marker = strip_yaml_inline_comment(marker)
    nonblank = [line for line in continuation if line.strip()]
    explicit = yaml_block_scalar_indent(marker)
    required = explicit or (len(nonblank[0]) - len(nonblank[0].lstrip()) if nonblank else 0)
    content = [line[required:] if line.strip() else "" for line in continuation]
    trailing_blank = 0
    while content and not content[-1]:
        trailing_blank += 1
        content.pop()
    separator = "\n" if marker.startswith("|") else " "
    rendered = separator.join(content)
    if content:
        rendered += "\n" * (trailing_blank + 1)
    elif continuation:
        rendered = "\n" * len(continuation)
    if "-" in marker:
        return rendered.rstrip("\n")
    if "+" in marker:
        return rendered
    clipped = rendered.rstrip("\n")
    return f"{clipped}\n" if clipped else ""


def validate_frontmatter_structure(lines: list[str]) -> None:
    field_pattern = re.compile(r"^(?P<key>[A-Za-z0-9_-]+):(?:[ \t]+(?P<value>.*))?$")
    seen: set[str] = set()
    current_key: str | None = None
    current_value = ""
    block_indent: int | None = None
    for line_number, line in enumerate(lines, start=2):
        if not line.strip():
            continue
        if line.lstrip().startswith("#"):
            if not line.startswith((" ", "\t")) or not is_yaml_block_scalar(current_value):
                continue
            indent = len(line) - len(line.lstrip(" \t"))
            if block_indent is not None and indent < block_indent:
                continue
        if line.startswith((" ", "\t")):
            if current_key is None:
                raise SystemExit(f"Installed SKILL.md frontmatter line {line_number} is indented without a field")
            if current_key != "metadata" and not is_yaml_block_scalar(current_value):
                if not current_value:
                    raise SystemExit(f"Installed SKILL.md field '{current_key}' must be a string, not a sequence or mapping")
                raise SystemExit(
                    f"Installed SKILL.md field '{current_key}' cannot continue a non-block scalar; "
                    "use | or > for multiline values"
                )
            if is_yaml_block_scalar(current_value):
                prefix = line[: len(line) - len(line.lstrip(" \t"))]
                if "\t" in prefix:
                    raise SystemExit(
                        f"Installed SKILL.md block scalar field '{current_key}' must use spaces, not tabs, "
                        "for indentation"
                    )
                indent = len(prefix)
                if block_indent is None:
                    block_indent = indent
                elif indent < block_indent:
                    raise SystemExit(
                        f"Installed SKILL.md block scalar field '{current_key}' must use at least "
                        f"{block_indent} spaces established by its first content line"
                    )
            continue
        match = field_pattern.match(line)
        if not match:
            raise SystemExit(f"Installed SKILL.md frontmatter line {line_number} is not a top-level YAML field")
        key = match.group("key")
        if key in seen:
            raise SystemExit(f"Installed SKILL.md frontmatter field '{key}' is declared more than once")
        seen.add(key)
        current_key = key
        current_value = (match.group("value") or "").strip()
        block_indent = yaml_block_scalar_indent(current_value) if is_yaml_block_scalar(current_value) else None


def frontmatter_scalar(lines: list[str], key: str) -> str | None:
    pattern = re.compile(rf"^{re.escape(key)}:\s*(?P<value>.*)$")
    for index, line in enumerate(lines):
        match = pattern.match(line)
        if not match:
            continue
        value = strip_yaml_inline_comment(match.group("value"))
        continuation: list[str] = []
        for following in lines[index + 1 :]:
            if following and not following.startswith((" ", "\t")):
                break
            if is_yaml_block_scalar(value):
                if following.lstrip().startswith("#"):
                    nonblank = [item for item in continuation if item.strip()]
                    required = yaml_block_scalar_indent(value) or (
                        len(nonblank[0]) - len(nonblank[0].lstrip(" \t")) if nonblank else None
                    )
                    indent = len(following) - len(following.lstrip(" \t"))
                    if required is not None and indent < required:
                        continue
                continuation.append(following)
            elif following.strip() and not following.lstrip().startswith("#"):
                continuation.append(following)
        if value and not is_yaml_block_scalar(value):
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
            if quoted and value.startswith('"') and not valid_yaml_double_quoted(value):
                raise SystemExit(f"Installed SKILL.md field '{key}' must be a valid double-quoted YAML string")
            if (value.startswith(("'", '"')) or value.endswith(("'", '"'))) and not quoted:
                raise SystemExit(f"Installed SKILL.md field '{key}' must be a valid YAML string")
            if not quoted and (
                yaml_plain_scalar_has_forbidden_prefix(value)
                or value.casefold() in {"null", "true", "false", "yes", "no", "on", "off", "y", "n", "~"}
                or YAML_NON_STRING_PLAIN_PATTERN.fullmatch(value)
                or re.search(r":(?:\s|$)", value)
            ):
                raise SystemExit(f"Installed SKILL.md field '{key}' must be a YAML string")
            return yaml_scalar(value)
        if not continuation:
            if not value:
                raise SystemExit(
                    f"Installed SKILL.md field '{key}' must be a YAML string scalar; quote an empty string explicitly"
                )
            return ""
        if not value and any(line.startswith("- ") or re.match(r"^[^:#]+:\s", line) for line in continuation):
            raise SystemExit(f"Installed SKILL.md field '{key}' must be a string, not a sequence or mapping")
        return render_yaml_block_scalar(value, continuation)
    return None


def validate_metadata_mapping(lines: list[str]) -> None:
    pattern = re.compile(r"^metadata:\s*(?P<value>.*)$")
    for index, line in enumerate(lines):
        match = pattern.match(line)
        if not match:
            continue
        if match.group("value").strip():
            raise SystemExit("Installed SKILL.md metadata must use an indented string-to-string mapping")
        entries: list[str] = []
        for following in lines[index + 1 :]:
            if following and not following.startswith((" ", "\t")):
                break
            if following.strip() and not following.lstrip().startswith("#"):
                entries.append(following)
        if not entries:
            raise SystemExit("Installed SKILL.md metadata must contain at least one string key/value entry")
        entry_indent: int | None = None
        seen: set[str] = set()
        for entry in entries:
            stripped = entry.strip()
            prefix = entry[: len(entry) - len(entry.lstrip(" \t"))]
            if stripped.startswith("- "):
                raise SystemExit("Installed SKILL.md metadata must be a mapping, not a sequence")
            if "\t" in prefix:
                raise SystemExit("Installed SKILL.md metadata entries must use spaces, not tabs")
            indent = len(prefix)
            if entry_indent is None:
                entry_indent = indent
            elif indent != entry_indent:
                raise SystemExit("Installed SKILL.md metadata must be a flat mapping with consistent indentation")
            item = split_yaml_mapping_entry(stripped)
            if item is None:
                raise SystemExit("Installed SKILL.md metadata must contain string key/value entries")
            key, item_value = item
            value = strip_yaml_inline_comment(item_value)
            if not value:
                raise SystemExit(f"Installed SKILL.md metadata value for '{key}' must be a YAML string scalar")
            key_quoted = len(key) >= 2 and key[0] == key[-1] and key[0] in {"'", '"'}
            invalid_key_single = key_quoted and key.startswith("'") and "'" in key[1:-1].replace("''", "")
            invalid_key_double = False
            if key_quoted and key.startswith('"'):
                invalid_key_double = not valid_yaml_double_quoted(key)
            invalid_key_plain = not key_quoted and (
                yaml_plain_scalar_has_forbidden_prefix(key)
                or key.casefold() in {"null", "true", "false", "yes", "no", "on", "off", "y", "n", "~"}
                or YAML_NON_STRING_PLAIN_PATTERN.fullmatch(key)
            )
            mismatched_key_quote = (key.startswith(("'", '"')) or key.endswith(("'", '"'))) and not key_quoted
            if invalid_key_single or invalid_key_double or invalid_key_plain or mismatched_key_quote:
                raise SystemExit(f"Installed SKILL.md metadata key '{key}' must be a YAML string scalar")
            try:
                resolved_key = yaml_scalar(key)
            except ValueError as error:
                raise SystemExit(f"Installed SKILL.md metadata key '{key}' must be a YAML string scalar") from error
            if resolved_key in seen:
                raise SystemExit(f"Installed SKILL.md metadata key '{resolved_key}' is declared more than once")
            seen.add(resolved_key)
            quoted = len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}
            invalid_single_quote = quoted and value.startswith("'") and "'" in value[1:-1].replace("''", "")
            invalid_double_quote = False
            if quoted and value.startswith('"'):
                invalid_double_quote = not valid_yaml_double_quoted(value)
            invalid_plain = not quoted and (
                yaml_plain_scalar_has_forbidden_prefix(value)
                or value.casefold() in {"null", "true", "false", "yes", "no", "on", "off", "y", "n", "~"}
                or YAML_NON_STRING_PLAIN_PATTERN.fullmatch(value)
                or re.search(r":(?:\s|$)", value)
            )
            mismatched_quote = (value.startswith(("'", '"')) or value.endswith(("'", '"'))) and not quoted
            if invalid_single_quote or invalid_double_quote or invalid_plain or mismatched_quote:
                raise SystemExit(f"Installed SKILL.md metadata value for '{key}' must be a YAML string scalar")
        return


def validate_skill_directory(skill_dir: Path, expected_name: str) -> dict[str, str | int]:
    skill_file = skill_dir / "SKILL.md"
    try:
        text = skill_file.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        raise SystemExit(f"Installed skill has no readable UTF-8 SKILL.md: {error}") from error
    clean_text = text[1:] if text.startswith("\ufeff") else text
    if re.search(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x84\x86-\x9f\ufffe\uffff]", clean_text):
        raise SystemExit("Installed SKILL.md contains YAML-forbidden control characters")
    lines = (
        clean_text.replace("\r\n", "\n")
        .replace("\r", "\n")
        .replace("\x85", "\n")
        .replace("\u2028", "\n")
        .replace("\u2029", "\n")
        .split("\n")
    )
    if not lines or lines[0] != "---":
        raise SystemExit("Installed SKILL.md must start with YAML frontmatter delimited by ---")
    try:
        closing = next(index for index, line in enumerate(lines[1:], start=1) if line == "---")
    except StopIteration as error:
        raise SystemExit("Installed SKILL.md frontmatter is missing its closing --- delimiter") from error
    frontmatter = lines[1:closing]
    validate_frontmatter_structure(frontmatter)
    name = frontmatter_scalar(frontmatter, "name")
    description = frontmatter_scalar(frontmatter, "description")
    frontmatter_scalar(frontmatter, "license")
    compatibility = frontmatter_scalar(frontmatter, "compatibility")
    frontmatter_scalar(frontmatter, "allowed-tools")
    validate_metadata_mapping(frontmatter)
    if not name or len(name) > 64 or not SKILL_NAME_PATTERN.fullmatch(name):
        raise SystemExit("Installed SKILL.md name must be 1-64 lowercase letters, numbers, or single hyphens")
    if name != expected_name:
        raise SystemExit(f"Installed SKILL.md name '{name}' must match destination directory '{expected_name}'")
    if not description or len(description) > 1024:
        raise SystemExit("Installed SKILL.md description must contain 1-1024 characters")
    if compatibility is not None and (not compatibility or len(compatibility) > 500):
        raise SystemExit("Installed SKILL.md compatibility must contain 1-500 characters when provided")
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

#!/usr/bin/env python3
"""Small stdlib-only client for the Capelry capability registry."""

from __future__ import annotations

import argparse
import io
import json
import os
import re
import shlex
import shutil
import sys
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path
from typing import Any

DEFAULT_REGISTRY = "https://capelry.com"
API_SEARCH_LIMIT_MIN = 1
API_SEARCH_LIMIT_MAX = 100

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

STOP_WORDS = {
    "a",
    "an",
    "and",
    "as",
    "for",
    "in",
    "into",
    "of",
    "on",
    "or",
    "the",
    "to",
    "with",
    "capability",
    "capabilities",
    "skill",
    "skills",
}

PRODUCTION_READINESS_QUERIES = (
    "devops rollout",
    "deployment preflight",
    "hardening docker",
    "container image hardening",
    "rbac hardening",
    "backup integrity",
    "observability",
    "SRE",
    "incident response",
    "preflight",
    "rollout",
    "hardening",
    "production",
    "readiness",
)

FEATURE_PLANNING_QUERIES = (
    "feature planning",
    "feature",
    "prd",
    "product requirements document",
    "implementation plan",
    "specification",
    "roadmap",
)

TERM_EXPANSIONS = {
    "backup": ("backup integrity", "recovery", "ransomware backup"),
    "container": ("container image hardening", "docker", "trivy"),
    "containers": ("container image hardening", "docker", "trivy"),
    "deploy": ("deployment", "preflight", "rollout"),
    "deployment": ("preflight", "rollout", "release plan"),
    "devops": ("rollout", "preflight", "SRE"),
    "docker": ("hardening docker", "container image hardening", "docker bench security", "trivy"),
    "feature": FEATURE_PLANNING_QUERIES,
    "features": FEATURE_PLANNING_QUERIES,
    "hardening": ("container image hardening", "hardening docker", "rbac hardening", "kubernetes"),
    "incident": ("incident response", "incident response playbook"),
    "k8s": ("kubernetes", "rbac hardening", "platform sre kubernetes"),
    "kubernetes": ("k8s", "rbac hardening", "platform sre kubernetes", "azure kubernetes readiness"),
    "observability": ("monitoring", "SRE"),
    "planning": FEATURE_PLANNING_QUERIES,
    "prd": FEATURE_PLANNING_QUERIES,
    "prod": PRODUCTION_READINESS_QUERIES,
    "production": PRODUCTION_READINESS_QUERIES,
    "readiness": PRODUCTION_READINESS_QUERIES,
    "recovery": ("backup", "backup integrity", "incident response"),
    "release": ("rollout", "deployment", "preflight"),
    "rollout": ("devops rollout", "release plan", "deployment"),
    "security": ("hardening", "trivy", "rbac hardening"),
    "sre": ("SRE", "observability", "kubernetes", "incident response"),
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


def post_json(url: str, payload: dict[str, Any]) -> Any:
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        headers={
            "User-Agent": "capelry-skill/0.1",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        body_text = error.read().decode("utf-8", errors="replace")
        raise SystemExit(f"HTTP {error.code} for {url}\n{body_text}") from error
    except urllib.error.URLError as error:
        raise SystemExit(f"Unable to reach {url}: {error.reason}") from error


def print_json(payload: Any) -> None:
    print(json.dumps(payload, indent=2, ensure_ascii=False))


def parse_ref(value: str) -> tuple[str, str, str | None]:
    ref, _, version = value.partition("@")
    if "/" not in ref:
        raise SystemExit("Capability ref must be namespace/name, optionally namespace/name@version")
    namespace, name = ref.split("/", 1)
    if not namespace or not name:
        raise SystemExit("Capability ref must be namespace/name")
    return namespace, name, version or None


def capability_ref(capability: dict[str, Any]) -> str:
    return f"{capability.get('namespace')}/{capability.get('name')}"


def capability_version(capability: dict[str, Any]) -> str:
    latest = capability.get("latestVersion") or {}
    version = latest.get("version")
    return version if isinstance(version, str) and version else "?"


def capability_status(capability: dict[str, Any]) -> str:
    latest = capability.get("latestVersion") or {}
    status = latest.get("validationStatus")
    return status if isinstance(status, str) and status else "?"


def capability_type(capability: dict[str, Any]) -> str:
    package_type = capability.get("packageType")
    return package_type if isinstance(package_type, str) and package_type else "capability"


def source_repository(capability: dict[str, Any]) -> str:
    source = capability.get("source") or {}
    repository = source.get("repository")
    return repository if isinstance(repository, str) else ""


def source_path(capability: dict[str, Any]) -> str:
    source = capability.get("source") or {}
    path = source.get("path")
    return path if isinstance(path, str) else ""


def github_slug_from_repository(repository: str) -> str:
    match = re.search(r"github\.com[:/](?P<owner>[^/]+)/(?P<repo>[^/]+?)(?:\.git)?/?$", repository)
    if not match:
        return ""
    return f"{match.group('owner')}/{match.group('repo')}"


def source_slug(capability: dict[str, Any]) -> str:
    repository = source_repository(capability)
    return github_slug_from_repository(repository) or repository


def capability_detail(base: str, ref: str) -> dict[str, Any]:
    namespace, name, _ = parse_ref(ref)
    return fetch_json(api_url(base, f"/api/capabilities/{namespace}/{name}"))["capability"]


def latest_version(capability: dict[str, Any]) -> str:
    latest = capability.get("latestVersion") or {}
    version = latest.get("version")
    if not isinstance(version, str) or not version:
        raise SystemExit("Capability has no latest version")
    return version


def clamp_api_search_limit(value: int | None) -> int | None:
    if value is None:
        return None
    return min(max(value, API_SEARCH_LIMIT_MIN), API_SEARCH_LIMIT_MAX)


def result_limit(value: int) -> int:
    return max(value, API_SEARCH_LIMIT_MIN)


def search_capabilities(
    base: str,
    query: str,
    *,
    package_type: str | None = None,
    status: str | None = None,
    domain: str | None = None,
    phase: str | None = None,
    source: str | None = None,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    params: dict[str, str] = {"q": query}
    if package_type:
        params["type"] = package_type
    if status:
        params["validation"] = status
    if domain:
        params["domain"] = domain
    if phase:
        params["phase"] = phase
    if source:
        params["source"] = source
    clamped_limit = clamp_api_search_limit(limit)
    if clamped_limit is not None:
        params["limit"] = str(clamped_limit)
    encoded = urllib.parse.urlencode(params)
    payload = fetch_json(api_url(base, f"/api/capabilities?{encoded}"))
    capabilities = payload.get("capabilities", [])
    return capabilities if isinstance(capabilities, list) else []


def tokenize(value: str) -> list[str]:
    return [token for token in re.findall(r"[a-z0-9]+", value.lower()) if token not in STOP_WORDS]


def dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        normalized = re.sub(r"\s+", " ", value.strip())
        key = normalized.lower()
        if normalized and key not in seen:
            seen.add(key)
            result.append(normalized)
    return result


def expanded_queries(query: str) -> list[str]:
    """Return a bounded set of related search queries for agent discovery."""
    seeds = [query]
    tokens = tokenize(query)
    lower = query.lower()

    if "production readiness" in lower or {"production", "readiness"}.issubset(set(tokens)):
        seeds.extend(PRODUCTION_READINESS_QUERIES)
    if "feature planning" in lower or {"feature", "planning"}.issubset(set(tokens)):
        seeds.extend(FEATURE_PLANNING_QUERIES)

    for token in tokens:
        seeds.extend(TERM_EXPANSIONS.get(token, ()))
        if len(token) > 2:
            seeds.append(token)

    # Keep network use predictable while still covering common adjacent terms.
    return dedupe(seeds)[:16]


def normalize_source_filter(value: str) -> str:
    lower = value.strip().lower().removesuffix(".git").strip("/")
    match = re.search(r"github\.com[:/](?P<owner>[^/]+)/(?P<repo>[^/]+)", lower)
    if match:
        return f"{match.group('owner')}/{match.group('repo')}"
    return lower.removeprefix("https://").removeprefix("http://").strip("/")


def source_filter_aliases(value: str) -> list[str]:
    """Return normalized source forms accepted by --source.

    In addition to GitHub owner/repo slugs, accept the documented
    `github/<owner-or-repo>` shorthand used by agents to mean "from GitHub".
    """
    normalized = normalize_source_filter(value)
    aliases = [normalized]
    if normalized.startswith("github/"):
        aliases.append(normalized.removeprefix("github/"))
    return dedupe(aliases)


def matches_type(capability: dict[str, Any], expected: str | None) -> bool:
    if not expected:
        return True
    return capability_type(capability).lower() == expected.lower()


def matches_status(capability: dict[str, Any], expected: str | None) -> bool:
    if not expected:
        return True
    return capability_status(capability).lower() == expected.lower()


def matches_source(capability: dict[str, Any], expected: str | None) -> bool:
    if not expected:
        return True
    wanted_aliases = source_filter_aliases(expected)
    candidate_aliases: list[str] = []
    for candidate in (source_repository(capability), source_slug(capability), source_path(capability)):
        if candidate:
            candidate_aliases.extend(source_filter_aliases(candidate))
    return any(wanted in candidate for wanted in wanted_aliases for candidate in candidate_aliases)


def filter_capabilities(capabilities: list[dict[str, Any]], args: argparse.Namespace) -> list[dict[str, Any]]:
    package_type = getattr(args, "package_type", None)
    status = getattr(args, "status", None)
    source = getattr(args, "source", None)
    return [
        capability
        for capability in capabilities
        if matches_type(capability, package_type)
        and matches_status(capability, status)
        and matches_source(capability, source)
    ]


def text_for_relevance(capability: dict[str, Any]) -> str:
    fields = [
        capability_ref(capability),
        capability.get("summary") or "",
        capability.get("description") or "",
        source_repository(capability),
        source_path(capability),
    ]
    return " ".join(str(field).lower() for field in fields if field)


def relevance_reasons(capability: dict[str, Any], query: str, args: argparse.Namespace) -> str:
    reasons: list[str] = []
    text = text_for_relevance(capability)
    matched_terms = [token for token in tokenize(query) if token in text]
    if matched_terms:
        reasons.append("matches " + ", ".join(dedupe(matched_terms)[:6]))

    matched_queries = capability.get("_capelryMatchedQueries") or []
    if isinstance(matched_queries, list) and matched_queries:
        display_queries = [str(item) for item in matched_queries[:4]]
        if display_queries != [query]:
            reasons.append("found via " + ", ".join(display_queries))

    if getattr(args, "package_type", None):
        reasons.append(f"type={capability_type(capability)}")
    if getattr(args, "status", None):
        reasons.append(f"status={capability_status(capability)}")
    if getattr(args, "source", None):
        slug = source_slug(capability)
        if slug:
            reasons.append(f"source={slug}")

    return "; ".join(reasons) if reasons else "returned by registry search"


def script_invocation() -> str:
    script = sys.argv[0] or "scripts/capelry.py"
    return f"python3 {shlex.quote(script)}"


def install_snippet(ref: str, target: str) -> str:
    return f"{script_invocation()} install {shlex.quote(ref)} --target {shlex.quote(target)}"


def parse_ref_list(values: list[str]) -> list[str]:
    refs: list[str] = []
    for value in values:
        refs.extend(part.strip() for part in value.split(","))
    result: list[str] = []
    for ref in dedupe(refs):
        parse_ref(ref)
        result.append(ref)
    if not result:
        raise SystemExit("At least one capability ref is required")
    if len(result) > 25:
        raise SystemExit("Bulk detail accepts at most 25 unique refs")
    return result


def bulk_capability_details(base: str, refs: list[str]) -> dict[str, Any]:
    return post_json(api_url(base, "/api/capabilities/bulk"), {"refs": refs})


def capability_output(
    capability: dict[str, Any],
    base: str,
    args: argparse.Namespace,
) -> dict[str, Any]:
    output = {key: value for key, value in capability.items() if not key.startswith("_capelry")}
    ref = capability_ref(capability)
    output["ref"] = ref
    output["version"] = capability_version(capability)
    output["status"] = capability_status(capability)
    output["type"] = capability_type(capability)
    output["sourceSlug"] = source_slug(capability) or None
    output["page"] = f"{base}/{ref}"

    matched_queries = capability.get("_capelryMatchedQueries")
    if matched_queries:
        output["matchedQueries"] = matched_queries
    install_target = getattr(args, "install_snippet", None)
    if install_target:
        output["installSnippet"] = install_snippet(ref, install_target)
    if getattr(args, "explain_relevance", False):
        output["relevance"] = relevance_reasons(capability, getattr(args, "query", ref), args)
    return output


def action_metadata_for_entry(entry: dict[str, Any]) -> dict[str, Any]:
    action_metadata = entry.get("actionMetadata") or {}
    return action_metadata if isinstance(action_metadata, dict) else {}


def detail_summary(entry: dict[str, Any], base: str, install_target: str | None) -> dict[str, Any]:
    capability = entry.get("capability") or entry
    if not isinstance(capability, dict):
        capability = {}
    ref = entry.get("ref") if isinstance(entry.get("ref"), str) else capability_ref(capability)
    latest = capability.get("latestVersion") or {}
    action_metadata = action_metadata_for_entry(entry)
    safety = action_metadata.get("safetyTrustSignals") or {}
    checksum = latest.get("checksumSha256") or safety.get("checksumSha256")
    repository = source_repository(capability) or safety.get("sourceRepository") or ""
    summary = capability.get("summary") or capability.get("description") or ""

    output = {
        "ref": ref,
        "name": ref,
        "version": latest.get("version") or capability_version(capability),
        "type": capability_type(capability),
        "status": latest.get("validationStatus") or safety.get("validationStatus") or capability_status(capability),
        "summary": summary,
        "source": repository,
        "sourcePath": source_path(capability) or None,
        "page": f"{base}/{ref}",
        "checksum": checksum,
    }
    if install_target:
        output["installCommand"] = install_snippet(ref, install_target)
    return output


def print_detail_summaries(summaries: list[dict[str, Any]]) -> None:
    for index, item in enumerate(summaries, start=1):
        print(f"{index}. {item['name']}@{item.get('version', '?')}")
        print(f"   type: {item.get('type', '?')}")
        print(f"   summary: {item.get('summary') or ''}")
        if item.get("source"):
            print(f"   source: {item['source']}")
        if item.get("sourcePath"):
            print(f"   source path: {item['sourcePath']}")
        print(f"   page: {item['page']}")
        if item.get("checksum"):
            print(f"   checksum: {item['checksum']}")
        if item.get("installCommand"):
            print(f"   install: {item['installCommand']}")


def collect_search_results(base: str, args: argparse.Namespace, queries: list[str], per_query_limit: int | None = None) -> list[dict[str, Any]]:
    capabilities_by_ref: dict[str, dict[str, Any]] = {}
    for query in queries:
        for item in search_capabilities(
            base,
            query,
            package_type=getattr(args, "package_type", None),
            status=getattr(args, "status", None),
            domain=getattr(args, "domain", None),
            phase=getattr(args, "phase", None),
            source=getattr(args, "source", None),
            limit=per_query_limit,
        ):
            ref = capability_ref(item)
            if ref == "None/None":
                continue
            if ref not in capabilities_by_ref:
                copy = dict(item)
                copy["_capelryMatchedQueries"] = []
                capabilities_by_ref[ref] = copy
            capabilities_by_ref[ref]["_capelryMatchedQueries"].append(query)
    return filter_capabilities(list(capabilities_by_ref.values()), args)


def command_search(args: argparse.Namespace) -> None:
    base = registry_base(args)
    queries = expanded_queries(args.query) if args.expand else [args.query]
    display_limit = result_limit(args.limit)
    api_limit = clamp_api_search_limit(max(display_limit, 25))
    filtered = collect_search_results(base, args, queries, per_query_limit=api_limit)
    limited = filtered[:display_limit]

    if args.json_output:
        print_json(
            {
                "registry": base,
                "query": args.query,
                "queries": queries,
                "filters": {
                    "type": args.package_type,
                    "status": args.status,
                    "source": args.source,
                    "domain": args.domain,
                    "phase": args.phase,
                },
                "count": len(filtered),
                "limit": display_limit,
                "suggestedQueries": expanded_queries(args.query)[1:],
                "capabilities": [capability_output(item, base, args) for item in limited],
            }
        )
        return

    if not filtered:
        print("No capabilities found.")
        suggestions = expanded_queries(args.query)[1:7]
        if suggestions and not args.expand:
            print("Try --expand or related queries: " + ", ".join(suggestions))
        return

    show_metadata = args.explain_relevance or args.install_snippet or args.package_type or args.status or args.source
    for item in limited:
        ref = capability_ref(item)
        version = capability_version(item)
        package_type = capability_type(item)
        summary = item.get("summary") or item.get("description") or ""
        print(f"{ref}@{version} [{package_type}] {summary}")
        if show_metadata:
            metadata = [f"status={capability_status(item)}"]
            slug = source_slug(item)
            if slug:
                metadata.append(f"source={slug}")
            print("  " + " ".join(metadata))
        if args.explain_relevance:
            print(f"  relevance: {relevance_reasons(item, args.query, args)}")
        if args.install_snippet:
            print(f"  install: {install_snippet(ref, args.install_snippet)}")


def command_info(args: argparse.Namespace) -> None:
    base = registry_base(args)
    capability = capability_detail(base, args.ref)
    latest = capability.get("latestVersion") or {}
    source = capability.get("source") or {}
    ref = capability_ref(capability)

    if args.json_output:
        print_json({"registry": base, "capability": capability_output(capability, base, args)})
        return

    print(f"{ref}@{latest.get('version', '?')}")
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
    if args.install_snippet:
        print(f"install: {install_snippet(ref, args.install_snippet)}")


def command_bulk_info(args: argparse.Namespace) -> None:
    base = registry_base(args)
    refs = parse_ref_list(args.refs)
    payload = bulk_capability_details(base, refs)
    entries = payload.get("capabilities", [])
    summaries = [detail_summary(entry, base, args.install_snippet) for entry in entries if isinstance(entry, dict)]

    if args.json_output:
        print_json({"registry": base, "refs": refs, "shortlist": summaries, "bulk": payload})
        return

    if summaries:
        print_detail_summaries(summaries)
    for error in payload.get("errors", []) or []:
        if isinstance(error, dict):
            print(f"error: {error.get('ref', '?')}: {error.get('code', '?')} - {error.get('message', '')}")


def compact_query(query: str) -> str:
    return " ".join(tokenize(query)) or query.strip()


def discover_queries(query: str, extra_queries: list[str] | None, expand: bool) -> list[str]:
    compact = compact_query(query)
    seeds: list[str] = []
    if expand:
        seeds.extend(expanded_queries(query)[1:])
    seeds.extend([compact, query])
    for extra in extra_queries or []:
        seeds.extend(compact_query(part) for part in extra.split(","))
    return dedupe(seeds)


def command_discover(args: argparse.Namespace) -> None:
    base = registry_base(args)
    queries = discover_queries(args.query, args.extra_query, expand=not args.no_expand)
    top = min(max(args.top, 1), 25)
    api_limit = clamp_api_search_limit(max(args.search_limit, top, 25))
    filtered = collect_search_results(base, args, queries, per_query_limit=api_limit)
    refs = [capability_ref(item) for item in filtered[:top]]

    payload: dict[str, Any] = {"capabilities": [], "errors": [], "meta": {"requested": 0, "returned": 0, "limit": 25}}
    summaries: list[dict[str, Any]] = []
    if refs:
        payload = bulk_capability_details(base, refs)
        summaries = [detail_summary(entry, base, args.install_snippet) for entry in payload.get("capabilities", []) if isinstance(entry, dict)]

    if args.json_output:
        print_json(
            {
                "registry": base,
                "query": args.query,
                "queries": queries,
                "filters": {
                    "type": args.package_type,
                    "status": args.status,
                    "source": args.source,
                    "domain": args.domain,
                    "phase": args.phase,
                },
                "refs": refs,
                "shortlist": summaries,
                "bulkErrors": payload.get("errors", []),
            }
        )
        return

    if not refs:
        print("No capabilities found.")
        return

    print("Queries: " + "; ".join(queries))
    print_detail_summaries(summaries)
    for error in payload.get("errors", []) or []:
        if isinstance(error, dict):
            print(f"error: {error.get('ref', '?')}: {error.get('code', '?')} - {error.get('message', '')}")


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
    source_path_value = source.get("path")
    branch = source.get("defaultBranch") or "main"
    if not isinstance(repository, str) or not isinstance(source_path_value, str):
        return False
    parts = github_parts(repository)
    if parts is None:
        return False

    owner, repo = parts
    prepare_dest(dest, force)
    download_github_path(owner, repo, source_path_value, branch, dest)
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
    if not args.json_output:
        print(f"Downloading {namespace}/{name}@{version} from {base}...")
    archive = fetch_bytes(archive_url)

    if extract_skill_archive(archive, dest, args.force):
        installed_from = "validated Capelry archive"
    elif install_from_github_source(capability, dest, args.force):
        installed_from = "declared GitHub source fallback"
    else:
        raise SystemExit("Package did not contain SKILL.md and no supported source fallback was available")

    skill_name = installed_skill_name(dest)
    if args.json_output:
        print_json(
            {
                "registry": base,
                "ref": f"{namespace}/{name}",
                "version": version,
                "destination": str(dest),
                "installedFrom": installed_from,
                "skillName": skill_name,
                "next": f"reload or restart your agent; in Pi run /reload and then /skill:{skill_name}",
            }
        )
        return

    print(f"Installed {namespace}/{name}@{version} to {dest}")
    print(f"source: {installed_from}")
    print("Next: reload or restart your agent. In Pi, run /reload and then /skill:" + skill_name)


def add_json_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--json",
        dest="json_output",
        action="store_true",
        default=argparse.SUPPRESS,
        help="Emit machine-readable JSON output",
    )


def add_install_snippet_argument(parser: argparse.ArgumentParser, default: str | None = None) -> None:
    parser.add_argument(
        "--install-snippet",
        nargs="?",
        const="agents-project",
        default=default,
        choices=sorted(TARGET_ROOTS),
        help="Include a python3 install command for the given target, e.g. pi-project",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Search, inspect, and install capabilities from Capelry")
    parser.add_argument("--registry", help=f"Registry base URL (default: {DEFAULT_REGISTRY} or CAPELRY_REGISTRY_URL)")
    parser.add_argument("--json", dest="json_output", action="store_true", help="Emit machine-readable JSON output")
    parser.set_defaults(json_output=False)
    subparsers = parser.add_subparsers(dest="command", required=True)

    search = subparsers.add_parser("search", help="Search capabilities")
    search.add_argument("query")
    search.add_argument("--limit", type=int, default=20)
    search.add_argument("--expand", action="store_true", help="Search related terms when an exact phrase is too narrow")
    search.add_argument("--type", dest="package_type", help="Filter by package type, e.g. skill, agent, prompt")
    search.add_argument("--status", help="Filter by latest validation status, e.g. passed")
    search.add_argument("--source", help="Filter by source repository, e.g. github/awesome-copilot")
    search.add_argument("--domain", help="Filter by derived domain facet, e.g. devops, docker, sre")
    search.add_argument("--phase", help="Filter by lifecycle facet, e.g. production, preflight, observability")
    add_install_snippet_argument(search)
    search.add_argument("--explain-relevance", action="store_true", help="Explain why each result may be relevant")
    add_json_argument(search)
    search.set_defaults(func=command_search)

    discover = subparsers.add_parser("discover", help="Search related queries, bulk-inspect top results, and print a shortlist")
    discover.add_argument("query")
    discover.add_argument("--query", dest="extra_query", action="append", help="Additional related query; repeat or comma-separate")
    discover.add_argument("--top", type=int, default=5, help="Number of top refs to bulk-inspect (max 25)")
    discover.add_argument("--search-limit", type=int, default=10, help="Per-query search limit before dedupe")
    discover.add_argument("--no-expand", action="store_true", help="Disable built-in related-query expansion")
    discover.add_argument("--type", dest="package_type", default="skill", help="Filter by package type (default: skill)")
    discover.add_argument("--status", default="passed", help="Filter by validation status (default: passed)")
    discover.add_argument("--source", help="Filter by source repository, e.g. github/awesome-copilot")
    discover.add_argument("--domain", help="Filter by derived domain facet, e.g. devops, docker, sre")
    discover.add_argument("--phase", help="Filter by lifecycle facet, e.g. production, preflight, observability")
    add_install_snippet_argument(discover, default="pi-project")
    add_json_argument(discover)
    discover.set_defaults(func=command_discover)

    info = subparsers.add_parser("info", help="Show capability details")
    info.add_argument("ref", help="namespace/name")
    add_install_snippet_argument(info)
    add_json_argument(info)
    info.set_defaults(func=command_info)

    bulk_info = subparsers.add_parser(
        "bulk-info",
        aliases=["batch-info"],
        help="Bulk-inspect up to 25 refs with /api/capabilities/bulk",
    )
    bulk_info.add_argument("refs", nargs="+", help="Refs as space-separated or comma-separated namespace/name values")
    add_install_snippet_argument(bulk_info, default="pi-project")
    add_json_argument(bulk_info)
    bulk_info.set_defaults(func=command_bulk_info)

    install = subparsers.add_parser("install", help="Install a skill capability")
    install.add_argument("ref", help="namespace/name or namespace/name@version")
    install.add_argument("--version", help="Version override")
    install.add_argument("--target", choices=sorted(TARGET_ROOTS), default="agents-project")
    install.add_argument("--dest", help="Exact destination directory")
    install.add_argument("--name", help="Install directory name override")
    install.add_argument("--force", action="store_true", help="Replace an existing destination")
    add_json_argument(install)
    install.set_defaults(func=command_install)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

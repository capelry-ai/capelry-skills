#!/usr/bin/env python3
"""Small stdlib-only client for the Capelry capability registry."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import re
import shlex
import shutil
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any

DEFAULT_REGISTRY = "https://capelry.com"
SELF_GITHUB_REPOSITORY = "capelry-ai/capelry-skills"
SELF_SOURCE_PATH = "skills/capelry"
SELF_DEFAULT_REF = "main"
API_SEARCH_LIMIT_MIN = 1
API_SEARCH_LIMIT_MAX = 100
ARD_SKILL_MEDIA_TYPES = (
    "application/vnd.capelry.skill+zip",
    "application/vnd.capelry.skill-source+json",
)
ARD_PACKAGE_TYPE_MEDIA_TYPES = {
    "skill": ARD_SKILL_MEDIA_TYPES,
}
ARD_TRUST_STATE_FILTER = "metadata.com.capelry.trustState"
ARD_VALIDATION_STATUS_FILTER = "metadata.com.capelry.validationStatus"
ARD_SOURCE_REPOSITORY_FILTER = "metadata.com.capelry.sourceRepository"
ARD_LEGACY_REF_FILTER = "metadata.com.capelry.legacyRef"
ARD_TRUST_STATE_METADATA = "com.capelry.trustState"
ARD_LEGACY_REF_METADATA = "com.capelry.legacyRef"

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


def env_truthy(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in {"1", "true", "yes", "on", "legacy"}


def selected_registry_api(args: argparse.Namespace) -> str:
    explicit_api = getattr(args, "api", None)
    if explicit_api:
        return explicit_api
    if env_truthy("CAPELRY_USE_LEGACY_API"):
        return "legacy"
    return "ard"


def api_url(base: str, path: str) -> str:
    return f"{base}{path if path.startswith('/') else '/' + path}"


def http_headers(url: str, *, user_agent: str = "capelry-skill/1.1.0") -> dict[str, str]:
    headers = {"User-Agent": user_agent}
    parsed = urllib.parse.urlparse(url)
    if parsed.netloc.lower() == "api.github.com":
        token = (
            os.environ.get("CAPELRY_GITHUB_TOKEN")
            or os.environ.get("GITHUB_TOKEN")
            or os.environ.get("GH_TOKEN")
            or ""
        ).strip()
        if token:
            headers["Authorization"] = f"Bearer {token}"
    return headers


def fetch_bytes(url: str) -> bytes:
    request = urllib.request.Request(url, headers=http_headers(url))
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


def github_headers(accept: str | None = "application/vnd.github+json") -> dict[str, str]:
    headers = {"User-Agent": "capelry-skill/self-update"}
    if accept:
        headers["Accept"] = accept
    token = (
        os.environ.get("CAPELRY_GITHUB_TOKEN")
        or os.environ.get("GITHUB_TOKEN")
        or os.environ.get("GH_TOKEN")
        or ""
    ).strip()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def fetch_github_json(url: str, *, allow_404: bool = False) -> Any:
    request = urllib.request.Request(url, headers=github_headers())
    try:
        with urllib.request.urlopen(request) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        if allow_404 and error.code == 404:
            return None
        body = error.read().decode("utf-8", errors="replace")
        raise SystemExit(f"HTTP {error.code} for {url}\n{body}") from error
    except urllib.error.URLError as error:
        raise SystemExit(f"Unable to reach {url}: {error.reason}") from error


def fetch_github_bytes(url: str) -> bytes:
    request = urllib.request.Request(url, headers=github_headers("application/octet-stream"))
    try:
        with urllib.request.urlopen(request) as response:
            return response.read()
    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8", errors="replace")
        raise SystemExit(f"HTTP {error.code} for {url}\n{body}") from error
    except urllib.error.URLError as error:
        raise SystemExit(f"Unable to reach {url}: {error.reason}") from error


def post_json(url: str, payload: dict[str, Any]) -> Any:
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        headers={
            "User-Agent": "capelry-skill/1.1.0",
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


def ard_error_message(url: str, status: int, body_text: str) -> str:
    try:
        payload = json.loads(body_text)
    except json.JSONDecodeError:
        payload = None
    if isinstance(payload, dict):
        code = payload.get("errorCode")
        message = payload.get("message")
        if isinstance(code, str) and isinstance(message, str):
            return f"ARD {code} for {url}: {message}"
        error = payload.get("error")
        if isinstance(error, dict):
            code = error.get("errorCode") or error.get("code")
            message = error.get("message")
            if isinstance(code, str) and isinstance(message, str):
                return f"ARD {code} for {url}: {message}"
    return f"HTTP {status} for {url}\n{body_text}"


def fetch_ard_json(url: str) -> Any:
    request = urllib.request.Request(url, headers={**http_headers(url), "Accept": "application/json"})
    try:
        with urllib.request.urlopen(request) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        body_text = error.read().decode("utf-8", errors="replace")
        raise SystemExit(ard_error_message(url, error.code, body_text)) from error
    except urllib.error.URLError as error:
        raise SystemExit(f"Unable to reach {url}: {error.reason}") from error


def post_ard_json(url: str, payload: dict[str, Any]) -> Any:
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        headers={
            "User-Agent": "capelry-skill/1.1.0",
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
        raise SystemExit(ard_error_message(url, error.code, body_text)) from error
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


def split_arg_values(values: list[str] | None) -> list[str]:
    result: list[str] = []
    for value in values or []:
        result.extend(part.strip() for part in value.split(","))
    return dedupe([part for part in result if part])


def ard_media_types_for_package_type(package_type: str) -> list[str]:
    normalized = package_type.strip().lower()
    mapped = ARD_PACKAGE_TYPE_MEDIA_TYPES.get(normalized)
    if mapped:
        return list(mapped)
    safe = re.sub(r"[^a-z0-9-]+", "-", normalized).strip("-")
    if not safe:
        return []
    return [f"application/vnd.capelry.{safe}+zip", f"application/vnd.capelry.{safe}-source+json"]


def add_ard_filter(filters: dict[str, list[str]], field: str, values: list[str] | str | None) -> None:
    if values is None:
        return
    value_list = [values] if isinstance(values, str) else values
    cleaned = [str(value).strip() for value in value_list if str(value).strip()]
    if not cleaned:
        return
    filters[field] = dedupe(filters.get(field, []) + cleaned)


def parse_ard_filter_arg(value: str) -> tuple[str, list[str]]:
    field, separator, raw_value = value.partition("=")
    if not separator or not field.strip() or not raw_value.strip():
        raise SystemExit("ARD filters must use FIELD=VALUE, for example --filter tags=ard")
    return field.strip(), split_arg_values([raw_value])


def build_ard_filter(args: argparse.Namespace) -> dict[str, list[str]]:
    filters: dict[str, list[str]] = {}
    package_type = getattr(args, "package_type", None)
    if package_type:
        add_ard_filter(filters, "type", ard_media_types_for_package_type(package_type))
    add_ard_filter(filters, "type", split_arg_values(getattr(args, "media_type", None)))
    add_ard_filter(filters, "publisher", split_arg_values(getattr(args, "publisher", None)))
    add_ard_filter(filters, ARD_TRUST_STATE_FILTER, split_arg_values(getattr(args, "trust_state", None)))
    add_ard_filter(filters, ARD_VALIDATION_STATUS_FILTER, getattr(args, "status", None))
    add_ard_filter(filters, ARD_SOURCE_REPOSITORY_FILTER, getattr(args, "source", None))
    for raw_filter in getattr(args, "ard_filter", None) or []:
        field, values = parse_ard_filter_arg(raw_filter)
        add_ard_filter(filters, field, values)
    return filters


def ard_search_payload(args: argparse.Namespace, query: str, page_size: int | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {"query": {"text": query}, "federation": getattr(args, "federation", "none")}
    filters = build_ard_filter(args)
    if filters:
        payload["query"]["filter"] = filters
    clamped_page_size = clamp_api_search_limit(page_size)
    if clamped_page_size is not None:
        payload["pageSize"] = clamped_page_size
    return payload


def ard_search_entries(base: str, args: argparse.Namespace, query: str, page_size: int | None = None) -> list[dict[str, Any]]:
    payload = post_ard_json(api_url(base, "/search"), ard_search_payload(args, query, page_size=page_size))
    results = payload.get("results", []) if isinstance(payload, dict) else []
    return results if isinstance(results, list) else []


def ard_quote_filter_value(value: str) -> str:
    return "'" + value.replace("\\", "\\\\").replace("'", "\\'") + "'"


def ard_agents_entries(base: str, *, field: str, value: str, page_size: int = 1) -> list[dict[str, Any]]:
    params = urllib.parse.urlencode(
        {
            "filter": f"{field} = {ard_quote_filter_value(value)}",
            "pageSize": str(clamp_api_search_limit(page_size) or 1),
        }
    )
    payload = fetch_ard_json(api_url(base, f"/agents?{params}"))
    items = payload.get("items", []) if isinstance(payload, dict) else []
    return items if isinstance(items, list) else []


def ard_metadata(entry: dict[str, Any]) -> dict[str, Any]:
    metadata = entry.get("metadata")
    return metadata if isinstance(metadata, dict) else {}


def ard_trust_state(entry: dict[str, Any]) -> str | None:
    metadata = ard_metadata(entry)
    trust_state = metadata.get(ARD_TRUST_STATE_METADATA) or metadata.get(ARD_TRUST_STATE_FILTER) or entry.get("trustState")
    return trust_state if isinstance(trust_state, str) and trust_state else None


def ard_entry_media_type(entry: dict[str, Any]) -> str:
    media_type = entry.get("type") or entry.get("mediaType")
    return media_type if isinstance(media_type, str) and media_type else "?"


def ard_entry_output(entry: dict[str, Any]) -> dict[str, Any]:
    metadata = ard_metadata(entry)
    output = {
        "identifier": entry.get("identifier"),
        "displayName": entry.get("displayName"),
        "version": entry.get("version"),
        "mediaType": ard_entry_media_type(entry),
        "description": entry.get("description"),
        "score": entry.get("score"),
        "source": entry.get("source"),
        "trustState": ard_trust_state(entry),
        "legacyRef": metadata.get(ARD_LEGACY_REF_METADATA) or metadata.get(ARD_LEGACY_REF_FILTER),
    }
    return {key: value for key, value in output.items() if value is not None}


def print_ard_entries(entries: list[dict[str, Any]]) -> None:
    for entry in entries:
        identifier = entry.get("identifier") or "?"
        display_name = entry.get("displayName") or ""
        version = entry.get("version") or "?"
        media_type = ard_entry_media_type(entry)
        print(f"{identifier}@{version} [{media_type}] {display_name}")
        metadata = []
        if entry.get("score") is not None:
            metadata.append(f"score={entry['score']}")
        if entry.get("source"):
            metadata.append(f"source={entry['source']}")
        trust_state = ard_trust_state(entry)
        if trust_state:
            metadata.append(f"trust={trust_state}")
        if metadata:
            print("  " + " ".join(str(item) for item in metadata))
        description = entry.get("description")
        if isinstance(description, str) and description:
            print(f"  {description}")


def ard_resolution_field(value: str) -> str:
    return "identifier" if value.startswith("urn:ai:") else ARD_LEGACY_REF_FILTER


def ard_detail_summary(entry: dict[str, Any], install_target: str | None = None) -> dict[str, Any]:
    metadata = ard_metadata(entry)
    identifier = entry.get("identifier") if isinstance(entry.get("identifier"), str) else "?"
    legacy_ref = metadata.get(ARD_LEGACY_REF_METADATA) or metadata.get(ARD_LEGACY_REF_FILTER)
    detail_url = metadata.get("com.capelry.detailUrl") or metadata.get("metadata.com.capelry.detailUrl")
    source = entry.get("source") or metadata.get("com.capelry.sourceRepository") or metadata.get(ARD_SOURCE_REPOSITORY_FILTER)
    output = {
        "identifier": identifier,
        "name": identifier,
        "displayName": entry.get("displayName") or identifier,
        "version": entry.get("version") or "?",
        "mediaType": ard_entry_media_type(entry),
        "summary": entry.get("description") or entry.get("displayName") or "",
        "source": source,
        "page": detail_url if isinstance(detail_url, str) and detail_url else None,
        "score": entry.get("score"),
        "trustState": ard_trust_state(entry),
        "legacyRef": legacy_ref if isinstance(legacy_ref, str) and legacy_ref else None,
    }
    if install_target and output["legacyRef"]:
        output["installCommand"] = install_snippet(str(output["legacyRef"]), install_target)
    return {key: value for key, value in output.items() if value is not None}


def print_ard_detail_summaries(summaries: list[dict[str, Any]]) -> None:
    for index, item in enumerate(summaries, start=1):
        print(f"{index}. {item['identifier']}@{item.get('version', '?')}")
        if item.get("displayName") and item["displayName"] != item["identifier"]:
            print(f"   name: {item['displayName']}")
        print(f"   type: {item.get('mediaType', '?')}")
        print(f"   summary: {item.get('summary') or ''}")
        if item.get("source"):
            print(f"   source: {item['source']}")
        if item.get("page"):
            print(f"   page: {item['page']}")
        if item.get("score") is not None:
            print(f"   score: {item['score']}")
        if item.get("trustState"):
            print(f"   trust: {item['trustState']}")
        if item.get("legacyRef"):
            print(f"   legacy ref: {item['legacyRef']}")
        if item.get("installCommand"):
            print(f"   install: {item['installCommand']}")


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


def collect_ard_search_results(base: str, args: argparse.Namespace, queries: list[str], per_query_limit: int | None = None) -> list[dict[str, Any]]:
    entries_by_identifier: dict[str, dict[str, Any]] = {}
    for query in queries:
        for entry in ard_search_entries(base, args, query, page_size=per_query_limit):
            identifier = entry.get("identifier")
            if not isinstance(identifier, str) or not identifier:
                continue
            if identifier not in entries_by_identifier:
                copy = dict(entry)
                copy["_capelryMatchedQueries"] = []
                entries_by_identifier[identifier] = copy
            entries_by_identifier[identifier]["_capelryMatchedQueries"].append(query)
    return list(entries_by_identifier.values())


def command_search(args: argparse.Namespace) -> None:
    base = registry_base(args)
    queries = expanded_queries(args.query) if args.expand else [args.query]
    display_limit = result_limit(args.limit)

    if selected_registry_api(args) == "ard":
        entries = collect_ard_search_results(base, args, queries, per_query_limit=display_limit)
        limited_entries = entries[:display_limit]
        if args.json_output:
            print_json(
                {
                    "registry": base,
                    "api": "ard",
                    "query": args.query,
                    "queries": queries,
                    "request": ard_search_payload(args, args.query, page_size=display_limit),
                    "count": len(entries),
                    "limit": display_limit,
                    "suggestedQueries": expanded_queries(args.query)[1:],
                    "entries": [ard_entry_output(entry) for entry in limited_entries],
                }
            )
            return
        if not entries:
            print("No ARD entries found.")
            return
        print_ard_entries(limited_entries)
        return

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
    if selected_registry_api(args) == "ard":
        entries = ard_agents_entries(base, field=ard_resolution_field(args.ref), value=args.ref, page_size=1)
        if not entries:
            raise SystemExit(f"No ARD entry found for {args.ref}")
        entry = entries[0]
        if args.json_output:
            print_json({"registry": base, "api": "ard", "entry": ard_entry_output(entry)})
            return
        print_ard_entries([entry])
        return

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

    if selected_registry_api(args) == "ard":
        entries = collect_ard_search_results(base, args, queries, per_query_limit=api_limit)
        shortlist = entries[:top]
        summaries = [ard_detail_summary(entry, args.install_snippet) for entry in shortlist]
        if args.json_output:
            print_json(
                {
                    "registry": base,
                    "api": "ard",
                    "query": args.query,
                    "queries": queries,
                    "filters": build_ard_filter(args),
                    "entries": [ard_entry_output(entry) for entry in shortlist],
                    "shortlist": summaries,
                }
            )
            return

        if not shortlist:
            print("No ARD entries found.")
            return

        print("Queries: " + "; ".join(queries))
        print_ard_detail_summaries(summaries)
        return

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
                "api": "legacy",
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


def github_archive_url(owner: str, repo: str, ref: str) -> str:
    return f"https://codeload.github.com/{owner}/{repo}/zip/{urllib.parse.quote(ref)}"


def normalize_github_source_path(path: str) -> str:
    normalized = path.strip().replace("\\", "/").strip("/")
    if normalized in ("", "."):
        return ""
    parts = [part for part in normalized.split("/") if part and part != "."]
    if any(part == ".." for part in parts):
        raise SystemExit(f"Unsafe GitHub source path: {path}")
    return "/".join(parts)


def github_archive_member_rel(member: zipfile.ZipInfo) -> str:
    """Return a GitHub zip member path relative to the archive root directory."""
    parts = PurePosixPath(member.filename).parts
    if len(parts) <= 1:
        return ""
    return PurePosixPath(*parts[1:]).as_posix()


def github_archive_rel_members(zf: zipfile.ZipFile) -> dict[str, zipfile.ZipInfo]:
    rel_members: dict[str, zipfile.ZipInfo] = {}
    for member in safe_zip_members(zf):
        rel = github_archive_member_rel(member)
        if rel:
            rel_members[rel] = member
    return rel_members


def download_github_archive_path(owner: str, repo: str, path: str, ref: str, dest: Path, force: bool) -> None:
    source_path_value = normalize_github_source_path(path)
    archive = fetch_bytes(github_archive_url(owner, repo, ref))

    with zipfile.ZipFile(io.BytesIO(archive)) as zf:
        rel_members = github_archive_rel_members(zf)
        if source_path_value:
            direct_file = rel_members.get(source_path_value)
            skill_marker = f"{source_path_value}/SKILL.md"
        else:
            direct_file = None
            skill_marker = "SKILL.md"
        if direct_file is None and skill_marker not in rel_members:
            display_path = source_path_value or "."
            raise SystemExit(f"GitHub archive did not contain source path: {display_path}")

        prepare_dest(dest, force)
        if direct_file is not None:
            target = dest / Path(source_path_value).name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(zf.read(direct_file))
        else:
            prefix = f"{source_path_value}/" if source_path_value else ""
            for rel, member in rel_members.items():
                if prefix and not rel.startswith(prefix):
                    continue
                output_rel = rel[len(prefix) :] if prefix else rel
                if not output_rel:
                    continue
                out = dest / output_rel
                out.parent.mkdir(parents=True, exist_ok=True)
                out.write_bytes(zf.read(member))

    if not (dest / "SKILL.md").exists():
        shutil.rmtree(dest, ignore_errors=True)
        raise SystemExit("GitHub archive fallback completed but did not produce SKILL.md")


def github_archive_file_bytes(owner: str, repo: str, path: str, ref: str) -> bytes:
    source_path_value = normalize_github_source_path(path)
    if not source_path_value:
        raise SystemExit("GitHub archive file path cannot be repository root")
    archive = fetch_bytes(github_archive_url(owner, repo, ref))
    with zipfile.ZipFile(io.BytesIO(archive)) as zf:
        rel_members = github_archive_rel_members(zf)
        member = rel_members.get(source_path_value)
        if member is None:
            raise SystemExit(f"GitHub archive did not contain file: {source_path_value}")
        return zf.read(member)


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
    payload = fetch_github_json(github_api_url(owner, repo, path, ref))
    if isinstance(payload, dict):
        if payload.get("type") != "file":
            raise SystemExit(f"Unsupported GitHub content type at {path}: {payload.get('type')}")
        target = dest / source_relative_path(path, root_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(fetch_github_bytes(payload["download_url"]))
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
            out.write_bytes(fetch_github_bytes(entry["download_url"]))
        elif entry_type == "dir":
            download_github_path(owner, repo, entry_path, ref, dest, root_path)


def install_from_github_source(capability: dict[str, Any], dest: Path, force: bool) -> str | None:
    source = capability.get("source") or {}
    repository = source.get("repository")
    source_path_value = source.get("path")
    branch = source.get("defaultBranch") or "main"
    if not isinstance(repository, str) or not isinstance(source_path_value, str):
        return None
    parts = github_parts(repository)
    if parts is None:
        return None

    owner, repo = parts
    if dest.exists() and not force:
        raise SystemExit(f"Destination already exists: {dest}\nUse --force to replace it.")

    archive_error: BaseException | None = None
    try:
        download_github_archive_path(owner, repo, source_path_value, branch, dest, force)
        return "declared GitHub codeload archive fallback"
    except (SystemExit, zipfile.BadZipFile) as error:
        archive_error = error

    try:
        prepare_dest(dest, force)
        download_github_path(owner, repo, source_path_value, branch, dest)
    except SystemExit as error:
        shutil.rmtree(dest, ignore_errors=True)
        raise SystemExit(f"{error}\n\nGitHub archive fallback also failed:\n{archive_error}") from error

    if not (dest / "SKILL.md").exists():
        shutil.rmtree(dest, ignore_errors=True)
        raise SystemExit("GitHub source fallback completed but did not produce SKILL.md")
    return "declared GitHub Contents API fallback"


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


def normalize_sha256(value: str | None) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip().lower()
    if normalized.startswith("sha256:"):
        normalized = normalized.split(":", 1)[1]
    return normalized if re.fullmatch(r"[a-f0-9]{64}", normalized) else None


def verify_archive_checksum(archive: bytes, expected: str | None) -> str | None:
    checksum = hashlib.sha256(archive).hexdigest()
    normalized_expected = normalize_sha256(expected)
    if normalized_expected and checksum != normalized_expected:
        raise SystemExit(f"Archive SHA-256 mismatch: expected {normalized_expected}, got {checksum}")
    return checksum


def ard_metadata_string(entry: dict[str, Any], *keys: str) -> str | None:
    metadata = ard_metadata(entry)
    for key in keys:
        value = metadata.get(key)
        if isinstance(value, str) and value:
            return value
    return None


def ard_archive_url(entry: dict[str, Any]) -> str | None:
    value = ard_metadata_string(entry, "com.capelry.archiveUrl", "metadata.com.capelry.archiveUrl")
    if value:
        return value
    url = entry.get("url")
    return url if isinstance(url, str) and url else None


def ard_archive_checksum(entry: dict[str, Any]) -> str | None:
    value = ard_metadata_string(
        entry,
        "com.capelry.archiveChecksumSha256",
        "metadata.com.capelry.archiveChecksumSha256",
        "com.capelry.checksumSha256",
        "metadata.com.capelry.checksumSha256",
    )
    if value:
        return value
    checksum = entry.get("checksumSha256")
    return checksum if isinstance(checksum, str) else None


def ard_legacy_ref(entry: dict[str, Any]) -> str | None:
    value = ard_metadata_string(entry, ARD_LEGACY_REF_METADATA, ARD_LEGACY_REF_FILTER)
    return value if value and "/" in value else None


def slugify_install_name(value: str) -> str:
    slug = re.sub(r"[^a-z0-9-]+", "-", value.lower()).strip("-")
    return slug or "capelry-entry"


def ard_entry_install_name(entry: dict[str, Any], requested_ref: str) -> str:
    legacy_ref = ard_legacy_ref(entry)
    if legacy_ref:
        return legacy_ref.split("/", 1)[1]
    identifier = entry.get("identifier")
    if isinstance(identifier, str) and identifier:
        return slugify_install_name(identifier.rsplit(":", 1)[-1].rsplit("/", 1)[-1])
    display_name = entry.get("displayName")
    if isinstance(display_name, str) and display_name:
        return slugify_install_name(display_name)
    return slugify_install_name(requested_ref)


def source_descriptor_value(descriptor: dict[str, Any], entry: dict[str, Any], *keys: str) -> str | None:
    for key in keys:
        value = descriptor.get(key)
        if isinstance(value, str) and value:
            return value
    return ard_metadata_string(entry, *keys)


def download_archive_source_path(archive_url: str, source_path_value: str, dest: Path, force: bool) -> None:
    source_path_value = normalize_github_source_path(source_path_value)
    archive = fetch_bytes(archive_url)
    with zipfile.ZipFile(io.BytesIO(archive)) as zf:
        rel_members = github_archive_rel_members(zf)
        skill_marker = f"{source_path_value}/SKILL.md" if source_path_value else "SKILL.md"
        if skill_marker not in rel_members:
            display_path = source_path_value or "."
            raise SystemExit(f"Source archive did not contain source path: {display_path}")
        prepare_dest(dest, force)
        prefix = f"{source_path_value}/" if source_path_value else ""
        for rel, member in rel_members.items():
            if prefix and not rel.startswith(prefix):
                continue
            output_rel = rel[len(prefix) :] if prefix else rel
            if not output_rel:
                continue
            out = dest / output_rel
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(zf.read(member))
    if not (dest / "SKILL.md").exists():
        shutil.rmtree(dest, ignore_errors=True)
        raise SystemExit("Source archive install completed but did not produce SKILL.md")


def ard_source_descriptor(entry: dict[str, Any]) -> dict[str, Any]:
    data = entry.get("data")
    if isinstance(data, dict):
        return data
    return {}


def print_ard_trust_summary(entry: dict[str, Any]) -> None:
    print(f"ARD entry: {entry.get('identifier', '?')}")
    print(f"type: {ard_entry_media_type(entry)}")
    trust_state = ard_trust_state(entry)
    if trust_state:
        print(f"trust: {trust_state}")
    checksum = ard_archive_checksum(entry)
    if checksum:
        print(f"checksum: {checksum}")
    trust_manifest = entry.get("trustManifest")
    if isinstance(trust_manifest, dict):
        identity = trust_manifest.get("identity")
        identity_type = trust_manifest.get("identityType")
        if identity:
            suffix = f" ({identity_type})" if identity_type else ""
            print(f"trust identity: {identity}{suffix}")
        provenance = trust_manifest.get("provenance")
        if isinstance(provenance, list):
            for item in provenance[:3]:
                if isinstance(item, dict):
                    relation = item.get("relation") or "provenance"
                    source_id = item.get("sourceId") or item.get("url") or item.get("source")
                    if source_id:
                        print(f"provenance: {relation} {source_id}")


def resolve_ard_entry_for_install(base: str, ref: str) -> dict[str, Any]:
    entries = ard_agents_entries(base, field=ard_resolution_field(ref), value=ref, page_size=1)
    if not entries:
        raise SystemExit(f"No ARD entry found for {ref}")
    return entries[0]


def install_ard_zip_entry(entry: dict[str, Any], dest: Path, force: bool) -> tuple[str, str]:
    archive_url = ard_archive_url(entry)
    if not archive_url:
        raise SystemExit("ARD zip entry did not include an archive URL")
    archive = fetch_bytes(archive_url)
    checksum = verify_archive_checksum(archive, ard_archive_checksum(entry))
    if not extract_skill_archive(archive, dest, force):
        raise SystemExit("ARD zip archive did not contain SKILL.md")
    return "ARD skill zip", checksum


def install_ard_source_entry(entry: dict[str, Any], dest: Path, force: bool) -> str:
    descriptor = ard_source_descriptor(entry)
    archive_url = source_descriptor_value(descriptor, entry, "archiveUrl", "com.capelry.sourceArchiveUrl")
    source_path_value = source_descriptor_value(descriptor, entry, "path", "sourcePath", "com.capelry.sourcePath", "metadata.com.capelry.sourcePath") or ""
    ref = source_descriptor_value(descriptor, entry, "ref", "sourceRef", "defaultBranch", "com.capelry.sourceRef", "metadata.com.capelry.sourceRef") or "main"
    repository = source_descriptor_value(descriptor, entry, "repository", "sourceRepository", "com.capelry.sourceRepository", "metadata.com.capelry.sourceRepository")

    if archive_url:
        download_archive_source_path(archive_url, source_path_value, dest, force)
        return f"ARD source archive descriptor at {ref}"

    if repository:
        parts = github_parts(repository)
        if parts:
            owner, repo = parts
            download_github_archive_path(owner, repo, source_path_value, ref, dest, force)
            return f"ARD GitHub source descriptor at {ref}"

    raise SystemExit("ARD source entry did not include a supported GitHub repository or source archive descriptor")


def unsupported_ard_install_message(entry: dict[str, Any]) -> str:
    url = entry.get("url")
    guidance = f" Open/connect manually: {url}" if isinstance(url, str) and url else " Inspect the entry and connect with its native protocol."
    return f"Unsupported ARD media type for automatic install: {ard_entry_media_type(entry)}.{guidance}"


def command_install_legacy(args: argparse.Namespace) -> None:
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
    else:
        installed_from = install_from_github_source(capability, dest, args.force)
        if not installed_from:
            raise SystemExit("Package did not contain SKILL.md and no supported source fallback was available")

    skill_name = installed_skill_name(dest)
    if args.json_output:
        print_json(
            {
                "registry": base,
                "api": "legacy",
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


def command_install(args: argparse.Namespace) -> None:
    if selected_registry_api(args) == "legacy":
        command_install_legacy(args)
        return

    base = registry_base(args)
    entry = resolve_ard_entry_for_install(base, args.ref)
    media_type = ard_entry_media_type(entry)
    dest = resolve_install_dest(args, ard_entry_install_name(entry, args.ref))
    if not args.json_output:
        print_ard_trust_summary(entry)

    checksum: str | None = None
    if media_type == "application/vnd.capelry.skill+zip":
        installed_from, checksum = install_ard_zip_entry(entry, dest, args.force)
    elif media_type == "application/vnd.capelry.skill-source+json":
        installed_from = install_ard_source_entry(entry, dest, args.force)
    else:
        raise SystemExit(unsupported_ard_install_message(entry))

    skill_name = installed_skill_name(dest)
    result = {
        "registry": base,
        "api": "ard",
        "ref": args.ref,
        "identifier": entry.get("identifier"),
        "mediaType": media_type,
        "trustState": ard_trust_state(entry),
        "destination": str(dest),
        "installedFrom": installed_from,
        "skillName": skill_name,
        "next": f"reload or restart your agent; in Pi run /reload and then /skill:{skill_name}",
    }
    if checksum:
        result["checksumSha256"] = checksum
    if args.json_output:
        print_json(result)
        return

    print(f"Installed {entry.get('identifier', args.ref)} to {dest}")
    print(f"source: {installed_from}")
    print("Next: reload or restart your agent. In Pi, run /reload and then /skill:" + skill_name)


def strip_yaml_scalar(value: str) -> str:
    value = value.strip()
    if " #" in value:
        value = value.split(" #", 1)[0].strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def yaml_section_value(text: str, section: str, key: str) -> str | None:
    in_section = False
    section_pattern = re.compile(rf"^{re.escape(section)}:\s*$")
    key_pattern = re.compile(rf"^\s+{re.escape(key)}:\s*(?P<value>.*?)\s*$")

    for line in text.splitlines():
        if section_pattern.match(line):
            in_section = True
            continue
        if in_section:
            if line and not line.startswith((" ", "\t")):
                break
            match = key_pattern.match(line)
            if match:
                return strip_yaml_scalar(match.group("value"))
    return None


def self_skill_dir() -> Path:
    return Path(__file__).resolve().parents[1]


def self_manifest_text(skill_dir: Path) -> str:
    manifest = skill_dir / "capability.yaml"
    try:
        return manifest.read_text(encoding="utf-8")
    except OSError as error:
        raise SystemExit(f"Unable to read {manifest}: {error}") from error


def self_manifest_value(skill_dir: Path, section: str, key: str) -> str | None:
    return yaml_section_value(self_manifest_text(skill_dir), section, key)


def self_local_version(skill_dir: Path) -> str:
    return self_manifest_value(skill_dir, "metadata", "version") or "unknown"


def split_github_slug(slug: str) -> tuple[str, str]:
    owner, _, repo = slug.partition("/")
    if not owner or not repo:
        raise SystemExit(f"Invalid GitHub repository slug: {slug}")
    return owner, repo


def semver_tuple(version: str) -> tuple[int, int, int] | None:
    match = re.match(r"^v?(\d+)\.(\d+)\.(\d+)(?:[-+].*)?$", version.strip())
    if not match:
        return None
    return tuple(int(part) for part in match.groups())


def is_self_release_tag(value: str) -> bool:
    return bool(re.match(r"^v\d+\.\d+\.\d+$", value.strip()))


def latest_self_ref() -> dict[str, str | None]:
    """Return the highest stable vX.X.X GitHub release/tag for this skill."""
    owner, repo = split_github_slug(SELF_GITHUB_REPOSITORY)
    candidates: list[dict[str, str | None]] = []

    releases = fetch_github_json(f"https://api.github.com/repos/{owner}/{repo}/releases?per_page=50", allow_404=True)
    if isinstance(releases, list):
        for release in releases:
            if not isinstance(release, dict) or release.get("draft") or release.get("prerelease"):
                continue
            tag = release.get("tag_name")
            if isinstance(tag, str) and is_self_release_tag(tag):
                candidates.append(
                    {
                        "ref": tag.strip(),
                        "source": "github-release",
                        "url": release.get("html_url") if isinstance(release.get("html_url"), str) else None,
                    }
                )

    tags = fetch_github_json(f"https://api.github.com/repos/{owner}/{repo}/tags?per_page=100", allow_404=True)
    if isinstance(tags, list):
        known_refs = {candidate["ref"] for candidate in candidates}
        for entry in tags:
            tag = entry.get("name") if isinstance(entry, dict) else None
            if isinstance(tag, str) and is_self_release_tag(tag) and tag.strip() not in known_refs:
                candidates.append(
                    {
                        "ref": tag.strip(),
                        "source": "github-tag",
                        "url": f"https://github.com/{SELF_GITHUB_REPOSITORY}/releases/tag/{urllib.parse.quote(tag.strip())}",
                    }
                )

    if candidates:
        return max(candidates, key=lambda item: semver_tuple(str(item["ref"])) or (-1, -1, -1))

    return {
        "ref": SELF_DEFAULT_REF,
        "source": "default-branch",
        "url": f"https://github.com/{SELF_GITHUB_REPOSITORY}/tree/{SELF_DEFAULT_REF}",
    }


def remote_self_manifest(ref: str) -> str:
    owner, repo = split_github_slug(SELF_GITHUB_REPOSITORY)
    manifest_path = f"{SELF_SOURCE_PATH}/capability.yaml"
    archive_error: BaseException | None = None
    try:
        return github_archive_file_bytes(owner, repo, manifest_path, ref).decode("utf-8")
    except (SystemExit, zipfile.BadZipFile) as error:
        archive_error = error

    try:
        payload = fetch_github_json(github_api_url(owner, repo, manifest_path, ref))
        if not isinstance(payload, dict) or payload.get("type") != "file" or not isinstance(payload.get("download_url"), str):
            raise SystemExit(f"Could not read capability.yaml from {SELF_GITHUB_REPOSITORY}@{ref}")
        return fetch_github_bytes(payload["download_url"]).decode("utf-8")
    except SystemExit as error:
        raise SystemExit(f"{error}\n\nGitHub archive manifest fallback also failed:\n{archive_error}") from error


def remote_self_version(ref: str) -> str:
    version = yaml_section_value(remote_self_manifest(ref), "metadata", "version")
    if not version:
        raise SystemExit(f"Remote capability.yaml at {SELF_GITHUB_REPOSITORY}@{ref} did not declare metadata.version")
    return version


def version_status(local_version: str, remote_version: str) -> str:
    if local_version == remote_version:
        return "current"
    local_semver = semver_tuple(local_version)
    remote_semver = semver_tuple(remote_version)
    if local_semver and remote_semver:
        if local_semver < remote_semver:
            return "update-available"
        if local_semver > remote_semver:
            return "local-newer"
        return "current"
    return "different"


def self_update_info(ref_override: str | None = None) -> dict[str, Any]:
    skill_dir = self_skill_dir()
    latest = (
        {
            "ref": ref_override,
            "source": "explicit-ref",
            "url": f"https://github.com/{SELF_GITHUB_REPOSITORY}/tree/{urllib.parse.quote(ref_override)}",
        }
        if ref_override
        else latest_self_ref()
    )
    ref = latest["ref"]
    if not isinstance(ref, str) or not ref:
        raise SystemExit("Unable to determine a GitHub ref for Capelry self-update")
    local_version = self_local_version(skill_dir)
    remote_version = remote_self_version(ref)
    return {
        "skillDir": str(skill_dir),
        "repository": f"https://github.com/{SELF_GITHUB_REPOSITORY}",
        "sourcePath": SELF_SOURCE_PATH,
        "localVersion": local_version,
        "remoteVersion": remote_version,
        "remoteRef": ref,
        "remoteRefSource": latest.get("source"),
        "remoteUrl": latest.get("url"),
        "status": version_status(local_version, remote_version),
    }


def print_self_update_info(info: dict[str, Any]) -> None:
    print(f"Capelry skill version: {info['localVersion']}")
    print(f"installed at: {info['skillDir']}")
    print(f"latest GitHub ref: {info['remoteRef']} ({info['remoteRefSource']})")
    print(f"latest skill version: {info['remoteVersion']}")
    print(f"status: {info['status']}")
    if info.get("remoteUrl"):
        print(f"release: {info['remoteUrl']}")
    if info["status"] == "update-available":
        print(f"update: {script_invocation()} self-update --yes")


def command_version(args: argparse.Namespace) -> None:
    info = self_update_info(args.ref)
    if args.json_output:
        print_json(info)
    else:
        print_self_update_info(info)
    if args.check and info["status"] == "update-available":
        raise SystemExit(1)


def confirm_self_update(args: argparse.Namespace, info: dict[str, Any]) -> None:
    if args.yes or args.dry_run:
        return
    if not sys.stdin.isatty():
        raise SystemExit("Refusing non-interactive self-update without --yes")
    answer = input(
        f"Replace {info['skillDir']} with Capelry {info['remoteVersion']} from {info['remoteRef']}? [y/N] "
    ).strip().lower()
    if answer not in {"y", "yes"}:
        raise SystemExit("Self-update cancelled")


def validate_downloaded_self_skill(dest: Path) -> None:
    required = ["SKILL.md", "capability.yaml", "scripts/capelry.py", "scripts/bootstrap.py"]
    missing = [item for item in required if not (dest / item).exists()]
    if missing:
        raise SystemExit("Downloaded Capelry skill is incomplete; missing: " + ", ".join(missing))


def remove_path(path: Path) -> None:
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
    else:
        path.unlink(missing_ok=True)


def backup_path_for(dest: Path) -> Path:
    stamp = int(time.time())
    candidate = dest.parent / f".{dest.name}.backup-{stamp}"
    index = 1
    while candidate.exists():
        candidate = dest.parent / f".{dest.name}.backup-{stamp}-{index}"
        index += 1
    return candidate


def replace_skill_dir(dest: Path, new_dir: Path, *, keep_backup: bool) -> Path | None:
    backup: Path | None = None
    if dest.exists():
        backup = backup_path_for(dest)
        dest.rename(backup)
    try:
        shutil.move(str(new_dir), str(dest))
    except Exception:
        if dest.exists():
            remove_path(dest)
        if backup and backup.exists():
            backup.rename(dest)
        raise
    if backup and backup.exists() and not keep_backup:
        shutil.rmtree(backup)
        return None
    return backup


def source_checkout_root(skill_dir: Path) -> Path | None:
    for parent in skill_dir.parents:
        if (parent / ".git").exists() and (parent / SELF_SOURCE_PATH).resolve() == skill_dir:
            return parent
    return None


def command_self_update(args: argparse.Namespace) -> None:
    info = self_update_info(args.ref)
    if info["status"] != "update-available" and not args.force:
        message = "already current" if info["status"] == "current" else "remote ref is not newer"
        if args.json_output:
            print_json({**info, "updated": False, "message": message})
        else:
            print_self_update_info(info)
            print(f"No update applied: {message}. Use --force to install from GitHub anyway.")
        return

    confirm_self_update(args, info)
    if args.dry_run:
        if args.json_output:
            print_json({**info, "updated": False, "dryRun": True})
        else:
            print_self_update_info(info)
            print("Dry run only; no files changed.")
        return

    skill_dir = Path(info["skillDir"])
    checkout_root = source_checkout_root(skill_dir)
    if checkout_root and not args.allow_source_checkout:
        raise SystemExit(
            f"Refusing to self-update source checkout at {checkout_root}. "
            "Use git to update the repository, or pass --allow-source-checkout if you really want to replace it."
        )

    owner, repo = split_github_slug(SELF_GITHUB_REPOSITORY)
    with tempfile.TemporaryDirectory(prefix="capelry-self-update-") as temp_root:
        candidate = Path(temp_root) / "capelry"
        archive_error: BaseException | None = None
        try:
            download_github_archive_path(owner, repo, SELF_SOURCE_PATH, str(info["remoteRef"]), candidate, force=True)
        except (SystemExit, zipfile.BadZipFile) as error:
            archive_error = error
            shutil.rmtree(candidate, ignore_errors=True)
            candidate.mkdir(parents=True, exist_ok=True)
            try:
                download_github_path(owner, repo, SELF_SOURCE_PATH, str(info["remoteRef"]), candidate, SELF_SOURCE_PATH)
            except SystemExit as api_error:
                shutil.rmtree(candidate, ignore_errors=True)
                raise SystemExit(f"{api_error}\n\nGitHub archive self-update download also failed:\n{archive_error}") from api_error
        validate_downloaded_self_skill(candidate)
        backup = replace_skill_dir(skill_dir, candidate, keep_backup=args.keep_backup)

    result = {**info, "updated": True, "backup": str(backup) if backup else None}
    if args.json_output:
        print_json(result)
        return

    print(f"Updated Capelry skill to {info['remoteVersion']} from {info['remoteRef']}.")
    if backup:
        print(f"backup: {backup}")
    print("Next: reload or restart your agent. In Pi, run /reload and then /skill:capelry")


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
    parser = argparse.ArgumentParser(description="Search, inspect, install, and update capabilities from Capelry")
    parser.add_argument("--registry", help=f"Registry base URL (default: {DEFAULT_REGISTRY} or CAPELRY_REGISTRY_URL)")
    parser.add_argument("--json", dest="json_output", action="store_true", help="Emit machine-readable JSON output")
    parser.set_defaults(json_output=False)
    subparsers = parser.add_subparsers(dest="command", required=True)

    search = subparsers.add_parser("search", help="Search capabilities")
    search.add_argument("query")
    search.add_argument("--limit", type=int, default=20)
    search.add_argument("--expand", action="store_true", help="Search related terms when an exact phrase is too narrow")
    search.add_argument(
        "--api",
        choices=("legacy", "ard"),
        help="Registry API to use (default: ard; CAPELRY_USE_LEGACY_API=1 selects legacy)",
    )
    search.add_argument("--type", dest="package_type", help="Filter by package type, e.g. skill, agent, prompt")
    search.add_argument("--media-type", action="append", help="ARD media type filter; repeat or comma-separate values")
    search.add_argument("--publisher", action="append", help="ARD publisher filter; repeat or comma-separate values")
    search.add_argument("--trust-state", action="append", help="ARD trust-state filter; repeat or comma-separate values")
    search.add_argument("--filter", dest="ard_filter", action="append", help="Generic ARD filter FIELD=VALUE; repeat or comma-separate values")
    search.add_argument("--federation", choices=("none", "referrals", "auto"), default="none", help="ARD federation mode")
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
    discover.add_argument(
        "--api",
        choices=("legacy", "ard"),
        help="Registry API to use (default: ard; CAPELRY_USE_LEGACY_API=1 selects legacy)",
    )
    discover.add_argument("--type", dest="package_type", default="skill", help="Filter by package type (default: skill)")
    discover.add_argument("--media-type", action="append", help="ARD media type filter; repeat or comma-separate values")
    discover.add_argument("--publisher", action="append", help="ARD publisher filter; repeat or comma-separate values")
    discover.add_argument("--trust-state", action="append", help="ARD trust-state filter; repeat or comma-separate values")
    discover.add_argument("--filter", dest="ard_filter", action="append", help="Generic ARD filter FIELD=VALUE; repeat or comma-separate values")
    discover.add_argument("--federation", choices=("none", "referrals", "auto"), default="none", help="ARD federation mode")
    discover.add_argument("--status", default="passed", help="Filter by validation status (default: passed)")
    discover.add_argument("--source", help="Filter by source repository, e.g. github/awesome-copilot")
    discover.add_argument("--domain", help="Filter by derived domain facet, e.g. devops, docker, sre")
    discover.add_argument("--phase", help="Filter by lifecycle facet, e.g. production, preflight, observability")
    add_install_snippet_argument(discover, default="pi-project")
    add_json_argument(discover)
    discover.set_defaults(func=command_discover)

    info = subparsers.add_parser("info", help="Show capability or ARD entry details")
    info.add_argument("ref", help="namespace/name or urn:ai:...")
    info.add_argument(
        "--api",
        choices=("legacy", "ard"),
        help="Registry API to use (default: ard; CAPELRY_USE_LEGACY_API=1 selects legacy)",
    )
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

    install = subparsers.add_parser("install", help="Install a supported skill from an ARD entry or legacy capability")
    install.add_argument("ref", help="urn:ai:... or legacy namespace/name; namespace/name@version only with --api legacy")
    install.add_argument(
        "--api",
        choices=("legacy", "ard"),
        help="Registry API to use (default: ard; CAPELRY_USE_LEGACY_API=1 selects legacy)",
    )
    install.add_argument("--version", help="Legacy version override")
    install.add_argument("--target", choices=sorted(TARGET_ROOTS), default="agents-project")
    install.add_argument("--dest", help="Exact destination directory")
    install.add_argument("--name", help="Install directory name override")
    install.add_argument("--force", action="store_true", help="Replace an existing destination")
    add_json_argument(install)
    install.set_defaults(func=command_install)

    version = subparsers.add_parser(
        "version",
        aliases=["check-update"],
        help="Show this Capelry skill version and the latest GitHub vX.X.X release/tag",
    )
    version.add_argument("--ref", help="Compare against a specific GitHub ref or tag, e.g. v1.1.0")
    version.add_argument("--check", action="store_true", help="Exit with code 1 when an update is available")
    add_json_argument(version)
    version.set_defaults(func=command_version)

    self_update = subparsers.add_parser(
        "self-update",
        aliases=["update", "upgrade"],
        help="Replace this installed Capelry skill with the latest GitHub vX.X.X release/tag",
    )
    self_update.add_argument("--ref", help="Install a specific GitHub ref or tag, e.g. v1.1.0")
    self_update.add_argument("--yes", "-y", action="store_true", help="Skip confirmation for non-interactive updates")
    self_update.add_argument("--dry-run", action="store_true", help="Show what would change without writing files")
    self_update.add_argument("--force", action="store_true", help="Reinstall even when the remote ref is not newer")
    self_update.add_argument("--keep-backup", action="store_true", help="Keep the previous skill directory as a backup")
    self_update.add_argument(
        "--allow-source-checkout",
        action="store_true",
        help="Allow replacing a checked-out capelry-skills source tree; normally use git instead",
    )
    add_json_argument(self_update)
    self_update.set_defaults(func=command_self_update)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

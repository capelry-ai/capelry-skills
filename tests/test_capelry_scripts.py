from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
import threading
import unittest
import urllib.parse
import urllib.request
import zipfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
CAPELRY_SCRIPT = ROOT / "skills" / "capelry" / "scripts" / "capelry.py"
BOOTSTRAP_SCRIPT = ROOT / "skills" / "capelry" / "scripts" / "bootstrap.py"
SELF_CATALOG = ROOT / "skills" / "capelry" / "ai-catalog.json"
WELL_KNOWN_CATALOG = ROOT / ".well-known" / "ai-catalog.json"
SELF_CAPABILITY = ROOT / "skills" / "capelry" / "capability.yaml"
README = ROOT / "README.md"
BOOTSTRAP_DOC = ROOT / "skills" / "capelry" / "BOOTSTRAP.md"
HARNESS_REFERENCE = ROOT / "skills" / "capelry" / "references" / "harnesses.md"


def clean_env(**overrides: str) -> dict[str, str]:
    env = os.environ.copy()
    for key in ("CAPELRY_REGISTRY_URL", "CAPELRY_USER_AGENT", "CAPELRY_USER_AGENT_SUFFIX"):
        env.pop(key, None)
    env.update(overrides)
    return env


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RegistryFixtureHandler(BaseHTTPRequestHandler):
    unexpected_requests: list[str] = []
    ard_requests: list[dict[str, object]] = []
    agents_requests: list[str] = []
    request_user_agents: list[str] = []

    def log_message(self, _format: str, *_args: object) -> None:
        return

    def send_json(self, payload: object, status: int = 200) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_bytes(self, payload: bytes, content_type: str = "application/octet-stream", status: int = 200) -> None:
        self.send_response(status)
        self.send_header("content-type", content_type)
        self.send_header("content-length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def fixture_base(self) -> str:
        return f"http://{self.headers['Host']}"

    @staticmethod
    def zip_bytes(entries: dict[str, str]) -> bytes:
        archive = io.BytesIO()
        with zipfile.ZipFile(archive, "w") as zf:
            for name, content in entries.items():
                member = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
                zf.writestr(member, content)
        return archive.getvalue()

    @staticmethod
    def skill_md(name: str, description: str | None = None) -> str:
        description = description or f"Fixture instructions for {name}. Use when testing Capelry skill installation."
        return f"---\nname: {name}\ndescription: {description}\n---\n\n# {name}\n\nFollow the fixture instructions.\n"

    @classmethod
    def good_skill_zip(cls) -> bytes:
        return cls.zip_bytes({"SKILL.md": cls.skill_md("zip-skill")})

    @classmethod
    def unsafe_skill_zip(cls) -> bytes:
        return cls.zip_bytes({"../evil/SKILL.md": cls.skill_md("evil")})

    @classmethod
    def backslash_unsafe_skill_zip(cls) -> bytes:
        return cls.zip_bytes({"..\\evil\\SKILL.md": cls.skill_md("evil")})

    @classmethod
    def invalid_skill_zip(cls) -> bytes:
        return cls.zip_bytes({"SKILL.md": "---\nname: invalid-skill\n---\n\n# Missing description\n"})

    @classmethod
    def malformed_yaml_skill_zip(cls) -> bytes:
        return cls.zip_bytes(
            {
                "SKILL.md": (
                    '---\nname: malformed-yaml\ndescription: "valid"\n'
                    "  invalid continuation\n---\n\n# Malformed YAML\n"
                )
            }
        )

    @classmethod
    def malformed_single_quote_skill_zip(cls) -> bytes:
        return cls.zip_bytes(
            {
                "SKILL.md": (
                    "---\nname: malformed-single-quote\ndescription: 'it's useful'\n"
                    "---\n\n# Malformed single quote\n"
                )
            }
        )

    @classmethod
    def compatibility_sequence_skill_zip(cls) -> bytes:
        return cls.zip_bytes(
            {
                "SKILL.md": (
                    "---\nname: compatibility-sequence\ndescription: Fixture. Use for schema validation.\n"
                    "compatibility:\n  - linux\n---\n\n# Compatibility sequence\n"
                )
            }
        )

    @classmethod
    def invalid_block_indent_skill_zip(cls) -> bytes:
        return cls.zip_bytes(
            {
                "SKILL.md": (
                    "---\nname: invalid-block-indent\ndescription: |\n  good\n bad\n"
                    "---\n\n# Invalid block indentation\n"
                )
            }
        )

    @classmethod
    def forbidden_prefix_skill_zip(cls) -> bytes:
        return cls.zip_bytes(
            {"SKILL.md": "---\nname: forbidden-prefix\ndescription: @foo\n---\n\n# Forbidden prefix\n"}
        )

    @classmethod
    def metadata_sequence_skill_zip(cls) -> bytes:
        return cls.zip_bytes(
            {
                "SKILL.md": (
                    "---\nname: metadata-sequence\ndescription: Fixture. Use for metadata validation.\n"
                    "metadata:\n  - owner: fixture\n---\n\n# Metadata sequence\n"
                )
            }
        )

    @classmethod
    def mismatched_skill_zip(cls) -> bytes:
        return cls.zip_bytes({"SKILL.md": cls.skill_md("redirected-skill")})

    @classmethod
    def source_skill_zip(cls) -> bytes:
        return cls.zip_bytes({"repo-fixture/skills/source-skill/SKILL.md": cls.skill_md("source-skill")})

    def ard_entry(self, score: int | None = None, kind: str = "default") -> dict[str, object]:
        base = self.fixture_base()
        entry: dict[str, object] = {
            "identifier": "urn:air:github.com:capelry-ai:capelry-skills:demo-skill",
            "version": "1.0.0",
            "displayName": "Demo ARD Skill",
            "type": "application/vnd.capelry.skill-source+json",
            "url": "https://github.com/capelry-ai/capelry-skills",
            "description": "Fixture skill returned by ARD.",
            "source": "http://fixture-registry.test",
            "metadata": {
                "com.capelry.packageType": "skill",
                "com.capelry.trustState": "source-hosted",
                "com.capelry.slug": "capelry-ai/capelry-skills/demo-skill",
                "com.capelry.catalogPath": "capelry-ai/capelry-skills",
                "com.capelry.catalogSlug": "capelry-skills",
                "com.capelry.catalogUrl": "https://github.com/capelry-ai/capelry-skills",
                "com.capelry.sourceRepository": "https://github.com/capelry-ai/capelry-skills",
                "com.capelry.sourceRepositoryFullName": "capelry-ai/capelry-skills",
            },
            "trustManifest": {
                "identity": "urn:air:github.com:capelry-ai:capelry-skills:demo-skill",
                "identityType": "other",
                "provenance": [{"relation": "publishedFrom", "sourceId": "https://github.com/capelry-ai/capelry-skills"}],
            },
        }
        if kind == "zip":
            archive = self.good_skill_zip()
            entry.update(
                {
                    "identifier": "urn:air:example.com:skills:zip-skill",
                    "displayName": "Zip Skill",
                    "type": "application/vnd.capelry.skill+zip",
                    "url": f"{base}/archives/good.zip",
                    "metadata": {
                        "com.capelry.packageType": "skill",
                        "com.capelry.trustState": "checksum-only",
                        "com.capelry.slug": "capelry-ai/capelry-skills/zip-skill",
                        "com.capelry.catalogPath": "capelry-ai/capelry-skills",
                        "com.capelry.catalogSlug": "capelry-skills",
                        "com.capelry.archiveUrl": f"{base}/archives/good.zip",
                        "com.capelry.archiveChecksumSha256": hashlib.sha256(archive).hexdigest(),
                    },
                }
            )
        elif kind == "bad-checksum":
            entry.update(
                {
                    "identifier": "urn:air:example.com:skills:bad-checksum",
                    "displayName": "Bad Checksum Skill",
                    "type": "application/vnd.capelry.skill+zip",
                    "url": f"{base}/archives/good.zip",
                    "metadata": {
                        "com.capelry.packageType": "skill",
                        "com.capelry.trustState": "checksum-only",
                        "com.capelry.slug": "capelry-ai/capelry-skills/bad-checksum",
                        "com.capelry.catalogPath": "capelry-ai/capelry-skills",
                        "com.capelry.catalogSlug": "capelry-skills",
                        "com.capelry.archiveUrl": f"{base}/archives/good.zip",
                        "com.capelry.archiveChecksumSha256": "0" * 64,
                    },
                }
            )
        elif kind in {
            "unsafe",
            "backslash-unsafe",
            "invalid",
            "malformed-yaml",
            "malformed-single-quote",
            "compatibility-sequence",
            "invalid-block-indent",
            "forbidden-prefix",
            "metadata-sequence",
            "mismatched",
        }:
            archive_name = {
                "unsafe": "unsafe.zip",
                "backslash-unsafe": "backslash-unsafe.zip",
                "invalid": "invalid.zip",
                "malformed-yaml": "malformed-yaml.zip",
                "malformed-single-quote": "malformed-single-quote.zip",
                "compatibility-sequence": "compatibility-sequence.zip",
                "invalid-block-indent": "invalid-block-indent.zip",
                "forbidden-prefix": "forbidden-prefix.zip",
                "metadata-sequence": "metadata-sequence.zip",
                "mismatched": "mismatched.zip",
            }[kind]
            archive_bytes = {
                "unsafe": self.unsafe_skill_zip(),
                "backslash-unsafe": self.backslash_unsafe_skill_zip(),
                "invalid": self.invalid_skill_zip(),
                "malformed-yaml": self.malformed_yaml_skill_zip(),
                "malformed-single-quote": self.malformed_single_quote_skill_zip(),
                "compatibility-sequence": self.compatibility_sequence_skill_zip(),
                "invalid-block-indent": self.invalid_block_indent_skill_zip(),
                "forbidden-prefix": self.forbidden_prefix_skill_zip(),
                "metadata-sequence": self.metadata_sequence_skill_zip(),
                "mismatched": self.mismatched_skill_zip(),
            }[kind]
            slug = {
                "unsafe": "unsafe-zip",
                "backslash-unsafe": "backslash-unsafe",
                "invalid": "invalid-skill",
                "malformed-yaml": "malformed-yaml",
                "malformed-single-quote": "malformed-single-quote",
                "compatibility-sequence": "compatibility-sequence",
                "invalid-block-indent": "invalid-block-indent",
                "forbidden-prefix": "forbidden-prefix",
                "metadata-sequence": "metadata-sequence",
                "mismatched": "planned-skill",
            }[kind]
            entry.update(
                {
                    "identifier": f"urn:air:example.com:skills:{slug}",
                    "displayName": f"{slug} fixture",
                    "type": "application/vnd.capelry.skill+zip",
                    "url": f"{base}/archives/{archive_name}",
                    "metadata": {
                        "com.capelry.packageType": "skill",
                        "com.capelry.trustState": "checksum-only",
                        "com.capelry.slug": f"capelry-ai/capelry-skills/{slug}",
                        "com.capelry.catalogPath": "capelry-ai/capelry-skills",
                        "com.capelry.catalogSlug": "capelry-skills",
                        "com.capelry.archiveUrl": f"{base}/archives/{archive_name}",
                        "com.capelry.archiveChecksumSha256": hashlib.sha256(archive_bytes).hexdigest(),
                    },
                }
            )
        elif kind == "source":
            entry.update(
                {
                    "identifier": "urn:air:example.com:skills:source-skill",
                    "displayName": "Source Skill",
                    "type": "application/vnd.capelry.skill-source+json",
                    "data": {
                        "repository": "https://github.com/example/source-skill",
                        "path": "skills/source-skill",
                        "ref": "fixture-ref",
                        "archiveUrl": f"{base}/archives/source.zip",
                    },
                    "metadata": {
                        "com.capelry.packageType": "skill",
                        "com.capelry.trustState": "source-hosted",
                        "com.capelry.slug": "capelry-ai/capelry-skills/source-skill",
                        "com.capelry.catalogPath": "capelry-ai/capelry-skills",
                        "com.capelry.catalogSlug": "capelry-skills",
                    },
                }
            )
        elif kind == "unsupported":
            entry.update(
                {
                    "identifier": "urn:air:example.com:apis:demo",
                    "displayName": "Demo API",
                    "type": "application/openapi+json",
                    "url": f"{base}/openapi.json",
                    "metadata": {
                        "com.capelry.trustState": "unsigned",
                        "com.capelry.slug": "capelry-ai/capelry-skills/unsupported",
                        "com.capelry.catalogPath": "capelry-ai/capelry-skills",
                        "com.capelry.catalogSlug": "capelry-skills",
                    },
                }
            )
        if score is not None:
            entry["score"] = score
        return entry

    def do_GET(self) -> None:  # noqa: N802 - stdlib handler hook
        self.request_user_agents.append(self.headers.get("User-Agent", ""))
        if self.path == "/archives/good.zip":
            self.send_bytes(self.good_skill_zip(), "application/zip")
            return
        if self.path == "/archives/unsafe.zip":
            self.send_bytes(self.unsafe_skill_zip(), "application/zip")
            return
        if self.path == "/archives/backslash-unsafe.zip":
            self.send_bytes(self.backslash_unsafe_skill_zip(), "application/zip")
            return
        if self.path == "/archives/invalid.zip":
            self.send_bytes(self.invalid_skill_zip(), "application/zip")
            return
        if self.path == "/archives/malformed-yaml.zip":
            self.send_bytes(self.malformed_yaml_skill_zip(), "application/zip")
            return
        if self.path == "/archives/malformed-single-quote.zip":
            self.send_bytes(self.malformed_single_quote_skill_zip(), "application/zip")
            return
        if self.path == "/archives/compatibility-sequence.zip":
            self.send_bytes(self.compatibility_sequence_skill_zip(), "application/zip")
            return
        if self.path == "/archives/invalid-block-indent.zip":
            self.send_bytes(self.invalid_block_indent_skill_zip(), "application/zip")
            return
        if self.path == "/archives/forbidden-prefix.zip":
            self.send_bytes(self.forbidden_prefix_skill_zip(), "application/zip")
            return
        if self.path == "/archives/metadata-sequence.zip":
            self.send_bytes(self.metadata_sequence_skill_zip(), "application/zip")
            return
        if self.path == "/archives/mismatched.zip":
            self.send_bytes(self.mismatched_skill_zip(), "application/zip")
            return
        if self.path == "/archives/source.zip":
            self.send_bytes(self.source_skill_zip(), "application/zip")
            return

        if self.path.startswith("/agents?"):
            self.agents_requests.append(self.path)
            parsed = urllib.parse.urlparse(self.path)
            filter_value = urllib.parse.parse_qs(parsed.query).get("filter", [""])[0]
            kind = "default"
            if "zip-skill" in filter_value:
                kind = "zip"
            elif "bad-checksum" in filter_value:
                kind = "bad-checksum"
            elif "backslash-unsafe" in filter_value:
                kind = "backslash-unsafe"
            elif "unsafe-zip" in filter_value:
                kind = "unsafe"
            elif "invalid-skill" in filter_value:
                kind = "invalid"
            elif "malformed-yaml" in filter_value:
                kind = "malformed-yaml"
            elif "malformed-single-quote" in filter_value:
                kind = "malformed-single-quote"
            elif "compatibility-sequence" in filter_value:
                kind = "compatibility-sequence"
            elif "invalid-block-indent" in filter_value:
                kind = "invalid-block-indent"
            elif "forbidden-prefix" in filter_value:
                kind = "forbidden-prefix"
            elif "metadata-sequence" in filter_value:
                kind = "metadata-sequence"
            elif "planned-skill" in filter_value:
                kind = "mismatched"
            elif "source-skill" in filter_value:
                kind = "source"
            elif "unsupported" in filter_value:
                kind = "unsupported"
            self.send_json({"items": [self.ard_entry(kind=kind)], "total": 1})
            return

        self.unexpected_requests.append(self.path)
        self.send_json({"error": "not found"}, status=404)

    def do_POST(self) -> None:  # noqa: N802 - stdlib handler hook
        self.request_user_agents.append(self.headers.get("User-Agent", ""))
        length = int(self.headers.get("content-length", "0"))
        raw_body = self.rfile.read(length) if length else b"{}"
        body = json.loads(raw_body.decode("utf-8"))

        if self.path == "/search":
            self.ard_requests.append(body)
            query = body.get("query") if isinstance(body, dict) else None
            if isinstance(query, dict) and query.get("text") == "bad-filter":
                self.send_json({"errorCode": "INVALID_ARGUMENT", "message": "bad ARD filter"}, status=400)
                return
            if isinstance(query, dict) and query.get("text") == "missing-ard":
                self.send_json({"errorCode": "NOT_FOUND", "message": "ARD search unavailable"}, status=404)
                return
            self.send_json({"results": [self.ard_entry(score=91)], "referrals": []})
            return

        if self.path == "/explore":
            self.ard_requests.append(body)
            self.send_json(
                {
                    "resultType": "facets",
                    "facets": {
                        "metadata.com.capelry.catalogPath": {
                            "buckets": [{"value": "capelry-ai/capelry-skills", "count": 3}],
                            "otherCount": 0,
                        },
                        "type": {
                            "buckets": [{"value": "application/vnd.capelry.skill-source+json", "count": 1}],
                            "otherCount": 0,
                        },
                    },
                }
            )
            return

        self.send_json({"error": "not found"}, status=404)


class RegistryFixture:
    def __enter__(self) -> "RegistryFixture":
        RegistryFixtureHandler.unexpected_requests = []
        RegistryFixtureHandler.ard_requests = []
        RegistryFixtureHandler.agents_requests = []
        RegistryFixtureHandler.request_user_agents = []
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), RegistryFixtureHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        return self

    def __exit__(self, *_exc: object) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)

    @property
    def url(self) -> str:
        host, port = self.server.server_address
        return f"http://{host}:{port}"


class CapelryScriptTests(unittest.TestCase):
    def test_api_selector_flag_is_no_longer_accepted(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(CAPELRY_SCRIPT),
                "search",
                "skill",
                "--api",
                "ard",
            ],
            text=True,
            capture_output=True,
            env=clean_env(),
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unrecognized arguments: --api", result.stderr)

    def test_fixture_server_emulates_ard_search_endpoint(self) -> None:
        with RegistryFixture() as fixture:
            request = urllib.request.Request(
                f"{fixture.url}/search",
                data=json.dumps({"query": {"text": "skill"}, "federation": "none"}).encode("utf-8"),
                headers={"content-type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(request) as response:
                payload = json.loads(response.read().decode("utf-8"))

        self.assertEqual(
            payload["results"][0]["identifier"],
            "urn:air:github.com:capelry-ai:capelry-skills:demo-skill",
        )
        self.assertEqual(RegistryFixtureHandler.ard_requests[0]["federation"], "none")

    def test_requests_use_capelry_client_user_agent_by_default(self) -> None:
        with RegistryFixture() as fixture:
            subprocess.run(
                [
                    sys.executable,
                    str(CAPELRY_SCRIPT),
                    "--registry",
                    fixture.url,
                    "search",
                    "ard skill",
                ],
                check=True,
                text=True,
                capture_output=True,
                env=clean_env(),
            )

        self.assertEqual(RegistryFixtureHandler.request_user_agents[0], "capelry-client")

    def test_requests_include_custom_user_agent_suffix(self) -> None:
        with RegistryFixture() as fixture:
            subprocess.run(
                [
                    sys.executable,
                    str(CAPELRY_SCRIPT),
                    "--registry",
                    fixture.url,
                    "search",
                    "ard skill",
                ],
                check=True,
                text=True,
                capture_output=True,
                env=clean_env(CAPELRY_USER_AGENT_SUFFIX="test-client/1.0"),
            )

        self.assertEqual(RegistryFixtureHandler.request_user_agents[0], "capelry-client test-client/1.0")

    def test_requests_allow_full_custom_user_agent_override(self) -> None:
        with RegistryFixture() as fixture:
            subprocess.run(
                [
                    sys.executable,
                    str(CAPELRY_SCRIPT),
                    "--registry",
                    fixture.url,
                    "search",
                    "ard skill",
                ],
                check=True,
                text=True,
                capture_output=True,
                env=clean_env(CAPELRY_USER_AGENT="my-capelry-client/2.3"),
            )

        self.assertEqual(RegistryFixtureHandler.request_user_agents[0], "my-capelry-client/2.3")

    def test_ard_search_posts_pinned_payload_and_filters_without_legacy_fallback(self) -> None:
        with RegistryFixture() as fixture:
            result = subprocess.run(
                [
                    sys.executable,
                    str(CAPELRY_SCRIPT),
                    "--registry",
                    fixture.url,
                    "search",
                    "ard skill",
                    "--limit",
                    "5",
                    "--type",
                    "skill",
                    "--media-type",
                    "application/example+json",
                    "--publisher",
                    "github.com",
                    "--trust-state",
                    "source-hosted",
                    "--catalog",
                    "capelry-ai/capelry-skills",
                    "--source",
                    "capelry-ai/capelry-skills",
                    "--filter",
                    "tags=ard,skill",
                    "--json",
                ],
                check=True,
                text=True,
                capture_output=True,
                env=clean_env(),
            )

        payload = json.loads(result.stdout)
        self.assertEqual(payload["api"], "ard")
        self.assertEqual(payload["entries"][0]["identifier"], "urn:air:github.com:capelry-ai:capelry-skills:demo-skill")
        self.assertEqual(payload["entries"][0]["displayName"], "Demo ARD Skill")
        self.assertEqual(payload["entries"][0]["mediaType"], "application/vnd.capelry.skill-source+json")
        self.assertEqual(payload["entries"][0]["score"], 91)
        self.assertEqual(payload["entries"][0]["source"], "http://fixture-registry.test")
        self.assertEqual(payload["entries"][0]["sourceRepositoryFullName"], "capelry-ai/capelry-skills")
        self.assertEqual(payload["entries"][0]["catalogPath"], "capelry-ai/capelry-skills")
        self.assertEqual(payload["entries"][0]["page"], f"{fixture.url}/c/capelry-ai/capelry-skills/demo-skill")
        self.assertEqual(payload["entries"][0]["trustState"], "source-hosted")
        self.assertFalse(RegistryFixtureHandler.unexpected_requests)
        request = RegistryFixtureHandler.ard_requests[0]
        self.assertEqual(request["query"]["text"], "ard skill")
        self.assertEqual(request["federation"], "none")
        self.assertEqual(request["pageSize"], 5)
        filters = request["query"]["filter"]
        self.assertEqual(
            filters["type"],
            [
                "application/vnd.capelry.skill+zip",
                "application/vnd.capelry.skill-source+json",
                "application/example+json",
            ],
        )
        self.assertEqual(filters["publisher"], ["github.com"])
        self.assertEqual(filters["metadata.com.capelry.trustState"], ["source-hosted"])
        self.assertEqual(filters["metadata.com.capelry.catalogPath"], ["capelry-ai/capelry-skills"])
        self.assertEqual(filters["metadata.com.capelry.sourceRepositoryFullName"], ["capelry-ai/capelry-skills"])
        self.assertEqual(filters["tags"], ["ard", "skill"])

    def test_source_url_filter_preserves_exact_source_repository_field(self) -> None:
        with RegistryFixture() as fixture:
            subprocess.run(
                [
                    sys.executable,
                    str(CAPELRY_SCRIPT),
                    "--registry",
                    fixture.url,
                    "search",
                    "ard skill",
                    "--source",
                    "https://github.com/capelry-ai/capelry-skills",
                    "--json",
                ],
                check=True,
                text=True,
                capture_output=True,
                env=clean_env(),
            )

        filters = RegistryFixtureHandler.ard_requests[0]["query"]["filter"]
        self.assertEqual(filters["metadata.com.capelry.sourceRepository"], ["https://github.com/capelry-ai/capelry-skills"])
        self.assertNotIn("metadata.com.capelry.sourceRepositoryFullName", filters)

    def test_legacy_status_domain_phase_flags_are_not_sent_to_ard(self) -> None:
        with RegistryFixture() as fixture:
            result = subprocess.run(
                [
                    sys.executable,
                    str(CAPELRY_SCRIPT),
                    "--registry",
                    fixture.url,
                    "search",
                    "ard skill",
                    "--status",
                    "passed",
                    "--domain",
                    "devops",
                    "--phase",
                    "production",
                    "--json",
                ],
                check=True,
                text=True,
                capture_output=True,
                env=clean_env(),
            )

        self.assertIn("were not sent", result.stderr)
        request = RegistryFixtureHandler.ard_requests[0]
        filters = request.get("query", {}).get("filter", {})
        self.assertNotIn("metadata.com.capelry.validationStatus", filters)
        self.assertNotIn("metadata.com.capelry.domains", filters)
        self.assertNotIn("metadata.com.capelry.lifecyclePhases", filters)

    def test_explore_posts_catalog_facet_request(self) -> None:
        with RegistryFixture() as fixture:
            result = subprocess.run(
                [
                    sys.executable,
                    str(CAPELRY_SCRIPT),
                    "--registry",
                    fixture.url,
                    "explore",
                    "ard skill",
                    "--field",
                    "metadata.com.capelry.catalogPath,type",
                    "--limit",
                    "5",
                    "--catalog",
                    "capelry-ai/capelry-skills",
                    "--json",
                ],
                check=True,
                text=True,
                capture_output=True,
                env=clean_env(),
            )

        payload = json.loads(result.stdout)
        self.assertEqual(payload["api"], "ard")
        self.assertIn("metadata.com.capelry.catalogPath", payload["facets"])
        request = RegistryFixtureHandler.ard_requests[0]
        self.assertEqual(request["query"]["text"], "ard skill")
        self.assertEqual(request["query"]["filter"]["metadata.com.capelry.catalogPath"], ["capelry-ai/capelry-skills"])
        self.assertEqual(
            [facet["field"] for facet in request["resultType"]["facets"]],
            ["metadata.com.capelry.catalogPath", "type"],
        )

    def test_ard_error_shape_is_reported_clearly(self) -> None:
        with RegistryFixture() as fixture:
            result = subprocess.run(
                [
                    sys.executable,
                    str(CAPELRY_SCRIPT),
                    "--registry",
                    fixture.url,
                    "search",
                    "bad-filter",
                ],
                text=True,
                capture_output=True,
                env=clean_env(),
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("ARD INVALID_ARGUMENT", result.stderr)
        self.assertIn("bad ARD filter", result.stderr)
        self.assertFalse(RegistryFixtureHandler.unexpected_requests)

    def test_default_search_reports_ard_error_when_endpoint_is_missing(self) -> None:
        with RegistryFixture() as fixture:
            result = subprocess.run(
                [
                    sys.executable,
                    str(CAPELRY_SCRIPT),
                    "--registry",
                    fixture.url,
                    "search",
                    "missing-ard",
                    "--json",
                ],
                text=True,
                capture_output=True,
                env=clean_env(),
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("ARD NOT_FOUND", result.stderr)
        self.assertFalse(RegistryFixtureHandler.unexpected_requests)

    def test_ard_info_resolves_identifier_through_agents_endpoint(self) -> None:
        with RegistryFixture() as fixture:
            result = subprocess.run(
                [
                    sys.executable,
                    str(CAPELRY_SCRIPT),
                    "--registry",
                    fixture.url,
                    "info",
                    "urn:air:github.com:capelry-ai:capelry-skills:demo-skill",
                    "--json",
                ],
                check=True,
                text=True,
                capture_output=True,
                env=clean_env(),
            )

        payload = json.loads(result.stdout)
        self.assertEqual(payload["entry"]["mediaType"], "application/vnd.capelry.skill-source+json")
        self.assertFalse(RegistryFixtureHandler.unexpected_requests)
        self.assertTrue(RegistryFixtureHandler.agents_requests)
        query = urllib.parse.parse_qs(urllib.parse.urlparse(RegistryFixtureHandler.agents_requests[0]).query)
        self.assertIn("identifier", query["filter"][0])

    def test_ard_info_resolves_slug_through_metadata_alias_by_default(self) -> None:
        with RegistryFixture() as fixture:
            result = subprocess.run(
                [
                    sys.executable,
                    str(CAPELRY_SCRIPT),
                    "--registry",
                    fixture.url,
                    "info",
                    "capelry-ai/capelry-skills/demo-skill",
                    "--install-snippet",
                    "pi-project",
                    "--json",
                ],
                check=True,
                text=True,
                capture_output=True,
                env=clean_env(),
            )

        payload = json.loads(result.stdout)
        self.assertEqual(payload["entry"]["slug"], "capelry-ai/capelry-skills/demo-skill")
        self.assertEqual(payload["entry"]["catalogPath"], "capelry-ai/capelry-skills")
        self.assertEqual(payload["entry"]["page"], f"{fixture.url}/c/capelry-ai/capelry-skills/demo-skill")
        self.assertIn("install capelry-ai/capelry-skills/demo-skill --target pi-project", payload["entry"]["installSnippet"])
        self.assertFalse(RegistryFixtureHandler.unexpected_requests)
        query = urllib.parse.parse_qs(urllib.parse.urlparse(RegistryFixtureHandler.agents_requests[0]).query)
        self.assertIn("metadata.com.capelry.slug", query["filter"][0])

    def test_bulk_info_resolves_each_ref_with_ard_agents(self) -> None:
        with RegistryFixture() as fixture:
            result = subprocess.run(
                [
                    sys.executable,
                    str(CAPELRY_SCRIPT),
                    "--registry",
                    fixture.url,
                    "bulk-info",
                    "capelry-ai/capelry-skills/demo-skill",
                    "capelry-ai/capelry-skills/zip-skill",
                    "--json",
                ],
                check=True,
                text=True,
                capture_output=True,
                env=clean_env(),
            )

        payload = json.loads(result.stdout)
        self.assertEqual(payload["api"], "ard")
        self.assertEqual([item["slug"] for item in payload["shortlist"]], ["capelry-ai/capelry-skills/demo-skill", "capelry-ai/capelry-skills/zip-skill"])
        self.assertEqual(len(RegistryFixtureHandler.agents_requests), 2)
        self.assertFalse(RegistryFixtureHandler.unexpected_requests)

    def test_discover_uses_ard_search_by_default(self) -> None:
        with RegistryFixture() as fixture:
            result = subprocess.run(
                [
                    sys.executable,
                    str(CAPELRY_SCRIPT),
                    "--registry",
                    fixture.url,
                    "discover",
                    "demo skill",
                    "--no-expand",
                    "--top",
                    "1",
                    "--json",
                ],
                check=True,
                text=True,
                capture_output=True,
                env=clean_env(),
            )

        payload = json.loads(result.stdout)
        self.assertEqual(payload["api"], "ard")
        self.assertEqual(payload["entries"][0]["displayName"], "Demo ARD Skill")
        self.assertFalse(RegistryFixtureHandler.unexpected_requests)
        self.assertTrue(RegistryFixtureHandler.ard_requests)

    def test_three_segment_slug_install_name_uses_resource_segment(self) -> None:
        capelry = load_module("capelry_cli_install_name", CAPELRY_SCRIPT)
        entry = {
            "metadata": {"com.capelry.slug": "owner/catalog/resource-name"},
            "identifier": "urn:air:example.com:owner:catalog:resource-name",
        }

        self.assertEqual(capelry.ard_entry_install_name(entry, "owner/catalog/resource-name"), "resource-name")

    def test_cli_and_bootstrap_share_complete_harness_target_matrix(self) -> None:
        capelry = load_module("capelry_target_matrix", CAPELRY_SCRIPT)
        bootstrap = load_module("bootstrap_target_matrix", BOOTSTRAP_SCRIPT)

        self.assertEqual(capelry.TARGET_ROOTS, bootstrap.TARGET_SKILLS_DIRS)
        self.assertEqual(len(capelry.TARGET_ROOTS), 28)
        self.assertEqual(capelry.TARGET_ROOTS["codex-project"], ".agents/skills")
        self.assertEqual(capelry.TARGET_ROOTS["codex-global"], "~/.agents/skills")
        self.assertEqual(capelry.TARGET_ROOTS["opencode-global"], "~/.config/opencode/skills")
        self.assertEqual(capelry.TARGET_ROOTS["windsurf-global"], "~/.codeium/windsurf/skills")
        self.assertEqual(capelry.TARGET_ROOTS["copilot-project"], ".github/skills")
        for target in capelry.TARGET_ROOTS:
            self.assertTrue(target.endswith(("-project", "-global")))

    def test_documented_harness_matrix_covers_every_cli_target(self) -> None:
        capelry = load_module("capelry_documented_targets", CAPELRY_SCRIPT)
        readme = README.read_text(encoding="utf-8")
        bootstrap = BOOTSTRAP_DOC.read_text(encoding="utf-8")
        reference = HARNESS_REFERENCE.read_text(encoding="utf-8")

        for target, root in capelry.TARGET_ROOTS.items():
            self.assertIn(target, readme)
            self.assertIn(target, bootstrap)
            self.assertIn(target, reference)
            self.assertIn(root, reference)
        for official_url in (
            "https://agentskills.io/specification",
            "https://code.claude.com/docs/en/skills",
            "https://developers.openai.com/codex/skills",
            "https://opencode.ai/docs/skills/",
            "https://geminicli.com/docs/cli/skills/",
            "https://docs.github.com/en/copilot/concepts/agents/about-agent-skills",
        ):
            self.assertIn(official_url, reference)

    def test_targets_command_reports_harness_specific_paths(self) -> None:
        result = subprocess.run(
            [sys.executable, str(CAPELRY_SCRIPT), "targets", "--harness", "codex", "--json"],
            check=True,
            text=True,
            capture_output=True,
            env=clean_env(),
        )

        payload = json.loads(result.stdout)
        self.assertEqual(payload["default"], "agents-project")
        self.assertEqual({item["root"] for item in payload["targets"]}, {".agents/skills", "~/.agents/skills"})
        self.assertEqual(
            {item["target"] for item in payload["targets"]},
            {"agents-project", "agents-global", "codex-project", "codex-global"},
        )

    def test_skill_validator_enforces_portable_frontmatter_contract(self) -> None:
        capelry = load_module("capelry_skill_validation", CAPELRY_SCRIPT)
        with tempfile.TemporaryDirectory() as tmpdir:
            valid_dir = Path(tmpdir) / "portable-skill"
            valid_dir.mkdir()
            (valid_dir / "SKILL.md").write_text(
                "---\nname: portable-skill\ndescription: >\n  Validates portable skills.\n  Use when testing frontmatter.\nmetadata:\n  owner: fixture\n---\n\n# Instructions\n\nDo the work.\n",
                encoding="utf-8",
            )
            report = capelry.validate_skill_directory(valid_dir)
            self.assertTrue(report["valid"])
            self.assertTrue(report["portable"])
            self.assertGreater(report["descriptionLength"], 1)

            (valid_dir / "SKILL.md").write_text(
                "---\nname: wrong-name\ndescription: Present but mismatched.\n---\n\n# Instructions\n",
                encoding="utf-8",
            )
            report = capelry.validate_skill_directory(valid_dir)
            self.assertFalse(report["valid"])
            self.assertIn("must match parent directory", " ".join(report["errors"]))

    def test_skill_validator_rejects_non_string_required_yaml_values(self) -> None:
        capelry = load_module("capelry_scalar_validation", CAPELRY_SCRIPT)
        fixtures = (
            ("bad-scalar", "Use when: YAML would parse this as a mapping"),
            ("bad-scalar", "123"),
            ("123", "Numeric names must be quoted even when the directory is numeric"),
            ("bad-scalar", "2026-08-27"),
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            for index, (name, description) in enumerate(fixtures):
                skill_dir = Path(tmpdir) / str(index) / name
                skill_dir.mkdir(parents=True)
                (skill_dir / "SKILL.md").write_text(
                    f"---\nname: {name}\ndescription: {description}\n---\n\n# Instructions\n",
                    encoding="utf-8",
                )
                report = capelry.validate_skill_directory(skill_dir)
                self.assertFalse(report["valid"], (name, description))
                self.assertIn("YAML string scalar", " ".join(report["errors"]))

    def test_skill_validators_reject_non_block_scalar_continuations(self) -> None:
        capelry = load_module("capelry_continuation_validation", CAPELRY_SCRIPT)
        bootstrap = load_module("bootstrap_continuation_validation", BOOTSTRAP_SCRIPT)
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_dir = Path(tmpdir) / "continuation-skill"
            skill_dir.mkdir()
            skill_file = skill_dir / "SKILL.md"
            skill_file.write_text(
                "---\nname: continuation-skill\ndescription: >\n"
                "  Valid block scalar.\n  Use when validating multiline fields.\n"
                "---\n\n# Instructions\n",
                encoding="utf-8",
            )
            self.assertTrue(capelry.validate_skill_directory(skill_dir)["valid"])
            self.assertEqual(
                bootstrap.validate_skill_directory(skill_dir, "continuation-skill")["name"],
                "continuation-skill",
            )

            skill_file.write_text(
                '---\nname: continuation-skill\ndescription: "valid"\n'
                "  invalid continuation\n---\n\n# Instructions\n",
                encoding="utf-8",
            )
            report = capelry.validate_skill_directory(skill_dir)
            self.assertFalse(report["valid"])
            self.assertIn("cannot continue non-block scalar", " ".join(report["errors"]))
            with self.assertRaisesRegex(SystemExit, "cannot continue a non-block scalar"):
                bootstrap.validate_skill_directory(skill_dir, "continuation-skill")

    def test_skill_validators_enforce_frontmatter_lexical_rules(self) -> None:
        capelry = load_module("capelry_lexical_validation", CAPELRY_SCRIPT)
        bootstrap = load_module("bootstrap_lexical_validation", BOOTSTRAP_SCRIPT)
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_dir = Path(tmpdir) / "lexical-skill"
            skill_dir.mkdir()
            skill_file = skill_dir / "SKILL.md"
            fixtures = (
                "---\nname: lexical-skill\ndescription: |\n  valid\n  ---\ncompatibility:\n  - linux\n---\n# Body\n",
                "---\nname: lexical-skill\ndescription: |\n  ok\n  #" + "x" * 1025 + "\n---\n# Body\n",
                "---\nname: lexical-skill\ndescription: ok\x00bad\n---\n# Body\n",
            )
            for fixture in fixtures:
                skill_file.write_text(fixture, encoding="utf-8")
                self.assertFalse(capelry.validate_skill_directory(skill_dir)["valid"])
                with self.assertRaises(SystemExit):
                    bootstrap.validate_skill_directory(skill_dir, "lexical-skill")

    def test_skill_validators_reject_forbidden_plain_scalar_prefixes(self) -> None:
        capelry = load_module("capelry_forbidden_prefix_validation", CAPELRY_SCRIPT)
        bootstrap = load_module("bootstrap_forbidden_prefix_validation", BOOTSTRAP_SCRIPT)
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_dir = Path(tmpdir) / "prefix-skill"
            skill_dir.mkdir()
            for prefix in ("@foo", "`foo", "!foo", "&foo", "*foo", "%foo", "|foo", ">foo", "true # documented"):
                (skill_dir / "SKILL.md").write_text(
                    f"---\nname: prefix-skill\ndescription: {prefix}\n---\n\n# Instructions\n",
                    encoding="utf-8",
                )
                report = capelry.validate_skill_directory(skill_dir)
                self.assertFalse(report["valid"], prefix)
                self.assertIn("must be a YAML string scalar", " ".join(report["errors"]))
                with self.assertRaisesRegex(SystemExit, "must be a YAML string"):
                    bootstrap.validate_skill_directory(skill_dir, "prefix-skill")

    def test_metadata_must_be_a_string_to_string_mapping(self) -> None:
        capelry = load_module("capelry_metadata_validation", CAPELRY_SCRIPT)
        bootstrap = load_module("bootstrap_metadata_validation", BOOTSTRAP_SCRIPT)
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_dir = Path(tmpdir) / "metadata-skill"
            skill_dir.mkdir()
            skill_file = skill_dir / "SKILL.md"
            skill_file.write_text(
                "---\nname: metadata-skill\ndescription: Fixture. Use for metadata validation.\n"
                "metadata:\n  owner: fixture\n  version: \"1.0\"\n---\n\n# Instructions\n",
                encoding="utf-8",
            )
            self.assertTrue(capelry.validate_skill_directory(skill_dir)["valid"])
            self.assertEqual(bootstrap.validate_skill_directory(skill_dir, "metadata-skill")["name"], "metadata-skill")

            skill_file.write_text(
                "---\nname: metadata-skill\ndescription: Fixture. Use for metadata validation.\n"
                "metadata:\n  - owner: fixture\n---\n\n# Instructions\n",
                encoding="utf-8",
            )
            report = capelry.validate_skill_directory(skill_dir)
            self.assertFalse(report["valid"])
            self.assertIn("metadata must be a mapping, not a sequence", report["errors"])
            with self.assertRaisesRegex(SystemExit, "metadata must be a mapping, not a sequence"):
                bootstrap.validate_skill_directory(skill_dir, "metadata-skill")

            for invalid_key in ("@foo", "true"):
                skill_file.write_text(
                    "---\nname: metadata-skill\ndescription: Fixture. Use for metadata validation.\n"
                    f"metadata:\n  {invalid_key}: bar\n---\n\n# Instructions\n",
                    encoding="utf-8",
                )
                self.assertFalse(capelry.validate_skill_directory(skill_dir)["valid"])
                with self.assertRaisesRegex(SystemExit, "metadata key"):
                    bootstrap.validate_skill_directory(skill_dir, "metadata-skill")

    def test_bootstrap_rejects_invalid_double_quoted_scalars(self) -> None:
        capelry = load_module("capelry_double_quote_validation", CAPELRY_SCRIPT)
        bootstrap = load_module("bootstrap_double_quote_validation", BOOTSTRAP_SCRIPT)
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_dir = Path(tmpdir) / "double-quote-skill"
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text(
                '---\nname: double-quote-skill\ndescription: "bad\\q"\n---\n\n# Instructions\n',
                encoding="utf-8",
            )
            self.assertFalse(capelry.validate_skill_directory(skill_dir)["valid"])
            with self.assertRaisesRegex(SystemExit, "valid double-quoted YAML string"):
                bootstrap.validate_skill_directory(skill_dir, "double-quote-skill")

    def test_optional_portable_fields_must_be_string_scalars(self) -> None:
        capelry = load_module("capelry_optional_scalar_validation", CAPELRY_SCRIPT)
        bootstrap = load_module("bootstrap_optional_scalar_validation", BOOTSTRAP_SCRIPT)
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_dir = Path(tmpdir) / "optional-scalar-skill"
            skill_dir.mkdir()
            for field in ("license", "compatibility", "allowed-tools"):
                (skill_dir / "SKILL.md").write_text(
                    "---\nname: optional-scalar-skill\n"
                    "description: Fixture. Use for optional scalar validation.\n"
                    f"{field}:\n  - invalid-sequence-value\n"
                    "---\n\n# Instructions\n",
                    encoding="utf-8",
                )
                report = capelry.validate_skill_directory(skill_dir)
                self.assertFalse(report["valid"], field)
                self.assertIn(
                    f"frontmatter field '{field}' must be a string, not a sequence or mapping",
                    report["errors"],
                )
                with self.assertRaisesRegex(SystemExit, f"field '{field}' must be a string"):
                    bootstrap.validate_skill_directory(skill_dir, "optional-scalar-skill")

    def test_skill_validators_reject_invalid_block_scalar_indentation(self) -> None:
        capelry = load_module("capelry_block_indent_validation", CAPELRY_SCRIPT)
        bootstrap = load_module("bootstrap_block_indent_validation", BOOTSTRAP_SCRIPT)
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_dir = Path(tmpdir) / "block-indent-skill"
            skill_dir.mkdir()
            skill_file = skill_dir / "SKILL.md"
            skill_file.write_text(
                "---\nname: block-indent-skill\ndescription: |\n  first line\n    deeper line\n"
                "---\n\n# Instructions\n",
                encoding="utf-8",
            )
            self.assertTrue(capelry.validate_skill_directory(skill_dir)["valid"])
            self.assertEqual(
                bootstrap.validate_skill_directory(skill_dir, "block-indent-skill")["name"],
                "block-indent-skill",
            )

            for marker in ("|2", "|2-", "|-2", ">2+", ">+2"):
                skill_file.write_text(
                    f"---\nname: block-indent-skill\ndescription: {marker}\n"
                    "  explicit indentation\n---\n\n# Instructions\n",
                    encoding="utf-8",
                )
                self.assertTrue(capelry.validate_skill_directory(skill_dir)["valid"], marker)
                self.assertEqual(
                    bootstrap.validate_skill_directory(skill_dir, "block-indent-skill")["name"],
                    "block-indent-skill",
                )

            for invalid_content in ("  good\n bad", "  good\n\tbad"):
                skill_file.write_text(
                    "---\nname: block-indent-skill\ndescription: |\n"
                    f"{invalid_content}\n---\n\n# Instructions\n",
                    encoding="utf-8",
                )
                report = capelry.validate_skill_directory(skill_dir)
                self.assertFalse(report["valid"], invalid_content)
                self.assertIn("block scalar field 'description'", " ".join(report["errors"]))
                with self.assertRaisesRegex(SystemExit, "block scalar field 'description'"):
                    bootstrap.validate_skill_directory(skill_dir, "block-indent-skill")

    def test_skill_validators_require_escaped_yaml_single_quotes(self) -> None:
        capelry = load_module("capelry_single_quote_validation", CAPELRY_SCRIPT)
        bootstrap = load_module("bootstrap_single_quote_validation", BOOTSTRAP_SCRIPT)
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_dir = Path(tmpdir) / "single-quote-skill"
            skill_dir.mkdir()
            skill_file = skill_dir / "SKILL.md"
            skill_file.write_text(
                "---\nname: single-quote-skill\ndescription: 'It''s useful for validation'\n"
                "---\n\n# Instructions\n",
                encoding="utf-8",
            )
            report = capelry.validate_skill_directory(skill_dir)
            bootstrap_report = bootstrap.validate_skill_directory(skill_dir, "single-quote-skill")
            self.assertTrue(report["valid"])
            self.assertEqual(report["descriptionLength"], len("It's useful for validation"))
            self.assertEqual(bootstrap_report["descriptionLength"], len("It's useful for validation"))

            skill_file.write_text(
                "---\nname: single-quote-skill\ndescription: 'It's useful for validation'\n"
                "---\n\n# Instructions\n",
                encoding="utf-8",
            )
            report = capelry.validate_skill_directory(skill_dir)
            self.assertFalse(report["valid"])
            self.assertIn("unescaped apostrophe", " ".join(report["errors"]))
            with self.assertRaisesRegex(SystemExit, "unescaped apostrophe"):
                bootstrap.validate_skill_directory(skill_dir, "single-quote-skill")

    def test_skill_validators_preserve_hashes_inside_quoted_descriptions(self) -> None:
        capelry = load_module("capelry_quoted_hash_validation", CAPELRY_SCRIPT)
        bootstrap = load_module("bootstrap_quoted_hash_validation", BOOTSTRAP_SCRIPT)
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_dir = Path(tmpdir) / "incident-triage"
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text(
                '---\nname: incident-triage\ndescription: "Use for #incident triage and response"\n---\n\n# Instructions\n',
                encoding="utf-8",
            )
            report = capelry.validate_skill_directory(skill_dir)
            bootstrap_report = bootstrap.validate_skill_directory(skill_dir, "incident-triage")

        self.assertTrue(report["valid"])
        self.assertEqual(bootstrap_report["name"], "incident-triage")

    def test_skill_validator_flags_non_standard_fields_as_non_portable(self) -> None:
        capelry = load_module("capelry_nonportable_validation", CAPELRY_SCRIPT)
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_dir = Path(tmpdir) / "cursor-skill"
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text(
                "---\nname: cursor-skill\ndescription: Cursor-scoped fixture. Use when testing paths.\npaths: '**/*.py'\n---\n\n# Instructions\n",
                encoding="utf-8",
            )
            report = capelry.validate_skill_directory(skill_dir)

        self.assertTrue(report["valid"])
        self.assertFalse(report["portable"])
        self.assertIn("non-standard frontmatter fields", " ".join(report["warnings"]))

    def test_validate_skill_command_accepts_repository_skill(self) -> None:
        result = subprocess.run(
            [sys.executable, str(CAPELRY_SCRIPT), "validate-skill", str(ROOT / "skills" / "capelry"), "--json"],
            check=True,
            text=True,
            capture_output=True,
            env=clean_env(),
        )

        payload = json.loads(result.stdout)
        self.assertTrue(payload["valid"])
        self.assertTrue(payload["portable"])
        self.assertEqual(payload["name"], "capelry")

    def test_harness_target_install_uses_native_root_and_next_step(self) -> None:
        with RegistryFixture() as fixture, tempfile.TemporaryDirectory() as tmpdir:
            result = subprocess.run(
                [
                    sys.executable,
                    str(CAPELRY_SCRIPT),
                    "--registry",
                    fixture.url,
                    "install",
                    "capelry-ai/capelry-skills/zip-skill",
                    "--target",
                    "opencode-project",
                    "--json",
                ],
                check=True,
                text=True,
                capture_output=True,
                cwd=tmpdir,
                env=clean_env(),
            )

            payload = json.loads(result.stdout)
            installed = Path(tmpdir) / ".opencode" / "skills" / "zip-skill" / "SKILL.md"
            self.assertTrue(installed.exists())
            self.assertEqual(payload["destination"], ".opencode/skills/zip-skill")
            self.assertIn("OpenCode", payload["next"])

    def test_ard_zip_install_verifies_checksum_and_extracts_safely(self) -> None:
        with RegistryFixture() as fixture, tempfile.TemporaryDirectory() as tmpdir:
            dest = Path(tmpdir) / "zip-skill"
            result = subprocess.run(
                [
                    sys.executable,
                    str(CAPELRY_SCRIPT),
                    "--registry",
                    fixture.url,
                    "install",
                    "capelry-ai/capelry-skills/zip-skill",
                    "--dest",
                    str(dest),
                ],
                check=True,
                text=True,
                capture_output=True,
                env=clean_env(),
            )

            self.assertTrue((dest / "SKILL.md").exists())
            self.assertIn("trust: checksum-only", result.stdout)
            self.assertIn("checksum:", result.stdout)
            self.assertFalse(RegistryFixtureHandler.unexpected_requests)
            query = urllib.parse.parse_qs(urllib.parse.urlparse(RegistryFixtureHandler.agents_requests[0]).query)
            self.assertIn("metadata.com.capelry.slug", query["filter"][0])

    def test_ard_zip_install_rejects_checksum_mismatch(self) -> None:
        with RegistryFixture() as fixture, tempfile.TemporaryDirectory() as tmpdir:
            dest = Path(tmpdir) / "bad-checksum"
            result = subprocess.run(
                [
                    sys.executable,
                    str(CAPELRY_SCRIPT),
                    "--registry",
                    fixture.url,
                    "install",
                    "capelry-ai/capelry-skills/bad-checksum",
                    "--dest",
                    str(dest),
                ],
                text=True,
                capture_output=True,
                env=clean_env(),
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("SHA-256 mismatch", result.stderr)
            self.assertFalse(dest.exists())

    def test_invalid_checksum_metadata_fails_closed(self) -> None:
        capelry = load_module("capelry_cli", CAPELRY_SCRIPT)
        with self.assertRaisesRegex(SystemExit, "Invalid archive SHA-256 metadata"):
            capelry.verify_archive_checksum(b"fixture", "not-a-sha256")

    def test_ard_zip_install_rejects_unsafe_archive_path(self) -> None:
        with RegistryFixture() as fixture, tempfile.TemporaryDirectory() as tmpdir:
            dest = Path(tmpdir) / "unsafe"
            result = subprocess.run(
                [
                    sys.executable,
                    str(CAPELRY_SCRIPT),
                    "--registry",
                    fixture.url,
                    "install",
                    "capelry-ai/capelry-skills/unsafe-zip",
                    "--dest",
                    str(dest),
                ],
                text=True,
                capture_output=True,
                env=clean_env(),
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Unsafe archive path", result.stderr)
            self.assertFalse(dest.exists())

    def test_ard_zip_install_rejects_backslash_traversal(self) -> None:
        with RegistryFixture() as fixture, tempfile.TemporaryDirectory() as tmpdir:
            dest = Path(tmpdir) / "backslash-unsafe"
            result = subprocess.run(
                [
                    sys.executable,
                    str(CAPELRY_SCRIPT),
                    "--registry",
                    fixture.url,
                    "install",
                    "capelry-ai/capelry-skills/backslash-unsafe",
                    "--dest",
                    str(dest),
                ],
                text=True,
                capture_output=True,
                env=clean_env(),
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Unsafe archive path", result.stderr)
            self.assertFalse(dest.exists())

    def test_invalid_skill_cannot_replace_existing_install(self) -> None:
        with RegistryFixture() as fixture, tempfile.TemporaryDirectory() as tmpdir:
            dest = Path(tmpdir) / "invalid-skill"
            dest.mkdir()
            (dest / "SKILL.md").write_text(RegistryFixtureHandler.skill_md("invalid-skill", "Existing valid skill. Use for rollback testing."), encoding="utf-8")
            marker = dest / "preserve-me.txt"
            marker.write_text("original", encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    str(CAPELRY_SCRIPT),
                    "--registry",
                    fixture.url,
                    "install",
                    "capelry-ai/capelry-skills/invalid-skill",
                    "--dest",
                    str(dest),
                    "--force",
                ],
                text=True,
                capture_output=True,
                env=clean_env(),
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("description", result.stderr)
            self.assertEqual(marker.read_text(encoding="utf-8"), "original")
            self.assertIn("Existing valid skill", (dest / "SKILL.md").read_text(encoding="utf-8"))

    def test_malformed_yaml_cannot_replace_existing_install(self) -> None:
        with RegistryFixture() as fixture, tempfile.TemporaryDirectory() as tmpdir:
            dest = Path(tmpdir) / "malformed-yaml"
            dest.mkdir()
            (dest / "SKILL.md").write_text(
                RegistryFixtureHandler.skill_md(
                    "malformed-yaml",
                    "Existing valid skill. Use for malformed YAML rollback testing.",
                ),
                encoding="utf-8",
            )
            marker = dest / "preserve-me.txt"
            marker.write_text("original", encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    str(CAPELRY_SCRIPT),
                    "--registry",
                    fixture.url,
                    "install",
                    "capelry-ai/capelry-skills/malformed-yaml",
                    "--dest",
                    str(dest),
                    "--force",
                ],
                text=True,
                capture_output=True,
                env=clean_env(),
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("cannot continue non-block scalar", result.stderr)
            self.assertEqual(marker.read_text(encoding="utf-8"), "original")
            self.assertIn("Existing valid skill", (dest / "SKILL.md").read_text(encoding="utf-8"))

    def test_malformed_single_quote_cannot_replace_existing_install(self) -> None:
        with RegistryFixture() as fixture, tempfile.TemporaryDirectory() as tmpdir:
            dest = Path(tmpdir) / "malformed-single-quote"
            dest.mkdir()
            (dest / "SKILL.md").write_text(
                RegistryFixtureHandler.skill_md(
                    "malformed-single-quote",
                    "Existing valid skill. Use for single-quote rollback testing.",
                ),
                encoding="utf-8",
            )
            marker = dest / "preserve-me.txt"
            marker.write_text("original", encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    str(CAPELRY_SCRIPT),
                    "--registry",
                    fixture.url,
                    "install",
                    "capelry-ai/capelry-skills/malformed-single-quote",
                    "--dest",
                    str(dest),
                    "--force",
                ],
                text=True,
                capture_output=True,
                env=clean_env(),
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("unescaped apostrophe", result.stderr)
            self.assertEqual(marker.read_text(encoding="utf-8"), "original")
            self.assertIn("Existing valid skill", (dest / "SKILL.md").read_text(encoding="utf-8"))

    def test_schema_invalid_skills_cannot_replace_existing_installs(self) -> None:
        with RegistryFixture() as fixture, tempfile.TemporaryDirectory() as tmpdir:
            for ref, expected_error in (
                ("compatibility-sequence", "must be a string, not a sequence or mapping"),
                ("invalid-block-indent", "block scalar field 'description'"),
                ("forbidden-prefix", "must be a YAML string scalar"),
                ("metadata-sequence", "metadata must be a mapping, not a sequence"),
            ):
                dest = Path(tmpdir) / ref
                dest.mkdir()
                (dest / "SKILL.md").write_text(
                    RegistryFixtureHandler.skill_md(
                        ref,
                        "Existing valid skill. Use for schema rollback testing.",
                    ),
                    encoding="utf-8",
                )
                marker = dest / "preserve-me.txt"
                marker.write_text("original", encoding="utf-8")
                result = subprocess.run(
                    [
                        sys.executable,
                        str(CAPELRY_SCRIPT),
                        "--registry",
                        fixture.url,
                        "install",
                        f"capelry-ai/capelry-skills/{ref}",
                        "--dest",
                        str(dest),
                        "--force",
                    ],
                    text=True,
                    capture_output=True,
                    env=clean_env(),
                )

                self.assertNotEqual(result.returncode, 0, ref)
                self.assertIn(expected_error, result.stderr)
                self.assertEqual(marker.read_text(encoding="utf-8"), "original")
                self.assertIn("Existing valid skill", (dest / "SKILL.md").read_text(encoding="utf-8"))

    def test_catalog_install_name_cannot_redirect_to_declared_skill_name(self) -> None:
        with RegistryFixture() as fixture, tempfile.TemporaryDirectory() as tmpdir:
            redirected = Path(tmpdir) / ".agents" / "skills" / "redirected-skill"
            redirected.mkdir(parents=True)
            marker = redirected / "preserve-me.txt"
            marker.write_text("original", encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    str(CAPELRY_SCRIPT),
                    "--registry",
                    fixture.url,
                    "install",
                    "capelry-ai/capelry-skills/planned-skill",
                    "--target",
                    "agents-project",
                    "--force",
                ],
                text=True,
                capture_output=True,
                cwd=tmpdir,
                env=clean_env(),
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("must match parent directory 'planned-skill'", result.stderr)
            self.assertFalse((Path(tmpdir) / ".agents" / "skills" / "planned-skill").exists())
            self.assertEqual(marker.read_text(encoding="utf-8"), "original")

    def test_install_stages_candidate_beside_destination(self) -> None:
        capelry = load_module("capelry_same_filesystem_staging", CAPELRY_SCRIPT)
        with tempfile.TemporaryDirectory() as tmpdir:
            dest = Path(tmpdir) / "skills" / "local-skill"
            args = SimpleNamespace(dest=str(dest), name=None, target="agents-project", force=False)
            observed: dict[str, Path] = {}

            def fake_install(_entry, candidate: Path, force: bool):
                self.assertTrue(force)
                observed["candidate"] = candidate
                candidate.mkdir(parents=True)
                (candidate / "SKILL.md").write_text(
                    RegistryFixtureHandler.skill_md("local-skill"),
                    encoding="utf-8",
                )
                return "fixture", None

            with mock.patch.object(capelry, "install_ard_entry", side_effect=fake_install):
                installed, _, _, validation = capelry.install_ard_entry_for_args({}, args, "local-skill")

            self.assertEqual(installed, dest)
            self.assertEqual(observed["candidate"].parent.parent, dest.parent)
            self.assertTrue(validation["valid"])
            self.assertTrue((dest / "SKILL.md").exists())

    def test_explicit_destination_must_match_declared_skill_name(self) -> None:
        with RegistryFixture() as fixture, tempfile.TemporaryDirectory() as tmpdir:
            dest = Path(tmpdir) / "renamed-skill"
            result = subprocess.run(
                [
                    sys.executable,
                    str(CAPELRY_SCRIPT),
                    "--registry",
                    fixture.url,
                    "install",
                    "capelry-ai/capelry-skills/zip-skill",
                    "--dest",
                    str(dest),
                ],
                text=True,
                capture_output=True,
                env=clean_env(),
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("must match parent directory", result.stderr)
            self.assertFalse(dest.exists())

    def test_ard_source_install_uses_pinned_archive_descriptor(self) -> None:
        with RegistryFixture() as fixture, tempfile.TemporaryDirectory() as tmpdir:
            dest = Path(tmpdir) / "source-skill"
            result = subprocess.run(
                [
                    sys.executable,
                    str(CAPELRY_SCRIPT),
                    "--registry",
                    fixture.url,
                    "install",
                    "capelry-ai/capelry-skills/source-skill",
                    "--dest",
                    str(dest),
                    "--json",
                ],
                check=True,
                text=True,
                capture_output=True,
                env=clean_env(),
            )

            payload = json.loads(result.stdout)
            self.assertTrue((dest / "SKILL.md").exists())
            self.assertEqual(payload["installedFrom"], "ARD source archive descriptor at fixture-ref")
            self.assertEqual(payload["mediaType"], "application/vnd.capelry.skill-source+json")
            self.assertTrue(payload["validation"]["valid"])
            self.assertEqual(payload["validation"]["path"], str(dest / "SKILL.md"))
            self.assertIn("Reload or restart", payload["next"])

    def test_ard_install_refuses_unsupported_media_type_with_guidance(self) -> None:
        with RegistryFixture() as fixture, tempfile.TemporaryDirectory() as tmpdir:
            dest = Path(tmpdir) / "unsupported"
            result = subprocess.run(
                [
                    sys.executable,
                    str(CAPELRY_SCRIPT),
                    "--registry",
                    fixture.url,
                    "install",
                    "capelry-ai/capelry-skills/unsupported",
                    "--dest",
                    str(dest),
                ],
                text=True,
                capture_output=True,
                env=clean_env(),
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Unsupported ARD media type", result.stderr)
            self.assertIn("Open/connect manually", result.stderr)
            self.assertFalse(dest.exists())

    def test_well_known_ai_catalog_matches_skill_catalog(self) -> None:
        self_catalog = json.loads(SELF_CATALOG.read_text(encoding="utf-8"))
        well_known_catalog = json.loads(WELL_KNOWN_CATALOG.read_text(encoding="utf-8"))

        self.assertEqual(well_known_catalog, self_catalog)

    def test_self_ai_catalog_entry_validates_fixture_shape(self) -> None:
        catalog = json.loads(SELF_CATALOG.read_text(encoding="utf-8"))
        self.assertEqual(catalog["specVersion"], "1.0")
        self.assertEqual(catalog["host"]["identifier"], "github.com")
        self.assertEqual(catalog["host"]["trustManifest"]["identity"], "https://github.com/capelry-ai/capelry-skills")
        self.assertEqual(catalog["host"]["trustManifest"]["identityType"], "https")
        manifest = SELF_CAPABILITY.read_text(encoding="utf-8")
        manifest_version = next(
            line.split(":", 1)[1].strip()
            for line in manifest.splitlines()
            if line.strip().startswith("version:")
        )
        self.assertEqual(manifest_version, "2.1.0")
        self.assertIn(f"capelry-{manifest_version}.zip", manifest)
        entries = catalog["entries"]
        self.assertEqual(len(entries), 1)
        entry = entries[0]
        self.assertEqual(entry["version"], manifest_version)
        for field in ("identifier", "displayName", "type", "description", "metadata", "trustManifest"):
            self.assertIn(field, entry)
        self.assertRegex(entry["identifier"], r"^urn:air:github\.com:[A-Za-z0-9._~-]+:[A-Za-z0-9._~-]+:[A-Za-z0-9._~-]+$")
        self.assertEqual(entry["type"], "application/vnd.capelry.skill-source+json")
        self.assertEqual(("url" in entry) + ("data" in entry), 1)
        self.assertEqual(entry["data"]["repository"], "https://github.com/capelry-ai/capelry-skills")
        self.assertEqual(entry["data"]["path"], "skills/capelry")
        self.assertEqual(entry["data"]["defaultInstallName"], "capelry")
        self.assertEqual(entry["metadata"]["com.capelry.slug"], "capelry-ai/capelry-skills/capelry")
        self.assertEqual(entry["metadata"]["com.capelry.catalogPath"], "capelry-ai/capelry-skills")
        self.assertEqual(entry["metadata"]["com.capelry.catalogSlug"], "capelry-skills")
        self.assertEqual(entry["metadata"]["com.capelry.sourceRepositoryFullName"], "capelry-ai/capelry-skills")
        capelry = load_module("capelry_catalog_targets", CAPELRY_SCRIPT)
        catalog_targets = set(entry["metadata"]["com.capelry.installTargets"].split(","))
        self.assertEqual(catalog_targets, set(capelry.TARGET_ROOTS))
        self.assertEqual(capelry.CAPELRY_SKILL_VERSION, manifest_version)
        for project_target in sorted(target for target in capelry.TARGET_ROOTS if target.endswith("-project")):
            self.assertIn(f"- target: {project_target}", manifest)
        self.assertIn("references/harnesses.md", manifest)
        removed_metadata_key = "com.capelry." + "legacy" + "Ref"
        self.assertNotIn(removed_metadata_key, entry["metadata"])
        self.assertEqual(entry["metadata"]["com.capelry.trustState"], "source-hosted")
        self.assertLessEqual(len(entry["representativeQueries"]), 10)
        for value in entry["metadata"].values():
            self.assertTrue(value is None or isinstance(value, (str, int, float, bool)))
        self.assertEqual(entry["trustManifest"]["identity"], "https://github.com/capelry-ai/capelry-skills")
        self.assertEqual(entry["trustManifest"]["identityType"], "https")

    def test_install_catalog_dry_run_plans_supported_entries(self) -> None:
        with RegistryFixture() as fixture:
            result = subprocess.run(
                [
                    sys.executable,
                    str(CAPELRY_SCRIPT),
                    "--registry",
                    fixture.url,
                    "install-catalog",
                    "capelry-ai/capelry-skills",
                    "--target",
                    "pi-project",
                    "--dry-run",
                    "--json",
                ],
                check=True,
                text=True,
                capture_output=True,
                env=clean_env(),
            )

        payload = json.loads(result.stdout)
        self.assertEqual(payload["catalog"], "capelry-ai/capelry-skills")
        self.assertEqual(payload["target"], "pi-project")
        self.assertEqual(payload["count"], 1)
        self.assertEqual(payload["entries"][0]["slug"], "capelry-ai/capelry-skills/demo-skill")
        self.assertTrue(RegistryFixtureHandler.agents_requests)
        query = urllib.parse.parse_qs(urllib.parse.urlparse(RegistryFixtureHandler.agents_requests[0]).query)
        self.assertIn("metadata.com.capelry.catalogPath", query["filter"][0])

    def test_transactional_replace_rolls_back_on_keyboard_interrupt(self) -> None:
        capelry = load_module("capelry_interrupt_rollback", CAPELRY_SCRIPT)
        with tempfile.TemporaryDirectory() as tmpdir:
            dest = Path(tmpdir) / "capelry"
            new_dir = Path(tmpdir) / "candidate"
            dest.mkdir()
            new_dir.mkdir()
            (dest / "marker.txt").write_text("old", encoding="utf-8")
            (new_dir / "marker.txt").write_text("new", encoding="utf-8")
            original_move = capelry.shutil.move
            calls = 0

            def interrupt_second_move(source, target):
                nonlocal calls
                calls += 1
                if calls == 2:
                    raise KeyboardInterrupt()
                return original_move(source, target)

            with (
                mock.patch.object(capelry.shutil, "move", side_effect=interrupt_second_move),
                self.assertRaises(KeyboardInterrupt),
            ):
                capelry.replace_skill_dir(dest, new_dir, keep_backup=False)

            self.assertEqual((dest / "marker.txt").read_text(encoding="utf-8"), "old")

    def test_sync_install_copies_local_skill_source_with_archive_backup(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            dest = Path(tmpdir) / "capelry"
            (dest / "scripts").mkdir(parents=True)
            (dest / "SKILL.md").write_text("old skill\n", encoding="utf-8")
            (dest / "capability.yaml").write_text("metadata:\n  version: 0.0.1\n", encoding="utf-8")
            (dest / "scripts" / "capelry.py").write_text("print('old')\n", encoding="utf-8")
            (dest / "scripts" / "bootstrap.py").write_text("print('old')\n", encoding="utf-8")

            result = subprocess.run(
                [
                    sys.executable,
                    str(CAPELRY_SCRIPT),
                    "sync-install",
                    "--dest",
                    str(dest),
                    "--yes",
                    "--json",
                ],
                check=True,
                text=True,
                capture_output=True,
                env=clean_env(),
            )

            payload = json.loads(result.stdout)
            backup = Path(payload["backup"])
            self.assertTrue((dest / "SKILL.md").exists())
            self.assertTrue((dest / "scripts" / "capelry.py").exists())
            self.assertEqual(payload["sourceVersion"], "2.1.0")
            self.assertEqual(payload["destVersion"], "0.0.1")
            self.assertEqual(payload["backupPolicy"], "archive")
            self.assertTrue(backup.exists())
            self.assertEqual(backup.suffix, ".zip")
            with zipfile.ZipFile(backup) as zf:
                self.assertEqual(zf.read("capelry/SKILL.md").decode("utf-8"), "old skill\n")

    def test_sync_install_reports_target_specific_activation_step(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            result = subprocess.run(
                [
                    sys.executable,
                    str(CAPELRY_SCRIPT),
                    "sync-install",
                    "--source",
                    str(ROOT / "skills" / "capelry"),
                    "--target",
                    "opencode-project",
                    "--yes",
                    "--json",
                ],
                check=True,
                text=True,
                capture_output=True,
                cwd=tmpdir,
                env=clean_env(),
            )

            payload = json.loads(result.stdout)
            self.assertIn("OpenCode", payload["next"])
            self.assertTrue((Path(tmpdir) / ".opencode" / "skills" / "capelry" / "SKILL.md").exists())

    def test_bootstrap_rejects_destination_name_mismatch_before_download(self) -> None:
        result = subprocess.run(
            [sys.executable, str(BOOTSTRAP_SCRIPT), "--dest", "/tmp/not-capelry"],
            text=True,
            capture_output=True,
            env=clean_env(),
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("directory named 'capelry'", result.stderr)

    def test_bootstrap_rejects_non_string_required_frontmatter(self) -> None:
        bootstrap = load_module("capelry_bootstrap_scalar_validation", BOOTSTRAP_SCRIPT)
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_dir = Path(tmpdir) / "123"
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text(
                "---\nname: 123\ndescription: 456\n---\n\n# Instructions\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(SystemExit, "YAML string"):
                bootstrap.validate_skill_directory(skill_dir, "123")

    def test_bootstrap_rejects_duplicate_frontmatter_before_replacement(self) -> None:
        bootstrap = load_module("capelry_bootstrap_duplicate_validation", BOOTSTRAP_SCRIPT)
        duplicate_skill = (
            "---\nname: capelry\nname: wrong\n"
            "description: Fixture. Use for duplicate-field validation.\n"
            "---\n\n# Instructions\n"
        )
        archive = io.BytesIO()
        with zipfile.ZipFile(archive, "w") as zf:
            zf.writestr("repo-main/skills/capelry/SKILL.md", duplicate_skill)
        archive.seek(0)

        with tempfile.TemporaryDirectory() as tmpdir:
            dest = Path(tmpdir) / "capelry"
            dest.mkdir()
            marker = dest / "preserve-me.txt"
            marker.write_text("original", encoding="utf-8")
            (dest / "SKILL.md").write_text(RegistryFixtureHandler.skill_md("capelry"), encoding="utf-8")
            with zipfile.ZipFile(archive) as zf:
                source_path, rel_members = bootstrap.find_skill_source(zf, ("skills/capelry",))
                with self.assertRaisesRegex(SystemExit, "field 'name' is declared more than once"):
                    bootstrap.install_source_path(zf, rel_members, source_path, dest, replace=True)

            self.assertEqual(marker.read_text(encoding="utf-8"), "original")
            self.assertIn("Fixture instructions for capelry", (dest / "SKILL.md").read_text(encoding="utf-8"))

    def test_bootstrap_validation_preserves_existing_destination_on_failure(self) -> None:
        bootstrap = load_module("capelry_bootstrap_atomic", BOOTSTRAP_SCRIPT)
        archive = io.BytesIO()
        with zipfile.ZipFile(archive, "w") as zf:
            zf.writestr("repo-main/skills/capelry/SKILL.md", "---\nname: capelry\n---\n\n# Missing description\n")
        archive.seek(0)

        with tempfile.TemporaryDirectory() as tmpdir:
            dest = Path(tmpdir) / "capelry"
            dest.mkdir()
            marker = dest / "preserve-me.txt"
            marker.write_text("original", encoding="utf-8")
            with zipfile.ZipFile(archive) as zf:
                source_path, rel_members = bootstrap.find_skill_source(zf, ("skills/capelry",))
                with self.assertRaisesRegex(SystemExit, "description"):
                    bootstrap.install_source_path(zf, rel_members, source_path, dest, replace=True)

            self.assertEqual(marker.read_text(encoding="utf-8"), "original")

    def test_bootstrap_finds_and_installs_skill_from_zip_fixture(self) -> None:
        bootstrap = load_module("capelry_bootstrap", BOOTSTRAP_SCRIPT)
        archive = io.BytesIO()
        with zipfile.ZipFile(archive, "w") as zf:
            zf.writestr("repo-main/README.md", "fixture")
            zf.writestr("repo-main/skills/capelry/SKILL.md", RegistryFixtureHandler.skill_md("capelry"))
            zf.writestr("repo-main/skills/capelry/scripts/capelry.py", "print('ok')\n")
        archive.seek(0)

        with tempfile.TemporaryDirectory() as tmpdir:
            dest = Path(tmpdir) / "capelry"
            with zipfile.ZipFile(archive) as zf:
                source_path, rel_members = bootstrap.find_skill_source(
                    zf,
                    ("skills/capelry",),
                )
                bootstrap.install_source_path(
                    zf,
                    rel_members,
                    source_path,
                    dest,
                    replace=True,
                )

            self.assertEqual(source_path, "skills/capelry")
            self.assertTrue((dest / "SKILL.md").exists())
            self.assertTrue((dest / "scripts" / "capelry.py").exists())


if __name__ == "__main__":
    unittest.main()

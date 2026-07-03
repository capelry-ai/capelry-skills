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

ROOT = Path(__file__).resolve().parents[1]
CAPELRY_SCRIPT = ROOT / "skills" / "capelry" / "scripts" / "capelry.py"
BOOTSTRAP_SCRIPT = ROOT / "skills" / "capelry" / "scripts" / "bootstrap.py"
SELF_CATALOG = ROOT / "skills" / "capelry" / "ai-catalog.json"
WELL_KNOWN_CATALOG = ROOT / ".well-known" / "ai-catalog.json"
SELF_CAPABILITY = ROOT / "skills" / "capelry" / "capability.yaml"


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
                zf.writestr(name, content)
        return archive.getvalue()

    @classmethod
    def good_skill_zip(cls) -> bytes:
        return cls.zip_bytes({"SKILL.md": "name: zip-skill\n"})

    @classmethod
    def unsafe_skill_zip(cls) -> bytes:
        return cls.zip_bytes({"../evil/SKILL.md": "name: evil\n"})

    @classmethod
    def source_skill_zip(cls) -> bytes:
        return cls.zip_bytes({"repo-fixture/skills/source-skill/SKILL.md": "name: source-skill\n"})

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
        elif kind == "unsafe":
            entry.update(
                {
                    "identifier": "urn:air:example.com:skills:unsafe-zip",
                    "displayName": "Unsafe Zip Skill",
                    "type": "application/vnd.capelry.skill+zip",
                    "url": f"{base}/archives/unsafe.zip",
                    "metadata": {
                        "com.capelry.packageType": "skill",
                        "com.capelry.trustState": "checksum-only",
                        "com.capelry.slug": "capelry-ai/capelry-skills/unsafe-zip",
                        "com.capelry.catalogPath": "capelry-ai/capelry-skills",
                        "com.capelry.catalogSlug": "capelry-skills",
                        "com.capelry.archiveUrl": f"{base}/archives/unsafe.zip",
                        "com.capelry.archiveChecksumSha256": hashlib.sha256(self.unsafe_skill_zip()).hexdigest(),
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
            elif "unsafe-zip" in filter_value:
                kind = "unsafe"
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
        self.assertEqual(manifest_version, "2.0.9")
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
            self.assertEqual(payload["sourceVersion"], "2.0.9")
            self.assertEqual(payload["destVersion"], "0.0.1")
            self.assertEqual(payload["backupPolicy"], "archive")
            self.assertTrue(backup.exists())
            self.assertEqual(backup.suffix, ".zip")
            with zipfile.ZipFile(backup) as zf:
                self.assertEqual(zf.read("capelry/SKILL.md").decode("utf-8"), "old skill\n")

    def test_bootstrap_finds_and_installs_skill_from_zip_fixture(self) -> None:
        bootstrap = load_module("capelry_bootstrap", BOOTSTRAP_SCRIPT)
        archive = io.BytesIO()
        with zipfile.ZipFile(archive, "w") as zf:
            zf.writestr("repo-main/README.md", "fixture")
            zf.writestr("repo-main/skills/capelry/SKILL.md", "name: capelry\n")
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

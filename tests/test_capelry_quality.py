from __future__ import annotations

import importlib.util
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "skills" / "capelry"
SKILL = SKILL_DIR / "SKILL.md"
CAPABILITY = SKILL_DIR / "capability.yaml"
METRICS_SCRIPT = ROOT / "tests" / "skill_metrics.py"


def load_metrics_module():
    spec = importlib.util.spec_from_file_location("capelry_skill_metrics", METRICS_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {METRICS_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CapelrySkillQualityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.skill_text = SKILL.read_text(encoding="utf-8")
        cls.metrics = load_metrics_module().collect_metrics()

    def test_loaded_skill_context_stays_inside_token_budget(self) -> None:
        prompt = self.metrics["promptContext"]
        self.assertLessEqual(prompt["bytes"], 8_000)
        self.assertLessEqual(prompt["estimatedTokens"], 2_000)

    def test_bootstrap_context_stays_inside_one_time_budget(self) -> None:
        bootstrap = self.metrics["bootstrapContext"]
        self.assertLessEqual(bootstrap["bytes"], 6_500)
        self.assertLessEqual(bootstrap["estimatedTokens"], 1_700)
        text = (SKILL_DIR / "BOOTSTRAP.md").read_text(encoding="utf-8")
        for phrase in (
            "Identify the active coding harness",
            "do not replace it without approval",
            "Verify the installed package without contacting the registry",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)

    def test_default_discovery_has_bounded_cost_envelope(self) -> None:
        defaults = self.metrics["discoveryDefaults"]
        self.assertLessEqual(defaults["top"], 3)
        self.assertLessEqual(defaults["maxQueries"], 4)
        self.assertLessEqual(defaults["perRequestLimit"], 10)
        self.assertLessEqual(defaults["candidateEnvelope"], 40)
        for example in self.metrics["discoveryExamples"].values():
            self.assertLessEqual(example["requestCount"], defaults["maxQueries"])
            self.assertLessEqual(example["candidateEnvelope"], defaults["candidateEnvelope"])

    def test_skill_keeps_effective_decision_and_safety_instructions(self) -> None:
        required_phrases = (
            "Cost-controlled discovery",
            "Run `discover` once",
            "Inspect only the best 1–3",
            "search → inspect → compare → install",
            "Default to project-local",
            "Never self-update",
        )
        for phrase in required_phrases:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.skill_text)
        self.assertNotIn("Generate 3-6 related queries", self.skill_text)

    def test_lazy_reference_links_and_manifest_assets_exist(self) -> None:
        references = set(re.findall(r"references/[a-z0-9_-]+\.md", self.skill_text))
        expected = {
            "references/cli.md",
            "references/harnesses.md",
            "references/maintenance.md",
        }
        self.assertTrue(expected.issubset(references))
        manifest = CAPABILITY.read_text(encoding="utf-8")
        declared_assets = set(re.findall(r"^    - path: (.+)$", manifest, flags=re.MULTILINE))
        for relative in declared_assets:
            with self.subTest(asset=relative):
                self.assertTrue((SKILL_DIR / relative).is_file())
        for relative in references:
            with self.subTest(reference=relative):
                self.assertIn(relative, declared_assets)

    def test_metrics_cover_the_full_test_suite(self) -> None:
        self.assertGreaterEqual(self.metrics["testMethods"], 38)


if __name__ == "__main__":
    unittest.main()

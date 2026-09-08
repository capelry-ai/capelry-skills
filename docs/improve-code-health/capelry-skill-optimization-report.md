# Capelry skill optimization and improvement report

Date: 2026-09-08

Branch: `optimize/capelry-skill-cost-testing`

Integrated baseline: `87adb04` (`v2.1.0`, `origin/main`)

## Scope

Complete the in-progress cost/testing optimization on top of the released harness-aware installer, then perform an Astra-assisted effectiveness pass across the repository's sole shipped skill, `skills/capelry`.

This work preserves v2.1.0's 28 harness targets, package validation, archive protections, transactional replacement, checksum enforcement, and activation guidance. It does not implement the separate unapproved telemetry plan under `docs/ai-dlc/`, close backlog issues, or modify an installed global skill. The resulting release target is v2.2.0.

No live registry or paid-model API calls were used for functional tests. Registry behavior is exercised through local ARD fixtures. “Estimated tokens” is the deterministic `characters / 4` heuristic from `tests/skill_metrics.py`, not provider billing data.

## Baselines and result

| Metric | v2.0.9 baseline | v2.1.0 origin | Integrated result |
| --- | ---: | ---: | ---: |
| Loaded `SKILL.md` bytes | 14,288 | 17,199 | 6,901 |
| Loaded `SKILL.md` lines | 276 | 304 | 113 |
| Loaded skill estimated tokens | 3,569 | 4,297 | 1,719 |
| One-time `BOOTSTRAP.md` bytes | 13,221 | 15,276 | 6,250 |
| One-time bootstrap estimated tokens | 3,306 | 3,819 | 1,548 |
| Default discovery candidate envelope | up to 425 | up to 425 | 40 (4 × 10) |
| CLI bytes | 97,235 | 130,625 | 126,529 |
| CLI lines | 2,340 | 3,172 | 3,073 |
| CLI functions | 165 | 187 | 165 |
| CLI branch nodes | 510 | 714 | 681 |
| Test methods | 27 | 73 | 97 |

The final context remains below enforced budgets of 8,000 bytes/about 2,000 estimated tokens for `SKILL.md` and 6,500 bytes/about 1,700 estimated tokens for `BOOTSTRAP.md`. CLI size is compared with v2.1.0 because its security and harness logic is mandatory, not removable optimization overhead.

## Completed in-progress work

### Bounded discovery and useful output

- Limits default discovery to four requests, ten results per request, and a three-entry shortlist.
- Prioritizes explicit queries, preserves punctuation and Unicode such as `C++`, `C#`, and non-Latin text, and hard-caps expansion at ten requests.
- Deduplicates identifiers while retaining the first payload, best observed numeric score, and unique matched-query evidence.
- Reports queries and request/candidate budgets even when no result matches.
- Makes `--explain-relevance` and `--install-snippet` effective in both concise text and JSON output.
- Keeps generic discovery and bulk inspection target-neutral until the active harness target is selected.

### Inspection and failure behavior

- Aligns detail output with installation's descriptor-first source repository/path/ref/archive/checksum precedence.
- Adds trust identity, provenance, source, and advertised-checksum evidence to `info --json` without removing its existing envelope or keys.
- Clearly distinguishes advertised checksums from hashes verified during download.
- Applies a configurable 1–300 second timeout to each network operation and converts built-in and Python 3.9 `socket.timeout` header/body failures into controlled CLI errors instead of tracebacks.
- Preserves catalog `--keep-going` and self-update GitHub API fallback behavior after controlled download failures.

### Reduced obsolete complexity

- Removes unreachable pre-ARD compatibility helpers and transports while retaining all catalog-aware ARD commands.
- Combines the original optimization tests with all v2.1.0 validation, rollback, checksum, archive-path, and harness-target regressions.
- Expands CI to Python 3.9, 3.11, and 3.13 while retaining the package-validation gate.

## New skill-effectiveness pass

- Rewrites triggering metadata around concrete discovery, inspection, catalog install, validation, bootstrap, update/sync, target-selection, and packaging requests.
- Adds one concise workflow router and explicit paths to the CLI, harness, and maintenance references.
- Keeps harness selection, project-local defaults, approval boundaries, install validation, third-party inspection, and activation confirmation in always-loaded guidance.
- Adds an unsuccessful-discovery branch and a compact answer contract that treats `source-hosted` as provenance rather than a security endorsement.
- Keeps all 28 target names in the standalone bootstrap entry point while moving detailed evidence and caveats to `references/harnesses.md`.
- Clarifies that running a checked-out bootstrap helper still downloads GitHub source; unreleased local content uses `sync-install`.
- Separates generic capability packaging from this repository's release procedure.
- Adds `scripts/package_skill.py`, a deterministic explicit-allowlist archive builder that excludes bytecode, caches, nested archives, tests, reports, unrelated files, and symlinks that could escape the skill root.
- Updates OpenAI UI metadata to compare first, obtain confirmation, validate/install into the selected project target, and confirm visibility.

## Enforced quality gates

`tests/test_capelry_quality.py` fails if:

- loaded `SKILL.md` or one-time `BOOTSTRAP.md` exceeds its context budget;
- default discovery exceeds 4 requests, 10 results per request, or 40 candidate rows;
- decision/safety instructions disappear;
- any of the three lazy references is missing or absent from package metadata.

The full suite additionally covers query fidelity, ranking aggregation, mocked and real stalled-header/body timeout normalization, catalog continuation, self-update fallback, text/JSON output parity, descriptor-first inspection aliases, empty discovery, target-selected slug installation, package symlink rejection, archive contents, extraction, validation, and packaged CLI execution.

## Verification evidence

- Host Python 3.13: **97 tests passed**; full script/test compilation passed.
- Container Python 3.9.25: **97 tests passed**; compilation, package validation, and metrics passed.
- Container Python 3.11.15: **97 tests passed**; compilation, package validation, and metrics passed.
- Container Python 3.13.15: **97 tests passed**; compilation, package validation, and metrics passed.
- Built-in `validate-skill`: `valid: true`, `portable: true`.
- Official `skills-ref==0.1.0`: `Valid skill: skills/capelry`.
- Ruff 0.12.4 focused `E4,E7,E9,F,I`: passed.
- PyYAML 6.0.2 parsed `capability.yaml` and `agents/openai.yaml`.
- Both catalog manifests parse and remain byte-identical.
- Two deterministic package builds produced the same SHA-256 and 11 allowlisted source files; the extracted package passed `validate-skill`, CLI help, and 28-target checks.
- `git diff --cached --check` passed for the exact staged release candidate; the unrelated telemetry draft remained excluded.

## Residual risks and boundaries

- Registry scores are assumed comparable across related queries; maximum-score ranking retains that existing assumption.
- Request/candidate budgets do not cap arbitrary response bytes or later user-approved downloads.
- A printed activation instruction is not proof of actual harness discovery; the user/agent must run the harness check.
- The release candidate synchronizes package metadata at version 2.2.0. Publication must tag the exact reviewed merge commit and preserve catalog/version parity.
- The telemetry planning document still requires product/privacy/design approval and cross-repository ownership before implementation.

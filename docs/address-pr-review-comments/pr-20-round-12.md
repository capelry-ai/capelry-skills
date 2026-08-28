# PR 20 review-remediation plan — round 12

## Fresh closure audit

- PR: https://github.com/capelry-ai/capelry-skills/pull/20
- Exact local/origin/provider head: `3c2f97521f77877b6200c6636e5ed9e4b9f97fee`
- Review threads: 31 total, 31 resolved, zero unresolved, no pagination remainder
- Pending reviews: none
- Actionable non-thread feedback discovered in review `5045500354`: source-archive descriptor installs download bytes without enforcing advertised archive SHA-256 metadata or propagating the verified checksum

## Worklist and action plan

Fix the actionable review summary by making the source-archive download path verify bytes with `verify_archive_checksum` before extraction, return the verified digest through `install_ard_source_entry`/`install_ard_entry`, and expose it in install output like `skill+zip`. Add successful propagation, mismatch fail-closed, and existing-destination preservation tests while retaining all 72 previous regressions. Edit only `skills/capelry/scripts/capelry.py`, `tests/test_capelry_scripts.py`, and this plan. Run focused/full tests, py_compile, Ruff, built-in/official validation, and diff hygiene. Commit and push normally to `origin/feat/harness-compatible-skill-installs`, verify exact PR head, then publish an evidence-rich top-level response mapped to the original review only after the commit is in the PR. Await CI and run a fresh all-pages thread plus actionable-review closure scan.

## Pre-commit evidence

- Source-archive successful checksum propagation and mismatch destination-preservation tests — PASS.
- Full `python3 -m unittest discover -s tests` — PASS (73 tests; all 72 earlier regressions retained).
- Python compilation, Ruff `E4,E7,E9,F,I`, built-in validation, official `skills-ref==0.1.0`, and `git diff --check` — PASS.

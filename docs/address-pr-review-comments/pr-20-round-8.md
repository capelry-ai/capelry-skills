# PR 20 review-remediation plan — round 8

## Snapshot

- PR: https://github.com/capelry-ai/capelry-skills/pull/20
- Provider/local/origin head before edits: `96c346ccc992146daf3ce04136cc5f4b329cdfea`
- Push target: `origin HEAD:refs/heads/feat/harness-compatible-skill-installs` (normal, non-force)
- Initial scan: 22 total threads; 20 resolved/excluded; 2 unresolved; no thread/nested-comment pagination remainder
- Actionable non-thread feedback: none; review summary duplicates the threads below

## Worklist

| Thread | Concern | Disposition | Correction | Validation | Resolution condition |
| --- | --- | --- | --- | --- | --- |
| `PRRT_kwDOSR0Wxs6c8YTJ` | Plain scalar ending in `:` is accepted although YAML treats the terminal colon as a mapping separator | Fix | Extend every unquoted portable scalar/value check in both validators from colon-plus-whitespace to colon-plus-whitespace-or-end | direct scalar and metadata tests; forced-install preservation; full regression suite | pushed commit is PR head, evidence reply published, green CI |
| `PRRT_kwDOSR0Wxs6c8YTP` | Literal C1 controls except DEL are accepted | Fix | Reject YAML-forbidden U+007F–U+0084 and U+0086–U+009F (plus the remaining BMP noncharacters) in both validators while preserving allowed U+0085 and line parsing | forbidden/allowed character fixtures; forced-install preservation; full regression suite | same |

## Authorized action plan

Edit only `skills/capelry/scripts/capelry.py`, `skills/capelry/scripts/bootstrap.py`, `tests/test_capelry_scripts.py`, and this plan. Keep all 64 earlier tests and add direct plus both transactional-path regressions. Run focused tests, full unittest, py_compile, built-in validation, Ruff, official `skills-ref`, external YAML semantic comparison, helper parity, and diff hygiene. Commit locally, push normally, verify exact provider head and ancestry, then follow the user's requested ordering by publishing evidence-rich replies only after the commit is part of the PR. Await updated CI, recheck and resolve each thread, and repeat a fully paginated closure scan if new feedback arrives.

## Pre-commit evidence

- Focused terminal-colon, forbidden/allowed C1, and both transactional candidate-preservation tests — PASS.
- `python3 -m py_compile skills/capelry/scripts/capelry.py skills/capelry/scripts/bootstrap.py tests/test_capelry_scripts.py` — PASS.
- `python3 -m unittest discover -s tests` — PASS (66 tests, retaining all 64 earlier regressions).
- Built-in shipped-skill validation — PASS (`valid: true`, `portable: true`).
- Ruff `E4,E7,E9,F,I` — PASS.
- Official `skills-ref==0.1.0` — PASS (`Valid skill: skills/capelry`).
- PyYAML 6.0.2 rejects `foo:` and literal U+0080 while accepting U+0085; both validators match the required accept/reject boundary.
- Shared validator helper parity and `git diff --check` — PASS.

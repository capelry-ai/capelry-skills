# PR 20 review-remediation plan — round 9

## Snapshot and worklist

- PR: https://github.com/capelry-ai/capelry-skills/pull/20
- Initial exact local/origin/provider head: `34834578b21e8e8a3f7bfbd49a4949784f89cadc`
- Initial scan: 24 total threads; 22 resolved/excluded; 2 unresolved; no pagination remainder; no pending review/actionable non-thread feedback
- Push target: `origin HEAD:refs/heads/feat/harness-compatible-skill-installs` (normal, non-force)

| Thread | Concern | Disposition | Planned correction | Validation/resolution gate |
| --- | --- | --- | --- | --- |
| `PRRT_kwDOSR0Wxs6c8tUP` | Present optional scalar with no value resolves to null but is accepted | Fix | Require a non-comment value, quoted empty string, or explicit block scalar whenever any portable scalar field is declared; align both validators | direct optional-field tests, all earlier tests, both forced-replacement paths; pushed exact head, reply, green CI |
| `PRRT_kwDOSR0Wxs6c8tUW` | Comment-only metadata value resolves to null but is accepted | Fix | Reject metadata values empty after inline-comment removal while preserving explicit quoted `""` | same |

## Authorized action plan

Edit only both validators, regression tests, and this plan. Keep all 66 earlier tests and add targeted direct and transactional-preservation fixtures. Run focused tests, full unittest, py_compile, built-in and official skill validation, Ruff, PyYAML comparison, helper parity, and diff hygiene. Commit locally, push normally, verify exact PR head/ancestry, then follow the user's requested ordering by posting evidence-rich replies only after the commit is in the PR. Await updated CI, recheck and resolve eligible threads, update PR evidence, and run a fresh all-pages closure scan; repeat for any new unresolved feedback.

## Pre-commit evidence

- Focused optional-scalar and metadata null-vs-explicit-empty-string regressions — PASS.
- Registry and bootstrap forced-replacement preservation fixtures for both new failure shapes — PASS.
- `python3 -m py_compile ...` — PASS.
- `python3 -m unittest discover -s tests` — PASS (68 tests, retaining all 66 earlier regressions).
- Built-in validation and official `skills-ref==0.1.0` shipped-skill validation — PASS.
- Ruff `E4,E7,E9,F,I` and `git diff --check` — PASS.
- PyYAML 6.0.2 comparison confirms omitted/comment-only values resolve to null and quoted `""` resolves to a string — PASS.

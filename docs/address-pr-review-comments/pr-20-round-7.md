# PR 20 review-remediation plan — round 7

## Snapshot

- PR: https://github.com/capelry-ai/capelry-skills/pull/20
- Provider head before edits: `04086cace7049e9ea8fc30215ef86baef692a10a`
- Push target: `origin HEAD:refs/heads/feat/harness-compatible-skill-installs` (normal, non-force)
- Initial thread scan: 20 total, 16 resolved/excluded, 4 unresolved, no thread or nested-comment pagination remainder
- Actionable non-thread feedback: none; the latest review summary duplicates the four threads below

## Worklist

| Thread | Concern | Disposition | Planned correction | Validation | Resolution condition |
| --- | --- | --- | --- | --- | --- |
| `PRRT_kwDOSR0Wxs6c7M3R` | `|+` trailing newlines are discarded | Fix | Apply YAML strip/clip/keep chomping semantics when rendering literal and folded block scalars in both validators | focused chomp tests, PyYAML comparison, full regression suite | pushed commit at PR head, green CI, evidence reply |
| `PRRT_kwDOSR0Wxs6c7M3a` | bootstrap trims whitespace inside quoted scalars | Fix | Decode quoted scalars without trimming their content; retain external whitespace/comment handling | quoted name/length tests plus full suite | same |
| `PRRT_kwDOSR0Wxs6c7M3g` | tab-separated inline comments are not stripped | Fix | Scan outside quote state and recognize `#` after space or tab while preserving hashes inside quotes | tab-comment and quoted-hash tests plus full suite | same |
| `PRRT_kwDOSR0Wxs6c7M3n` | metadata duplicate detection compares raw rather than resolved keys | Fix | Decode valid quoted metadata keys before duplicate comparison in both validators | plain/single/double equivalent-key tests plus full suite | same |

## Action plan

Edit only `skills/capelry/scripts/capelry.py`, `skills/capelry/scripts/bootstrap.py`, and `tests/test_capelry_scripts.py`, plus this plan. Keep every earlier regression test intact and add forced-replacement preservation coverage for the newly malformed candidates. Run focused tests first, then `py_compile`, the complete unit suite, built-in validation, Ruff, official `skills-ref`, PyYAML semantic fixtures, and diff hygiene. Commit locally, push normally, verify the exact provider head and commit ancestry, then (per the user's requested ordering) post evidence-rich replies only after the fix commit is part of the PR. Wait for updated CI, recheck and resolve eligible threads one at a time, and run a fresh all-pages closure scan; repeat if new unresolved threads arrive.

## Pre-commit evidence

- Focused tests for chomping, quoted whitespace, tab comments, resolved metadata keys, block-header comments, and both transactional replacement paths — PASS.
- `python3 -m py_compile skills/capelry/scripts/capelry.py skills/capelry/scripts/bootstrap.py tests/test_capelry_scripts.py` — PASS.
- `python3 -m unittest discover -s tests` — PASS (64 tests, including every prior PR review regression).
- `python3 skills/capelry/scripts/capelry.py validate-skill skills/capelry --json` — PASS (`valid: true`, `portable: true`).
- `ruff check --no-cache --select E4,E7,E9,F,I ...` — PASS.
- Official `skills-ref==0.1.0`: `agentskills validate skills/capelry` — PASS (`Valid skill`).
- PyYAML 6.0.2 comparison — PASS for chomping forms, quoted whitespace and escapes, and resolved mapping keys; Ruby Psych comparison confirms tab-separated comments resolve per YAML grammar.
- Read-only adversarial review found one adjacent block-scalar/top-level-comment issue; both validators now distinguish unindented YAML comments from indented scalar content and the paired regression passes.
- `git diff --check` — PASS.

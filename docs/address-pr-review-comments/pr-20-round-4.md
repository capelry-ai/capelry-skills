# PR 20 review-remediation plan — round 4

Recorded: 2026-08-27

## Provider snapshot

- PR: https://github.com/capelry-ai/capelry-skills/pull/20
- Head repository/ref: `capelry-ai/capelry-skills:feat/harness-compatible-skill-installs`
- Snapshot head: `1efdf77b9d9195e569e6a390fbdd863fe0feed6c`
- Review-thread pagination: one page; three unresolved threads; five resolved threads excluded
- Actionable non-thread feedback: none (`@codex` comments are review triggers; the prior remediation summary is already complete)

## Worklist

| Unresolved thread | Reviewer ask | Disposition | Planned change and why | Validation | Resolution condition |
| --- | --- | --- | --- | --- | --- |
| [`PRRT_kwDOSR0Wxs6c5B2t`](https://github.com/capelry-ai/capelry-skills/pull/20#discussion_r3873619867) | Reject all forbidden YAML plain-scalar prefixes, including `@`. | fix | Add a shared prefix predicate in both dependency-free validators, apply it to every portable string scalar and metadata value, and add forced-install preservation coverage. | Focused prefix/install tests, PyYAML and official-validator fixtures, full gates. | Published after-push response, passing CI, final state recheck. |
| [`PRRT_kwDOSR0Wxs6c5B20`](https://github.com/capelry-ai/capelry-skills/pull/20#discussion_r3873619874) | Reject sequence-valued `metadata`; require a string-to-string mapping. | fix | Parse and type-check the complete indented metadata section in both validators, rejecting sequences, malformed/nested entries, duplicates, non-string values, tabs, and inline non-mapping shapes; add rollback coverage. | Focused metadata/install tests, official-validator fixtures, full gates. | Published after-push response, passing CI, final state recheck. |
| [`PRRT_kwDOSR0Wxs6c5B26`](https://github.com/capelry-ai/capelry-skills/pull/20#discussion_r3873619879) | Accept valid block indentation indicators and optional chomping modifiers. | fix | Expand the block-header grammar to `|`/`>` plus optional `1`-`9` indentation and `+`/`-` chomping indicators in either legal order; enforce explicit indentation in both validators and add valid-form coverage. | Focused block-header tests, PyYAML and official-validator fixtures, full gates. | Published after-push response, passing CI, final state recheck. |

## Authorized mutation sequence

1. Change only the two validators, regression tests, and this plan.
2. Commit as `fix(capelry): complete portable frontmatter validation`.
3. Post evidence-rich local-commit replies, push normally to the PR head branch, verify exact head/ancestry, then ensure after-push responses are published (submitting any pending reviews).
4. Wait for updated CI, recheck and resolve each fully addressed thread, verify mutations, and run a fresh all-pages closure scan.

## Pre-commit validation evidence

- Focused forbidden-prefix, metadata-shape, block-header, and forced-install preservation tests — PASS (4 tests)
- `python3 -m py_compile skills/capelry/scripts/capelry.py skills/capelry/scripts/bootstrap.py tests/test_capelry_scripts.py` — PASS
- `python3 skills/capelry/scripts/capelry.py validate-skill skills/capelry --json` — PASS (`valid: true`, `portable: true`)
- `python3 -m unittest discover -s tests` — PASS (56 tests)
- Ruff focused syntax/import checks — PASS
- Official `skills-ref==0.1.0` shipped-skill validation — PASS (`Valid skill`)
- PyYAML fixture comparison — PASS (`@` rejected, metadata sequence typed as a list, and all legal indicator/chomping orders accepted)
- `git diff --check` — PASS

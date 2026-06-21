# Capelry ARD-Native Registry Pivot — Skills Work Items

## Shared Tracker

Capelry Skills ARD client work is tracked in the shared Capelry AI GitHub Project:

- Project: <https://github.com/orgs/capelry-ai/projects/1/views/1>
- Organization: `capelry-ai`
- Repo: `capelry-ai/capelry-skills`
- Parent feature: <https://github.com/capelry-ai/capelry-skills/issues/6>

This repository uses the same y30k/agent-skill workflow as the other Capelry repos. Use the GitHub Project as the source of truth for status and dependency readiness.

## Shared Process

1. Use `manage-delivery-board` to inspect the shared project and identify Skills items whose GitHub `blocked by` relationships are fully resolved.
2. Use `implement-prd-stories` only for issues that are unblocked and in `Ready` or explicitly approved for implementation.
3. Keep dependency state in GitHub native relationships (`blocked by`, `blocking`, parent/sub-issue). Do not encode blockers only in labels or prose.
4. Run the validation named in the issue before handing off for review.
5. Use `review-pull-request`, `address-pr-review-comments`, and `check-production-readiness` for PR and release gates.
6. If repo-local docs disagree with the GitHub Project, trust the GitHub Project and update the docs.

## Source Planning Docs

The primary planning artifacts live in the sibling registry repo when working in the standard Capelry checkout:

- `../capelry-registry/docs/prds/capelry-ard-registry-alignment.prd.md`
- `../capelry-registry/docs/technical-designs/capelry-ard-native-registry-pivot.technical-design.md`
- `../capelry-registry/docs/test-strategies/capelry-ard-native-registry-pivot.test-strategy.md`
- `../capelry-registry/docs/prd-work-items/capelry-ard-native-registry-pivot.posted.md`

## Skills Work Queue

| ID    | Issue                                                                                                                             | Status at posting | Blocked by                                                                                                                                  | Validation                                                                                                                             |
| ----- | --------------------------------------------------------------------------------------------------------------------------------- | ----------------- | ------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| `P4`  | [#6 — Make Capelry Skills the reference ARD client and installer](https://github.com/capelry-ai/capelry-skills/issues/6)          | Done              | none                                                                                                                                        | Python test/compile gates across children                                                                                              |
| `K01` | [#7 — Add Python test harness and CI for Capelry skill scripts](https://github.com/capelry-ai/capelry-skills/issues/7)            | Done              | none                                                                                                                                        | `python3 -m unittest discover -s tests`; `python3 -m py_compile skills/capelry/scripts/capelry.py skills/capelry/scripts/bootstrap.py` |
| `K02` | [#8 — Add ARD client transport, models, and filter mapping](https://github.com/capelry-ai/capelry-skills/issues/8)                | Done              | [`R01`](https://github.com/capelry-ai/capelry-registry/issues/17), [`R02`](https://github.com/capelry-ai/capelry-registry/issues/18), `K01` | Python unit/subprocess tests with fixture server                                                                                       |
| `K03` | [#9 — Switch search, discover, and info commands to ARD by default](https://github.com/capelry-ai/capelry-skills/issues/9)        | Done              | [`R09`](https://github.com/capelry-ai/capelry-registry/issues/25), `K02`                                                                    | Python unit/subprocess tests with fixture server                                                                                       |
| `K04` | [#10 — Install supported ARD media types with trust and checksum display](https://github.com/capelry-ai/capelry-skills/issues/10) | Done              | [`R04`](https://github.com/capelry-ai/capelry-registry/issues/20), `K02`, `K03`                                                             | Python tests with temp dirs and fixture archives                                                                                       |
| `K05` | [#11 — Publish Capelry skill ARD self-entry and update bootstrap/docs](https://github.com/capelry-ai/capelry-skills/issues/11)    | Done              | `K03`, `K04`                                                                                                                                | Python tests; `py_compile`; manual bootstrap/self-update smoke when network is available                                               |

## Cross-Repo Dependencies

Important registry dependencies:

- [`R01`](https://github.com/capelry-ai/capelry-registry/issues/17): pinned ARD schemas and field-policy ADR.
- [`R02`](https://github.com/capelry-ai/capelry-registry/issues/18): shared ARD fixture corpus.
- [`R04`](https://github.com/capelry-ai/capelry-registry/issues/20): ARD URN/media/trust/page-token utilities and media policy.
- [`R09`](https://github.com/capelry-ai/capelry-registry/issues/25): public ARD `/search`, `/explore`, and `/agents` contract.

Cross-repo release gates:

- [`X01`](https://github.com/capelry-ai/capelry-registry/issues/33): cross-repo ARD happy-path smoke test.
- [`X02`](https://github.com/capelry-ai/capelry-registry/issues/34): production readiness, migration review, and post-release observation plan.

## Current Next Action

[`P4`](https://github.com/capelry-ai/capelry-skills/issues/6) and all child Skills stories [`K01`](https://github.com/capelry-ai/capelry-skills/issues/7) through [`K05`](https://github.com/capelry-ai/capelry-skills/issues/11) are complete. No remaining Capelry Skills ARD client stories are ready in this work queue.

## Skills Validation Gates

Current minimum validation:

```bash
python3 -m py_compile skills/capelry/scripts/capelry.py skills/capelry/scripts/bootstrap.py
```

Target validation after `K01` lands:

```bash
python3 -m unittest discover -s tests
python3 -m py_compile skills/capelry/scripts/capelry.py skills/capelry/scripts/bootstrap.py
```

Do not mark a Skills item done until the issue-specific validation and the shared project dependency state are both satisfied.

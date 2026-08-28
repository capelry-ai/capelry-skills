# PR 20 review-remediation plan — round 3

Recorded: 2026-08-27

## Provider snapshot

- PR: https://github.com/capelry-ai/capelry-skills/pull/20
- Head repository/ref: `capelry-ai/capelry-skills:feat/harness-compatible-skill-installs`
- Snapshot head: `7bbec68e2db52574b4fc861e3ed878ef9e904bda`
- Review-thread pagination: one page; three unresolved threads; two resolved threads excluded
- Actionable non-thread feedback: none (the two `@codex` comments are review triggers)

## Worklist

| Unresolved thread | Reviewer ask | Disposition | Planned change and why | Validation | Resolution condition |
| --- | --- | --- | --- | --- | --- |
| [`PRRT_kwDOSR0Wxs6c4Z9V`](https://github.com/capelry-ai/capelry-skills/pull/20#discussion_r3873376377) | Reject sequence-valued `compatibility` before replacement. | fix | Apply scalar-shape checks to every portable scalar field (`name`, `description`, `license`, `compatibility`, and `allowed-tools`) in `skills/capelry/scripts/capelry.py`; add schema and forced-install rollback regressions. | Focused schema/install tests plus full gates. | Evidence reply, verified push/follow-up, passing updated CI, final unresolved-state recheck. |
| [`PRRT_kwDOSR0Wxs6c4Z9b`](https://github.com/capelry-ai/capelry-skills/pull/20#discussion_r3873376386) | Reject inconsistent or tab-indented block scalars before replacement. | fix | Validate block-scalar indentation in both dependency-free validators, retaining valid consistently indented `|`/`>` values; add direct and forced-install rollback regressions. | Focused block-scalar/install tests plus full gates. | Evidence reply, verified push/follow-up, passing updated CI, final unresolved-state recheck. |
| [`PRRT_kwDOSR0Wxs6c4Z9g`](https://github.com/capelry-ai/capelry-skills/pull/20#discussion_r3873376394) | Reject duplicate top-level bootstrap frontmatter fields before replacement. | fix | Scan the complete bootstrap frontmatter for duplicate top-level keys before reading required values; add direct and bootstrap replacement-preservation regressions. | Focused bootstrap tests plus full gates. | Evidence reply, verified push/follow-up, passing updated CI, final unresolved-state recheck. |

## Authorized mutation sequence

1. Change only `skills/capelry/scripts/capelry.py`, `skills/capelry/scripts/bootstrap.py`, `tests/test_capelry_scripts.py`, and this plan.
2. Commit as `fix(capelry): harden frontmatter schema validation`.
3. Recheck all three threads and post one independently auditable local-commit reply to each.
4. Push normally to `origin HEAD:refs/heads/feat/harness-compatible-skill-installs`, verify the commit is on the exact PR head, then post a push-verification follow-up to each still-unresolved thread.
5. Wait for updated CI, recheck each thread, resolve each fully addressed thread, and verify every mutation.
6. Run a fresh all-pages thread scan bound to the exact final PR head and repeat remediation if new unresolved threads arrived.

## Pre-commit validation evidence

- Focused tests for optional scalar shape, block indentation, forced-install preservation, and duplicate bootstrap fields — PASS (4 tests)
- `python3 -m py_compile skills/capelry/scripts/capelry.py skills/capelry/scripts/bootstrap.py tests/test_capelry_scripts.py` — PASS
- `python3 skills/capelry/scripts/capelry.py validate-skill skills/capelry --json` — PASS (`valid: true`, `portable: true`)
- `python3 -m unittest discover -s tests` — PASS (54 tests)
- `ruff check --no-cache --select E4,E7,E9,F,I skills/capelry/scripts/capelry.py skills/capelry/scripts/bootstrap.py tests/test_capelry_scripts.py` — PASS
- `agentskills validate skills/capelry` with official `skills-ref==0.1.0` — PASS (`Valid skill`)
- Official `skills-ref==0.1.0` invalid-fixture checks — PASS (sequence `compatibility`, uneven block indentation, and duplicate top-level fields all rejected)
- PyYAML fixture comparison — PASS (sequence parsed as a list; uneven and tab-indented block scalars rejected)
- `git diff --check` — PASS

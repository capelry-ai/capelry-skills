# PR 20 review-remediation plan — round 2

Recorded: 2026-08-27

## Provider snapshot

- PR: https://github.com/capelry-ai/capelry-skills/pull/20
- Head repository/ref: `capelry-ai/capelry-skills:feat/harness-compatible-skill-installs`
- Snapshot head: `65fa171b52ade3d72f4e6ed223e4660b9db8e933`
- Review-thread pagination: one page; one unresolved thread; one resolved thread excluded
- Actionable non-thread feedback: none (`@codex` is a review trigger, not a remediation request)

## Worklist

| Unresolved thread | Reviewer ask | Disposition | Planned change and why | Validation | Resolution condition |
| --- | --- | --- | --- | --- | --- |
| [`PRRT_kwDOSR0Wxs6c3t-3`](https://github.com/capelry-ai/capelry-skills/pull/20#discussion_r3873109820) | Reject malformed YAML single-quoted scalars such as `description: 'it's useful'` before `install --force` can replace a working skill. | fix | Make `parse_yaml_scalar` in `skills/capelry/scripts/capelry.py` fail closed when an interior apostrophe is not escaped as `''`, apply the same rule in `skills/capelry/scripts/bootstrap.py`, and add valid-escaping plus validator/install/bootstrap regressions in `tests/test_capelry_scripts.py`. | Focused regressions; full `unittest`; Python compilation; bundled and official Agent Skills validation; Ruff; PyYAML fixture comparison; diff hygiene. | Evidence-rich local-commit reply succeeds; push succeeds and a follow-up confirms the cited commit is on the exact PR head; updated CI passes; thread remains unresolved and resolvable immediately before resolution. |

## Authorized mutation sequence

1. Change only the two validators, their regression tests, and this plan.
2. Stage exactly `skills/capelry/scripts/capelry.py`, `skills/capelry/scripts/bootstrap.py`, `tests/test_capelry_scripts.py`, and this plan.
3. Commit as `fix(capelry): validate YAML single quotes`.
4. Recheck the thread and post an evidence-rich reply citing the local commit.
5. Push normally to `origin HEAD:refs/heads/feat/harness-compatible-skill-installs`, verify the commit is on the exact PR head, then post a push-verification follow-up so the thread response also records the commit after it is part of the PR.
6. Wait for required CI, recheck the thread, resolve it, and verify resolution.
7. Run a fresh all-pages thread scan bound to the exact final PR head; remediate any newly arrived unresolved threads before reporting completion.

## Pre-commit validation evidence

- `python3 -m unittest discover -s tests -k escaped_yaml_single_quotes` — PASS (1 test)
- `python3 -m unittest discover -s tests -k malformed_single_quote_cannot_replace` — PASS (1 test)
- `python3 -m py_compile skills/capelry/scripts/capelry.py skills/capelry/scripts/bootstrap.py tests/test_capelry_scripts.py` — PASS
- `python3 skills/capelry/scripts/capelry.py validate-skill skills/capelry --json` — PASS (`valid: true`, `portable: true`)
- `python3 -m unittest discover -s tests` — PASS (50 tests)
- `ruff check --no-cache --select E4,E7,E9,F,I skills/capelry/scripts/capelry.py skills/capelry/scripts/bootstrap.py tests/test_capelry_scripts.py` — PASS
- `agentskills validate skills/capelry` with official `skills-ref==0.1.0` — PASS (`Valid skill`)
- PyYAML fixture comparison — PASS (escaped `''` accepted and decoded; unescaped apostrophe rejected)
- `git diff --check` — PASS

# PR 20 review-remediation plan

Recorded: 2026-08-27

## Provider snapshot

- PR: https://github.com/capelry-ai/capelry-skills/pull/20
- Head repository/ref: `capelry-ai/capelry-skills:feat/harness-compatible-skill-installs`
- Snapshot head: `97b353452da2e38db41a0f15f12b8491a6a64ac7`
- Review-thread pagination: one page; one unresolved thread; zero resolved threads excluded
- Actionable non-thread feedback: none (the Codex review summary only introduces the inline thread)

## Worklist

| Unresolved thread | Reviewer ask | Disposition | Planned change and why | Validation | Resolution condition |
| --- | --- | --- | --- | --- | --- |
| [`PRRT_kwDOSR0Wxs6c3J5A`](https://github.com/capelry-ai/capelry-skills/pull/20#discussion_r3872889149) | Reject malformed YAML where an indented continuation follows a non-block inline scalar, before `install --force` can replace a working skill. | fix | Update `parse_skill_frontmatter` in `skills/capelry/scripts/capelry.py` to reject non-block continuations, apply the same fail-closed rule in `skills/capelry/scripts/bootstrap.py`, and add validator/install/bootstrap regressions in `tests/test_capelry_scripts.py`. This keeps the dependency-free installers while accepting explicit `>`/`|` multiline scalars. | Focused regression tests; full `unittest`; Python compilation; bundled and official Agent Skills validation; Ruff; diff hygiene. | Reply cites the local fix commit and evidence; normal push succeeds; cited commit is on the exact PR head; updated CI passes; thread remains unresolved and resolvable immediately before resolution. |

## Authorized mutation sequence

1. Change only the two validators, their regression tests, and this plan.
2. Stage exactly `skills/capelry/scripts/capelry.py`, `skills/capelry/scripts/bootstrap.py`, `tests/test_capelry_scripts.py`, and this plan.
3. Commit as `fix(capelry): reject invalid YAML continuations`.
4. Recheck the thread and post an evidence-rich reply citing the local commit.
5. Push normally to `origin HEAD:refs/heads/feat/harness-compatible-skill-installs`.
6. Verify the cited commit is the provider-reported PR head (or its ancestor), wait for required CI, recheck the thread, resolve it, and verify resolution.
7. Run a fresh all-pages thread scan bound to the exact final PR head; remediate any newly arrived unresolved threads before reporting completion.

## Pre-commit validation evidence

- `python3 -m unittest discover -s tests -k non_block_scalar_continuations` — PASS (1 test)
- `python3 -m unittest discover -s tests -k malformed_yaml_cannot_replace` — PASS (1 test)
- `python3 -m py_compile skills/capelry/scripts/capelry.py skills/capelry/scripts/bootstrap.py tests/test_capelry_scripts.py` — PASS
- `python3 skills/capelry/scripts/capelry.py validate-skill skills/capelry --json` — PASS (`valid: true`, `portable: true`)
- `python3 -m unittest discover -s tests` — PASS (48 tests)
- `ruff check --no-cache --select E4,E7,E9,F,I skills/capelry/scripts/capelry.py skills/capelry/scripts/bootstrap.py tests/test_capelry_scripts.py` — PASS
- `agentskills validate skills/capelry` with official `skills-ref==0.1.0` — PASS (`Valid skill`)
- PyYAML fixture check — PASS (the reviewer-provided malformed continuation is rejected as YAML)
- `git diff --check` — PASS

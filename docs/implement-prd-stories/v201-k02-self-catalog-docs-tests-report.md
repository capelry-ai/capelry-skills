# V201-K02 Skills Self Catalog, Docs, Bootstrap, and Tests Report

## Source

- Tracker: capelry-ai/capelry-skills#16 — `[skills] v2.0.1 update self ARD catalog, docs, bootstrap copy, and tests`
- Project: <https://github.com/orgs/capelry-ai/projects/1>
- Supporting staged docs reviewed in `../capelry-registry/docs/`:
  - `docs/prd-work-items/capelry-v2-0-1-ard-only-cutover.posted.md`
  - `docs/technical-designs/capelry-v2-0-1-ard-only-cutover.technical-design.md`
  - `docs/test-strategies/capelry-v2-0-1-ard-only-cutover.test-strategy.md`
- Companion design: `docs/technical-designs/capelry-skills-v2-0-1-ard-only-registry-cutover.technical-design.md`

## Readiness

- capelry-ai/capelry-skills#15 was closed/done and its project status moved to `Done`.
- capelry-ai/capelry-skills#16's only native blocker is #15, now closed.
- #16 project status was moved to `In progress` before implementation.

## Implementation Summary

The Capelry skill self AI Catalog entry now publishes `com.capelry.slug` and no longer publishes `com.capelry.legacyRef`. Public README, skill instructions, and bootstrap copy now describe ARD-only discovery/install flows and slug-based `namespace/name` resolution without active old compatibility API, `--api legacy`, environment fallback, or legacy bulk endpoint instructions. Tests now validate the self-entry slug metadata and absence of the removed metadata key without causing the no-legacy grep gate to fail.

## Changed Files

- `skills/capelry/ai-catalog.json` — replaced `com.capelry.legacyRef` with `com.capelry.slug`.
- `tests/test_capelry_scripts.py` — updated self-entry assertions for slug metadata and removed grep-blocking legacyRef literals.
- `README.md` — removed legacy fallback/API selector/bulk compatibility examples and documented ARD slug resolution.
- `skills/capelry/SKILL.md` — updated workflow and command docs to ARD slug-only behavior.
- `skills/capelry/BOOTSTRAP.md` — removed old compatibility API guidance and documented ARD slug inspection before install.

## Validation Summary

- `python3 -m py_compile skills/capelry/scripts/capelry.py skills/capelry/scripts/bootstrap.py` — pass.
- `python3 -m unittest discover -s tests` — pass, 17 tests.
- `rg -n "legacyRef|legacy ref|/api/capabilities|--api legacy|CAPELRY_USE_LEGACY_API" skills/capelry README.md tests || true` — pass, no matches.
- `rg -n "bulk-info|--api" README.md skills/capelry/SKILL.md skills/capelry/BOOTSTRAP.md || true` — pass, no active docs matches.

## Tracker Updates

- capelry-ai/capelry-skills#15 acceptance criteria were marked complete, completion comment added, issue closed, and project status moved to `Done`.
- capelry-ai/capelry-skills#16 project status moved to `In progress`; start comment added.
- #16 acceptance criteria were marked complete, completion comment added, issue closed, and project status moved to `Done`.

## Remaining Work or Risks

- capelry-ai/capelry-registry#49 cross-repo smoke remains blocked by capelry-ai/capelry-repo-sync#13, which is still open/in review.
- Source changes are local and not committed/pushed in this pass.

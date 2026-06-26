# V201-K01 Skills Slug Resolution Implementation Report

## Source

- Tracker: capelry-ai/capelry-skills#15 — `[skills] v2.0.1 replace legacyRef and legacy API fallback with ARD slug resolution`
- Project: <https://github.com/orgs/capelry-ai/projects/1>
- Supporting staged docs reviewed in `../capelry-registry/docs/`:
  - `docs/prd-work-items/capelry-v2-0-1-ard-only-cutover.posted.md`
  - `docs/technical-designs/capelry-v2-0-1-ard-only-cutover.technical-design.md`
  - `docs/test-strategies/capelry-v2-0-1-ard-only-cutover.test-strategy.md`
- Companion design: `docs/technical-designs/capelry-skills-v2-0-1-ard-only-registry-cutover.technical-design.md`

## Readiness

- Project status was `Ready`.
- Native `blockedBy` relationship points only to capelry-ai/capelry-registry#40, which is closed/done.
- Scope is owned by `capelry-ai/capelry-skills` and has observable acceptance criteria plus Python validation gates.

## Implementation Summary

The Capelry CLI now treats ARD as the only registry API for search, discover, info, bulk-info, and install flows. Human `namespace/name` refs resolve via `metadata.com.capelry.slug`; outputs expose `slug` instead of legacy ref fields; `--api` selection, environment-driven legacy selection, automatic compatibility fallback, and legacy capability download/install paths were removed from active CLI behavior. `bulk-info` is retained as an ARD-native multi-ref resolver over `/agents`.

## Changed Files

- `skills/capelry/scripts/capelry.py` — replaced ARD legacy-ref constants with slug constants, changed non-URN resolution to slug filters, removed active legacy API fallback/selection/install paths, rewrote command flows as ARD-only, and changed JSON/text outputs and install destination naming to use slugs.
- `tests/test_capelry_scripts.py` — updated fixture ARD metadata to `com.capelry.slug`, removed old compatibility endpoint emulation, added assertions for slug filter resolution, no unexpected compatibility calls, removed API-selector behavior, and added ARD-native `bulk-info` coverage.

## Validation Summary

- `python3 -m py_compile skills/capelry/scripts/capelry.py skills/capelry/scripts/bootstrap.py` — pass.
- `python3 -m unittest discover -s tests` — pass, 17 tests.
- `rg -n "legacyRef|legacy ref|/api/capabilities|--api legacy|CAPELRY_USE_LEGACY_API" skills/capelry/scripts/capelry.py tests/test_capelry_scripts.py || true` — passed after V201-K02 cleanup, no matches.

## Tracker Updates

- capelry-ai/capelry-skills#15 acceptance criteria were marked complete.
- Completion comment with validation was added to #15.
- #15 was closed as completed and its project status moved to `Done`.
- capelry-ai/capelry-skills#16 was moved to `In progress` after #15 closed.

## Remaining Work or Risks

- Cross-repo smoke remains blocked by Repo Sync review completion and registry release-gate work.
- Source changes are local and not committed/pushed in this pass.

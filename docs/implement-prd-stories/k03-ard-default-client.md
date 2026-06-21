# K03 — Switch Search, Discover, and Info to ARD by Default

## Implementation Plan

**Story**: capelry-ai/capelry-skills#9 — `[skills] Switch search, discover, and info commands to ARD by default`

**Why ready**: GitHub Project 1 marks #9 as `Ready`; native issue dependency summary reports `blockedBy: 0`. Closed blockers: capelry-skills#8 and capelry-registry#25.

**Scope**:
- Make `search`, `discover`, and `info` use ARD endpoints by default.
- Keep legacy `/api/capabilities` reads available only through explicit `--api legacy` or `CAPELRY_USE_LEGACY_API=1`.
- Have `discover` batch ARD `/search` requests and dedupe by `identifier` instead of calling legacy bulk info.
- Have `info` resolve `urn:ai:...` identifiers and legacy `namespace/name` refs through ARD `/agents` filters.
- Update tests and agent-facing docs for default ARD behavior.

**Files touched**:
- `skills/capelry/scripts/capelry.py`
- `skills/capelry/SKILL.md`
- `tests/test_capelry_scripts.py`
- `README.md`
- `docs/implement-prd-stories/k03-ard-default-client.md`

**Acceptance criteria**:
- Default CLI requests hit `/search`.
- Output includes URN, display name, media type, score, source, and trust state.
- Legacy ref resolution works through ARD metadata alias.
- Legacy `/api/capabilities` calls require explicit flag/env.

**Validation**:
- `python3 -m unittest discover -s tests`
- `python3 -m py_compile skills/capelry/scripts/capelry.py skills/capelry/scripts/bootstrap.py`

## Result

Implemented and validated locally. Tracker status will be updated after validation evidence is posted.

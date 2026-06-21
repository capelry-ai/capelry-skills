# K04 — Install Supported ARD Media Types with Trust and Checksum Display

## Implementation Plan

**Story**: capelry-ai/capelry-skills#10 — `[skills] Install supported ARD media types with trust and checksum display`

**Why ready**: GitHub Project 1 moved #10 to `In progress`; native issue dependency summary reports `blockedBy: 0`. Closed blockers: capelry-registry#20, capelry-skills#8, and capelry-skills#9.

**Scope**:
- Make `install` resolve ARD entries by `urn:ai:...` identifier or legacy `namespace/name` metadata alias by default.
- Support `application/vnd.capelry.skill+zip` installs with SHA-256 verification when checksum metadata is present.
- Support `application/vnd.capelry.skill-source+json` installs from pinned source descriptors, using declared source archives or GitHub source path/ref.
- Reuse safe zip extraction so path traversal and archives without `SKILL.md` fail closed.
- Refuse unsupported ARD media types with open/connect guidance.
- Print trust state, checksum, Trust Manifest identity, and provenance before non-JSON installs.
- Keep legacy archive install available only through `--api legacy` or `CAPELRY_USE_LEGACY_API=1`.

**Files touched**:
- `skills/capelry/scripts/capelry.py`
- `skills/capelry/SKILL.md`
- `tests/test_capelry_scripts.py`
- `README.md`
- `docs/implement-prd-stories/k04-ard-media-install.md`

**Acceptance criteria**:
- Zip install verifies checksum and extracts safely.
- Source install uses pinned descriptor/ref where possible.
- Zip traversal/unsafe archive fixtures fail.
- Unsupported media types do not auto-install.

**Validation**:
- `python3 -m unittest discover -s tests`
- `python3 -m py_compile skills/capelry/scripts/capelry.py skills/capelry/scripts/bootstrap.py`

## Result

Implemented and validated locally. Tracker status will be updated after validation evidence is posted.

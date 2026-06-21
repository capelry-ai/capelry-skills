# K05 — Capelry Skill ARD Self-Entry and ARD-First Bootstrap Docs

## Implementation Plan

**Story**: capelry-ai/capelry-skills#11 — `[skills] Publish Capelry skill ARD self-entry and update bootstrap/docs`

**Why ready**: GitHub Project 1 moved #11 to `In progress`; native issue dependency summary reports `blockedBy: 0`. Closed blockers: capelry-skills#9 and capelry-skills#10.

**Scope**:
- Add an AI Catalog/ARD self-entry for the Capelry skill.
- Include the self-entry in the legacy Capelry package manifest as a required asset/additional doc.
- Update README, SKILL, and BOOTSTRAP examples to describe ARD-first search/info/install defaults.
- Preserve GitHub-source bootstrap and self-update flows as the trust bootstrap path.
- Add Python fixture validation for the self-entry shape.

**Files touched**:
- `skills/capelry/ai-catalog.json`
- `skills/capelry/capability.yaml`
- `skills/capelry/BOOTSTRAP.md`
- `skills/capelry/SKILL.md`
- `README.md`
- `tests/test_capelry_scripts.py`
- `docs/implement-prd-stories/k05-capelry-ard-self-entry.md`

**Acceptance criteria**:
- Self-entry validates against pinned fixture expectations.
- Docs show ARD search/info/install by default.
- Version and self-update smoke still pass or are updated intentionally.

**Validation**:
- `python3 -m unittest discover -s tests`
- `python3 -m py_compile skills/capelry/scripts/capelry.py skills/capelry/scripts/bootstrap.py`
- `python3 skills/capelry/scripts/capelry.py version --ref main`
- `python3 skills/capelry/scripts/capelry.py self-update --ref main --dry-run --force`

## Result

Implemented and validated locally. Tracker status will be updated after validation evidence is posted.

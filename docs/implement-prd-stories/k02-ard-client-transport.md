# K02 — ARD Client Transport, Models, and Filter Mapping

## Implementation Plan

**Story**: capelry-ai/capelry-skills#8 — `[skills] Add ARD client transport, models, and filter mapping`

**Why ready**: GitHub Project 1 marks #8 as `Ready`; native issue dependency summary reports `blockedBy: 0`. Closed blockers: capelry-skills#7, capelry-registry#17, and capelry-registry#18.

**Scope**:
- Add stdlib ARD transport helpers for `POST /search` and `GET /agents`.
- Add ARD error parsing for `{errorCode,message}` responses.
- Map `--type skill` to supported Capelry skill media types.
- Add ARD opt-in CLI filters: `--media-type`, `--publisher`, `--trust-state`, and generic `--filter FIELD=VALUE`.
- Keep legacy API behavior unchanged unless ARD is explicitly selected with `--api ard`.

**Files touched**:
- `skills/capelry/scripts/capelry.py`
- `tests/test_capelry_scripts.py`
- `README.md`

**Acceptance criteria**:
- ARD request payloads match the pinned `/search` shape: `query.text`, optional `query.filter`, `federation`, and `pageSize`.
- ARD errors are displayed clearly.
- Legacy fallback remains opt-in/no automatic fallback when using ARD mode.

**Validation**:
- `python3 -m unittest discover -s tests`
- `python3 -m py_compile skills/capelry/scripts/capelry.py skills/capelry/scripts/bootstrap.py`

## Result

Implemented and validated locally. No tracker status update was made.

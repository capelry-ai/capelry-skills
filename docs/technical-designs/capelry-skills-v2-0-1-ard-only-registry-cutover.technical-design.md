# Capelry Skills v2.0.1 ARD-Only Registry Cutover Technical Design

## Inputs

- Upstream registry design: `../capelry-registry/docs/technical-designs/capelry-v2-0-1-ard-only-cutover.technical-design.md`
- Trigger: Capelry Registry v2.0.1 will remove legacy capability compatibility as a source of truth and make ARD the only registry contract.
- Target repo/system: `capelry-ai/capelry-skills`, especially the bundled Capelry CLI in `skills/capelry/scripts/capelry.py`, self ARD catalog entry, docs, and test fixture server.
- Approval state: Companion design for the Capelry Skills team to pick up after registry v2.0.1 design approval.

## Summary

Capelry Skills is already ARD-first, but it still depends on legacy compatibility concepts for `namespace/name` resolution, output labels, fallback behavior, docs, tests, and explicit `--api legacy` flows. For v2.0.1, update the Capelry skill so the latest client speaks ARD only: resolve human refs through `metadata.com.capelry.slug`, remove old `/api/capabilities` fallbacks and bulk compatibility commands, publish its own ARD entry with `com.capelry.slug`, and update docs/tests to stop producing or asserting `com.capelry.legacyRef`.

## Codebase Findings

- `skills/capelry/scripts/capelry.py:42` — the CLI defines `ARD_LEGACY_REF_FILTER = "metadata.com.capelry.legacyRef"`.
- `skills/capelry/scripts/capelry.py:44` — the CLI defines `ARD_LEGACY_REF_METADATA = "com.capelry.legacyRef"`.
- `skills/capelry/scripts/capelry.py:257` — the CLI can automatically fall back from ARD to the old compatibility API for selected ARD errors.
- `skills/capelry/scripts/capelry.py:375` — legacy detail lookup calls `GET /api/capabilities/{namespace}/{name}`.
- `skills/capelry/scripts/capelry.py:422` — legacy search calls `GET /api/capabilities`.
- `skills/capelry/scripts/capelry.py:540` — ARD output exposes `legacyRef` from ARD metadata.
- `skills/capelry/scripts/capelry.py:567` — non-URN ARD resolution uses the legacyRef metadata filter.
- `skills/capelry/scripts/capelry.py:574` — ARD detail summaries still compute `legacy_ref` from legacy metadata.
- `skills/capelry/scripts/capelry.py:610` — human output prints `legacy ref:`.
- `skills/capelry/scripts/capelry.py:770` — bulk info posts to `/api/capabilities/bulk`.
- `skills/capelry/scripts/capelry.py:1431` — install logic uses `ard_legacy_ref`.
- `skills/capelry/scripts/capelry.py:1441` — install destination names prefer the legacy ref suffix.
- `skills/capelry/scripts/capelry.py:1520` — install resolution delegates to `ard_resolution_field`, so `namespace/name` installs currently depend on legacyRef metadata.
- `skills/capelry/scripts/capelry.py:1565` — `command_install_legacy` downloads old compatibility archives.
- `skills/capelry/scripts/capelry.py:2009`, `:2035`, `:2056`, `:2077` — CLI parser exposes `--api legacy|ard` on search/discover/info/install.
- `skills/capelry/scripts/capelry.py:2064` — CLI parser exposes `bulk-info` as a compatibility bulk API command.
- `skills/capelry/ai-catalog.json:31` — Capelry skill self-entry publishes `com.capelry.legacyRef`.
- `skills/capelry/SKILL.md:75` — docs describe fallback to the old compatibility API.
- `skills/capelry/SKILL.md:192` — docs describe resolving `namespace/name` through `metadata.com.capelry.legacyRef`.
- `skills/capelry/SKILL.md:196` — docs tell users to use `bulk-info` only for legacy compatibility.
- `skills/capelry/BOOTSTRAP.md:219` — bootstrap docs include `--api legacy` and `bulk-info` examples.
- `tests/test_capelry_scripts.py:99` and nearby fixtures — ARD test fixtures publish `com.capelry.legacyRef`.
- `tests/test_capelry_scripts.py:218` and `:243` — test fixture server still emulates `/api/capabilities` routes.
- `tests/test_capelry_scripts.py:546` and `:550` — tests assert `legacyRef` output and `metadata.com.capelry.legacyRef` filters.
- `tests/test_capelry_scripts.py:719` — self-entry test asserts `com.capelry.legacyRef`.

## Decisions

| Decision | Choice | Alternatives | Rationale | Reversible? |
| --- | --- | --- | --- | --- |
| Human ARD ref metadata | Use `com.capelry.slug` / `metadata.com.capelry.slug` | Keep `legacyRef`; resolve only URNs | Preserves ergonomic `namespace/name` refs without legacy semantics. | Yes |
| Default and only registry API | ARD only | Keep explicit `--api legacy`; fallback on ARD errors | Registry v2.0.1 returns `410` or removes old compatibility JSON. Keeping fallback creates confusing failures. | Yes, but not recommended |
| CLI output label | `slug` or `ref`, not `legacyRef` | Keep old output key for compatibility | Latest skill should not expose legacy concepts. | Yes |
| `bulk-info` | Remove or convert to an ARD-native multi-ref command | Keep `/api/capabilities/bulk` call | Old bulk API will no longer be a supported registry contract. | Yes |
| Install destination naming | Prefer slug name segment, then identifier/display name | Keep legacyRef name segment | Same UX without old metadata key. | Yes |
| Self ARD entry | Replace `com.capelry.legacyRef` with `com.capelry.slug` | Publish both during transition | Strict ARD-only goal means no legacy metadata in the published catalog. | Yes |
| Older installed clients | Users self-update from GitHub; old clients may fail legacy commands after registry cutover | Maintain old registry compatibility forever | Self-update path does not depend on registry compatibility. | Partially |

## Proposed Architecture

### Metadata contract

Define new constants in `skills/capelry/scripts/capelry.py`:

```python
ARD_SLUG_FILTER = "metadata.com.capelry.slug"
ARD_SLUG_METADATA = "com.capelry.slug"
```

Use `slug` as the human-friendly ARD ref for Capelry package entries. A slug has the existing `namespace/name` shape, but it is now just ARD metadata used for routing and CLI ergonomics.

### Resolution behavior

- If input starts with `urn:ai:`, resolve with:
  - `GET /agents?filter=identifier = 'urn:ai:...'&pageSize=1`
- Otherwise resolve with:
  - `GET /agents?filter=metadata.com.capelry.slug = 'namespace/name'&pageSize=1`
- Do not query `metadata.com.capelry.legacyRef`.
- Do not fallback to `/api/capabilities`.

### Search/discover behavior

- Continue using `POST /search`.
- Keep ARD filters for type, publisher, trust state, validation, source, domain, phase, and generic `--filter`.
- Output should include `slug` when present.
- Install snippets should use slug when present, else identifier.

### Info behavior

- `info namespace/name` means ARD slug lookup.
- `info urn:ai:...` means ARD identifier lookup.
- JSON output should expose `slug`, not `legacyRef`.
- Human output should print `slug:` or `ref:`.

### Install behavior

- `install namespace/name` means ARD slug lookup.
- Zip installs use the ARD entry `url` or `com.capelry.archiveUrl` and checksum metadata/trust manifest.
- Source installs use ARD source descriptor data or source metadata.
- Unsupported media type behavior remains unchanged.
- Remove `command_install_legacy` and old archive fallback logic.

### Bulk behavior

Preferred v2.0.1 implementation:

- Remove `bulk-info` and document `discover` + repeated `info` for shortlisted entries.

Acceptable implementation if the team wants to preserve the command name:

- Reimplement `bulk-info` as ARD-native:
  - for each ref, resolve identifier or slug through `/agents`,
  - report per-ref success/errors locally,
  - no `/api/capabilities/bulk` call.

## API, Data, and Contract Changes

### CLI flags and environment

Remove or retire:

- `--api legacy`
- `CAPELRY_USE_LEGACY_API`
- automatic fallback to legacy API

Options:

1. **Hard removal:** delete `--api` entirely because ARD is the only API.
2. **Soft removal:** leave `--api` hidden/accepted only for `ard`; if user passes `legacy`, exit with a clear message: `Legacy Capelry API was removed in v2.0.1; use ARD identifiers or slugs.`

Recommendation: hard removal in source plus a clear changelog/release note.

### Self catalog entry

Update `skills/capelry/ai-catalog.json` metadata:

```json
{
  "com.capelry.packageType": "skill",
  "com.capelry.slug": "capelry/capelry",
  "com.capelry.trustState": "source-hosted",
  "com.capelry.sourceRepository": "https://github.com/capelry-ai/capelry-skills",
  "com.capelry.sourcePath": "skills/capelry",
  "com.capelry.installTargets": "agents-project,pi-project,claude-project,codex-project"
}
```

Remove:

- `com.capelry.legacyRef`

### Tests and fixtures

Replace fixture metadata:

- `com.capelry.legacyRef` -> `com.capelry.slug`
- `metadata.com.capelry.legacyRef` filters -> `metadata.com.capelry.slug` filters
- JSON output key `legacyRef` -> `slug`
- Text output `legacy ref:` -> `slug:`

Remove fixture server dependency on `/api/capabilities` except possibly a negative test proving the CLI does not call it.

## Security, Privacy, and Permissions

- No new secrets are introduced.
- GitHub token behavior for source installs/self-update remains unchanged.
- Removing fallback to `/api/capabilities` reduces accidental use of deprecated endpoints and stale package metadata.
- ARD install checksum verification and safe archive extraction must remain intact.

## Performance and Reliability

- `info` and `install` remain single `/agents` lookups for exact identifier/slug filters.
- `discover` remains bounded by configured search limits.
- Removing fallback shortens failure paths and makes registry cutover failures explicit.
- If `bulk-info` is retained as ARD-native, keep a small default max and preserve per-ref errors to avoid one failed lookup hiding all results.

## Rollout, Rollback, and Observability

### Rollout sequence

1. Registry publishes v2.0.1 design and slug metadata contract.
2. Capelry Skills updates CLI/docs/tests/self-entry to ARD slug contract.
3. Release Capelry Skills v2.0.1 before or alongside registry ARD-only cutover.
4. Registry migration/backfill writes `com.capelry.slug` for package entries.
5. Smoke test against staging/production:
   - `search` uses `/search`,
   - `info capelry/capelry` uses `/agents` slug filter,
   - `install capelry/capelry` uses ARD source/zip entry,
   - no request hits `/api/capabilities`.

### Rollback

- If registry must temporarily keep old compatibility endpoints, v2.0.1 skills still works because it only uses ARD.
- If a slug metadata issue appears, fix registry ARD entries or Capelry Skills self-entry rather than reintroducing legacy fallback.

## Validation Strategy

Minimum gates for the Capelry Skills team:

- `python3 -m py_compile skills/capelry/scripts/capelry.py skills/capelry/scripts/bootstrap.py`
- Existing Python test suite after fixture updates.
- Add/modify tests:
  - `info namespace/name` filters on `metadata.com.capelry.slug`.
  - `install namespace/name` filters on `metadata.com.capelry.slug`.
  - ARD output includes `slug` and never `legacyRef`.
  - self `ai-catalog.json` contains `com.capelry.slug` and not `com.capelry.legacyRef`.
  - default commands do not call `/api/capabilities`.
  - passing `--api legacy` either fails clearly or is no longer accepted.
  - `bulk-info` is removed or uses only ARD `/agents`.
- Documentation grep gate:
  - `rg "legacyRef|legacy ref|/api/capabilities|--api legacy|CAPELRY_USE_LEGACY_API" skills/capelry README.md docs tests`
  - Expected final state: no active instructions or production code references. Historical design docs may mention these only as removed behavior.

## Dependencies and Story Seeds

| Seed | Repo/System | Depends On | Notes |
| --- | --- | --- | --- |
| Replace legacyRef with slug in CLI | capelry-skills | Registry slug contract | Constants, resolution, output, install naming. |
| Remove legacy API fallback | capelry-skills | Registry ARD-only direction | Delete old search/detail/install compatibility code. |
| Retire or rewrite bulk-info | capelry-skills | Product decision | Prefer removal; ARD-native rewrite acceptable. |
| Update self ARD catalog entry | capelry-skills | Slug metadata contract | `skills/capelry/ai-catalog.json`. |
| Update docs/bootstrap/SKILL copy | capelry-skills | CLI changes | Remove migration-window legacy language. |
| Update tests and fixture server | capelry-skills | CLI changes | Assert no `/api/capabilities` calls. |
| Cross-repo smoke against registry v2.0.1 | capelry-skills + capelry-registry | Both changes staged | Validate search/info/install with ARD-only registry. |

## Risks and Open Questions

- **Should `bulk-info` disappear or become ARD-native?** Recommendation: remove for v2.0.1 unless a current user workflow depends on it.
- **Will installed older clients fail after registry cutover?** They may fail legacy commands, but default ARD search/discover already works. Users can self-update from GitHub, which does not depend on the registry.
- **Do we keep `namespace/name` terminology?** Yes, as ARD `slug`, not legacy ref. Docs should say “slug” or “resource ref”.
- **Does every registry entry get `com.capelry.slug`?** Registry migration must guarantee this for Capelry package entries that should support human refs. Third-party generic ARD entries can remain identifier-only.

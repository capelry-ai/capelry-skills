# Capelry Agent Skills harness compatibility review

Reviewed: 2026-08-27

Candidate version: 2.1.0

## Scope

This review covered every shipped resource under `skills/capelry/` and its repository-facing metadata:

- `SKILL.md` agent instructions and frontmatter
- `BOOTSTRAP.md` fresh-project procedure
- `agents/openai.yaml` OpenAI presentation metadata
- `capability.yaml` compatibility/install manifest
- `ai-catalog.json` and mirrored `.well-known/ai-catalog.json`
- `scripts/bootstrap.py` standalone GitHub bootstrapper
- `scripts/capelry.py` registry, install, validation, and update CLI
- README, CI, and installer tests

The research matrix is maintained in `skills/capelry/references/harnesses.md`. It links the official documentation used for the Agent Skills standard, Claude Code, Codex, Pi, OpenCode, Gemini CLI, Cursor, GitHub Copilot/VS Code, Windsurf, Cline, Roo Code, JetBrains Junie, Kiro, Factory Droid, and OpenHands.

## Baseline findings

1. **Codex paths were misleading.** The CLI offered `.codex/skills` and `~/.codex/skills`, while current Codex documentation defines repository and user skills under `.agents/skills` and `~/.agents/skills`.
2. **The portable fallback was presented as universal.** Claude Code, Cline, and Kiro do not document `.agents/skills` discovery, and Windsurf's cross-agent guarantee is surface-specific. A successful copy could therefore produce a skill the active harness never loaded.
3. **Major native targets were absent.** OpenCode, Gemini CLI, Cursor, Windsurf, GitHub Copilot/VS Code, Cline, Roo Code, Junie, Kiro, and Factory had no deterministic CLI/bootstrap target.
4. **Automatic installs checked only for a file named `SKILL.md`.** Missing frontmatter, missing descriptions, invalid names, name/directory mismatches, and non-string YAML values could install successfully but remain undiscoverable.
5. **Replacement was destructive before validation.** Existing destinations could be removed before package validation completed.
6. **Archive traversal handling was incomplete.** Backslash-based traversal and Windows drive paths were not normalized before checks.
7. **Post-install instructions were Pi-centric.** Install, sync, and update output could tell users of another harness to run Pi commands.
8. **Published metadata drifted from implementation.** The catalog advertised only four project targets, the capability manifest listed fewer compatibility/install records, and UI metadata did not mention validation or harness selection.

## Change catalog and rationale

### Harness-aware targeting

- Added 28 explicit project/global targets covering portable Agent Skills plus 13 named harness families.
- Corrected both Codex aliases to the documented `.agents/skills` roots.
- Added `capelry.py targets` with JSON output, harness filtering, scope filtering, resolved roots, and a stable portable default.
- Added harness-specific activation instructions to successful install and sync output.
- Kept `.agents/skills` as the shared target only for products whose official docs advertise it.

**Why:** a filesystem copy is not a successful skill install unless the active harness scans that root and can disclose the skill.

### Portable package validation

- Added `capelry.py validate-skill <path>` and `validate` alias.
- Enforced UTF-8 `SKILL.md`, YAML delimiters, required string `name` and `description`, Agent Skills name syntax, 64/1024-character limits, optional compatibility length, metadata map shape, and exact parent-directory matching.
- Accepted folded/literal/multiline descriptions and quoted hashes while rejecting numeric, boolean, null, date-like, sequence, mapping, duplicate, malformed, and unquoted-colon required values.
- Marked harness-specific unknown frontmatter fields as valid but non-portable with an explicit warning.
- Applied the same required-core checks to fresh bootstrap, self-update, and local sync.

**Why:** all reviewed harnesses rely on the name/description disclosure contract, and most strict consumers require the directory name to match.

### Transactional installation and archive safety

- Download/extract into a hidden staging directory on the destination filesystem.
- Validate the staged package before moving the existing skill.
- Keep the catalog/explicit destination authoritative; a package cannot redirect installation by declaring a different name.
- Move the old install aside, move the validated candidate into place, and restore the old install on ordinary errors, `SystemExit`, or keyboard interruption.
- Preserve the old temporary path and report it if both replacement and rollback fail.
- Normalize `/` and `\` archive separators and reject traversal, absolute, NUL, and Windows drive paths.

**Why:** invalid or malicious packages must not remove or overwrite a working skill, and same-filesystem staging makes replacement a rename rather than a cross-device copy/delete.

### Agent and human instructions

- Reworked `SKILL.md`, `BOOTSTRAP.md`, and README to require active-harness identification before installation.
- Removed the claim that Claude Code can use the portable path automatically.
- Documented exact project/global paths and confirmation commands for each supported harness.
- Added explicit guidance for products without documented native Agent Skills loading: provide `SKILL.md` as instructions, but do not claim automatic discovery.
- Added a bundled evidence-backed harness reference with official source URLs and portability caveats.

**Why:** the Capelry skill itself must teach an agent how to complete an install for the harness executing it, not merely how to copy files.

### Manifests, catalog, and CI

- Bumped candidate metadata to 2.1.0.
- Expanded capability compatibility and project install records.
- Synchronized all 28 CLI targets into ARD catalog metadata and kept both catalog copies byte-identical.
- Updated OpenAI UI metadata to mention validation and harness selection.
- Added portable skill validation as an explicit CI step.
- Added drift tests tying CLI targets, bootstrap targets, docs, capability metadata, catalog metadata, and version constants together.

**Why:** registry consumers, bootstrap users, and direct CLI users must receive the same install contract.

## Verification evidence

- `python3 -m unittest discover -s tests` — **46 tests passed**.
- `python3 -m py_compile skills/capelry/scripts/capelry.py skills/capelry/scripts/bootstrap.py tests/test_capelry_scripts.py` — passed.
- `python3 skills/capelry/scripts/capelry.py validate-skill skills/capelry --json` — valid and portable.
- Official `skills-ref` 0.1.0 (`agentskills validate skills/capelry`) — `Valid skill`.
- PyYAML parse of `capability.yaml`, `agents/openai.yaml`, and `SKILL.md` frontmatter — passed.
- JSON parse and byte-for-byte catalog mirror comparison — passed.
- HTTP validation of all 19 official documentation URLs in the harness reference — passed (including expected redirects).
- Codex CLI 0.147.0 smoke test in an isolated temporary repository — disclosed the project skill at `.agents/skills/capelry/SKILL.md` with the expected description.
- Two independent read-only Codex reviews — four initial correctness findings fixed with regression tests; one later quoted-hash finding fixed. A later suggestion to restore `~/.codex/skills` was rejected because it conflicts with current official Codex documentation, which specifies `$HOME/.agents/skills`.
- `git diff --check` — passed.

Claude Code 2.1.246 was installed locally but not authenticated, so no model-backed Claude smoke call could run. Its path/frontmatter/reload behavior is instead backed by the current official Claude Code documentation and the official Agent Skills validator.

## Performance and operational assessment

The change does not affect application request latency or a runtime service. Added work occurs only during explicit discovery/install/validation commands. Validation is linear in `SKILL.md` size, and package extraction/download already dominates install time. Same-filesystem staging temporarily needs space for the old and new skill copies during replacement; failure leaves the prior install intact or reports the preserved recovery path.

## Compatibility and rollback

- Existing target names remain accepted.
- `codex-project` and `codex-global` intentionally change destination to Codex's current documented roots.
- Explicit `--name`/`--dest` aliases that do not match frontmatter now fail instead of creating a non-portable install.
- Invalid catalog skills that previously copied successfully now fail closed.
- Rollback is a normal Git revert of this candidate. Individual installation replacement also has in-process rollback, while `sync-install` retains its archive backup by default.

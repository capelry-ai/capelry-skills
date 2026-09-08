# Capelry maintenance and packaging

Read this file for Capelry self-update, local source sync, packaging another capability, or releasing this repository. It does not authorize publishing, commits, pushes, tags, or releases.

## Contents

- [Version and self-update](#version-and-self-update)
- [Sync unreleased local source](#sync-unreleased-local-source)
- [Package another capability](#package-another-capability)
- [Release this Capelry repository](#release-this-capelry-repository)

## Version and self-update

Check the installed skill from its installed directory:

```text
python3 <cli> version
python3 <cli> version --check
```

Updating writes to the filesystem and always requires user approval. Show a dry run first:

```text
python3 <cli> self-update --dry-run
python3 <cli> self-update --yes
python3 <cli> self-update --ref vX.Y.Z --yes
```

Self-update downloads `skills/capelry` from `capelry-ai/capelry-skills`, validates it, and replaces transactionally. Reload/confirm the skill afterward. If GitHub rate limits apply, the CLI reads `CAPELRY_GITHUB_TOKEN`, `GITHUB_TOKEN`, or `GH_TOKEN`.

Use Git, not self-update, inside a source checkout unless the user explicitly asks for `--allow-source-checkout`.

## Sync unreleased local source

When a maintainer asks to test unreleased local Capelry content in an installed target, use `sync-install` rather than manual copies:

```text
python3 skills/capelry/scripts/capelry.py sync-install --target pi-global --dry-run
python3 skills/capelry/scripts/capelry.py sync-install --target pi-global --yes
python3 skills/capelry/scripts/capelry.py sync-install --dest /absolute/path/to/skills/capelry --yes
```

Select the active harness target first. `sync-install` validates the candidate, replaces transactionally, and keeps a `.zip` archive backup by default. Do not create persistent backup directories inside skill roots; harnesses may load them as duplicate skills.

## Package another capability

Design the package around the capability's actual needs. For an Agent Skill, require `SKILL.md`; add only useful optional resources:

```text
capability.yaml       # Capelry package metadata when publishing to a catalog
SKILL.md              # required Agent Skills instructions
BOOTSTRAP.md          # optional fresh-project entry point
ai-catalog.json       # optional ARD/AI Catalog entry
agents/openai.yaml    # optional UI metadata
scripts/              # optional deterministic helpers
references/           # optional detail loaded on demand
assets/               # optional output resources
```

Use `SKILL.md` as `spec.docs.readme` unless a distinct human readme is necessary. Declare additional packaged files in the capability manifest. Use three-part `namespace/catalog/resource` slugs and collection member refs.

Before archiving:

1. Validate the skill with `python3 <cli> validate-skill path/to/skill`.
2. Test bundled scripts that the skill relies on.
3. Build from an explicit source allowlist or clean staging directory.
4. Exclude caches, bytecode, backups, temporary archives, tests, reports, credentials, and unrelated repository files.
5. Inspect archive paths and contents; preserve exact version/checksum evidence when reproducibility matters.

Some agent harnesses block or discourage particular executable extensions. Prefer portable, inspectable helpers and include only files required to run the capability. Capelry's bundled CLI does not publish a package; follow the registry's approved publication process and obtain authorization for external writes.

## Release this Capelry repository

Use this section only in a `capelry-ai/capelry-skills` source checkout.

Before release:

1. Set matching stable `X.Y.Z` versions in `capability.yaml`, both catalog entries, the CLI constant, and release examples.
2. Keep `skills/capelry/ai-catalog.json` and `.well-known/ai-catalog.json` byte-identical.
3. Compile, validate, test, and report metrics from the repository root:

```text
python3 -m py_compile skills/capelry/scripts/capelry.py skills/capelry/scripts/bootstrap.py skills/capelry/scripts/package_skill.py
python3 skills/capelry/scripts/capelry.py validate-skill skills/capelry
python3 -m unittest discover -s tests
python3 tests/skill_metrics.py
```

4. Build an allowlisted deterministic archive; it excludes `__pycache__`, `.pyc`, nested archives, and repository-only files:

```text
python3 skills/capelry/scripts/package_skill.py --output capelry-X.Y.Z.zip
python3 -m zipfile -t capelry-X.Y.Z.zip
python3 -m zipfile -l capelry-X.Y.Z.zip
```

5. Extract into a directory named `capelry`, rerun `validate-skill`, `--help`, and `targets --json` from the packaged copy.
6. Only after separate authorization, use a stable `vX.Y.Z` tag/release matching the manifest version. Smoke-test an installed copy with `self-update --ref vX.Y.Z --yes` and confirm harness visibility.

Do not publish automatically. Do not claim a release, remote CI result, or installed update without direct evidence.

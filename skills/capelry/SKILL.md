---
name: capelry
description: Integrate with the catalog-aware Capelry capability registry to search, explore facets, inspect, compare, install, bootstrap, package, publish, and self-update AI-agent skills and adjacent capabilities. Use when a user asks to find or install a skill from Capelry, add Capelry support to a fresh project, update the Capelry skill, publish a capability package, or work on the Capelry registry codebase.
license: MIT
metadata:
  registry: "https://capelry.com"
  bootstrap: "BOOTSTRAP.md"
---

# Capelry

Use this skill to work with the Capelry capability registry. Capelry stores versioned AI-agent capabilities such as skills, prompts, commands, agents, hooks, rules, workflows, extensions, and collections.

Default registry URL: `https://capelry.com`. Set `CAPELRY_REGISTRY_URL` for private, staging, or self-hosted registries.

Network requests send `User-Agent: capelry-client` by default so Capelry.com can attribute client usage. Set `CAPELRY_USER_AGENT_SUFFIX` to append an integration identifier (recommended) or `CAPELRY_USER_AGENT` to fully override it. Use product/deployment identifiers, not personal data.

## Python launcher

Use `python3` in Linux, macOS, and Pi environments. If unavailable, use the local Python 3 launcher such as `py` on Windows.

## Choose the active harness target before installing

Before every bootstrap, `install`, `install-catalog`, or `sync-install` operation:

1. Identify the coding harness and whether the user requested project or global scope.
2. Run `python3 <capelry-skill-dir>/scripts/capelry.py targets --harness <name>` when the target is not obvious.
3. Pass the matching `--target`; prefer project scope unless the user explicitly asks for global scope.
4. Follow the harness-specific `next` instruction printed after installation.

Do not assume one vendor's directory works in another harness. In particular, Claude Code uses `.claude/skills`, while Codex's documented project and user paths are `.agents/skills` (not `.codex/skills`). The portable `.agents/skills` target is natively discovered by Codex, Pi, OpenCode, Gemini CLI, Cursor, GitHub Copilot, Roo Code, Junie, Factory, and OpenHands. See [the verified harness matrix](references/harnesses.md) for native paths, reload behavior, and official sources.

## Capelry skill version and self-update

Check the installed skill version from the installed skill directory:

```text
python3 <capelry-skill-dir>/scripts/capelry.py version
python3 <capelry-skill-dir>/scripts/capelry.py version --check
```

Update only after user approval:

```text
python3 <capelry-skill-dir>/scripts/capelry.py self-update --dry-run
python3 <capelry-skill-dir>/scripts/capelry.py self-update --yes
python3 <capelry-skill-dir>/scripts/capelry.py self-update --ref vX.Y.Z --yes
```

Self-update downloads GitHub source path `skills/capelry` from `capelry-ai/capelry-skills`. Reload/restart the agent afterward. Use `git` rather than self-update inside a `capelry-skills` source checkout unless the user explicitly asks for `--allow-source-checkout`.

When maintaining Capelry from a source checkout and the user wants the installed agent skill to include unreleased local changes, use the local sync command instead of manual copy steps:

```text
python3 skills/capelry/scripts/capelry.py sync-install --target pi-global --dry-run
python3 skills/capelry/scripts/capelry.py sync-install --target pi-global --yes
python3 skills/capelry/scripts/capelry.py sync-install --dest /absolute/path/to/skills/capelry --yes
```

`sync-install` validates the local skill, replaces the destination, keeps a `.zip` archive backup by default, and then the agent must be reloaded. Do not create persistent backup directories inside agent skill roots because agent harnesses may load them as duplicate skills.

## Fast path: Search -> Info -> Compare -> Install

Prefer inspect-before-install. Do not install directly from a search result unless the user requested a specific trusted capability.

For Pi project-local installs:

```text
python3 .pi/skills/capelry/scripts/capelry.py search "pdf" --type skill --trust-state source-hosted
python3 .pi/skills/capelry/scripts/capelry.py info capelry-ai/capelry-skills/capelry --install-snippet pi-project
python3 .pi/skills/capelry/scripts/capelry.py install capelry-ai/capelry-skills/capelry --target pi-project
```

For portable Agent Skills project installs:

```text
python3 .agents/skills/capelry/scripts/capelry.py search "pdf" --type skill --trust-state source-hosted
python3 .agents/skills/capelry/scripts/capelry.py info capelry-ai/capelry-skills/capelry --install-snippet agents-project
python3 .agents/skills/capelry/scripts/capelry.py install capelry-ai/capelry-skills/capelry --target agents-project
```

If this skill is installed elsewhere, run the script from that installed path, e.g. `.claude/skills/capelry/scripts/capelry.py`.

## Catalog-aware ARD model

Capelry v2.0.6 and later expose ARD resources under a first-class catalog hierarchy:

```text
Namespace page: /c/{namespace}
Catalog page:   /c/{namespace}/{catalog}
Resource page:  /c/{namespace}/{catalog}/{resource}
ARD slug:       namespace/catalog/resource
Catalog path:   namespace/catalog
```

Use `metadata.com.capelry.slug = 'namespace/catalog/resource'` for exact resource resolution and `metadata.com.capelry.catalogPath = 'namespace/catalog'` for catalog-scoped discovery. Do not use old two-segment `namespace/name` refs for new examples.

## Discovery workflow

When a user says “find me skills for X”, produce a shortlist instead of dumping raw search output.

1. Generate 3-6 related queries from the user's phrase. Remove generic words like “skill” or “capability”.
2. Search with narrow supported ARD filters: usually `--type skill`, `--trust-state source-hosted`, `--catalog namespace/catalog`, `--source owner/repo`, or `--filter FIELD=VALUE`.
3. Inspect shortlisted entries with `info`; it resolves spec `urn:air:...` identifiers and `namespace/catalog/resource` slug refs through `GET /agents`.
4. Compare media type, ARD identifier, slug, catalog path, source repository, trust state, Trust Manifest/provenance, install data, and checksum when present.
5. Return a concise shortlist. Install only after confirmation unless the user requested a specific known capability.

Preferred discovery command (replace `agents-project` with the active harness target):

```text
python3 <capelry-skill-dir>/scripts/capelry.py discover "feature planning skills" --query "feature planning" --query feature --query prd --query "implementation plan" --top 5 --install-snippet agents-project
```

Manual batch flow:

```text
python3 <capelry-skill-dir>/scripts/capelry.py search "feature planning" --type skill --trust-state source-hosted --limit 10
python3 <capelry-skill-dir>/scripts/capelry.py search prd --expand --type skill --limit 10
python3 <capelry-skill-dir>/scripts/capelry.py info <namespace/catalog/resource> --install-snippet agents-project
```

Shortlist output format:

```text
1. urn:air:publisher.example:capability@version
   name: Display Name
   type: application/vnd.capelry.skill-source+json
   summary: ...
   source: https://github.com/org/repo
   catalog: namespace/catalog
   trust: source-hosted
   slug: namespace/catalog/resource
   page: https://capelry.com/c/namespace/catalog/resource
   install: python3 <capelry-skill-dir>/scripts/capelry.py install namespace/catalog/resource --target <active-target>
```

Machine-readable variant:

```text
python3 <capelry-skill-dir>/scripts/capelry.py discover "feature planning skills" --query "feature planning,feature,prd,implementation plan" --top 5 --install-snippet agents-project --json
```

If exact search fails, try related searches such as:

- feature planning: `feature planning`, `feature`, `prd`, `product requirements document`, `implementation plan`, `specification`, `roadmap`
- production readiness: `production`, `readiness`, `preflight`, `rollout`, `release plan`, `deployment`
- operational terms: `SRE`, `observability`, `monitoring`, `incident response`
- safety terms: `hardening`, `hardening docker`, `container image hardening`, `RBAC hardening`
- resilience terms: `backup`, `recovery`, `backup integrity`

## Explore facets

Use `explore` to discover catalog/source/type/trust buckets before narrowing searches:

```text
python3 <capelry-skill-dir>/scripts/capelry.py explore "production readiness" --field metadata.com.capelry.catalogPath --field type --limit 10
python3 <capelry-skill-dir>/scripts/capelry.py explore --catalog capelry-ai/capelry-skills --json
```

Direct ARD endpoint: `POST {CAPELRY_REGISTRY_URL}/explore` with `{"query":{"text":"query"},"resultType":{"facets":[{"field":"metadata.com.capelry.catalogPath","limit":10}]}}`.

## Search

```text
python3 <capelry-skill-dir>/scripts/capelry.py search "query" --type skill --trust-state source-hosted
```

Useful supported flags:

- `--expand`: search related terms.
- `--json`: emit machine-readable output.
- `--type skill`: map package type to supported ARD skill media types.
- `--media-type application/vnd.capelry.skill-source+json`: exact ARD media type filter; repeat or comma-separate.
- `--publisher github.com`: ARD publisher filter.
- `--trust-state source-hosted`: filter by `metadata.com.capelry.trustState`.
- `--source owner/repo` or `--source https://github.com/owner/repo`: filter by GitHub `metadata.com.capelry.sourceRepositoryFullName` or exact source URL.
- `--catalog namespace/catalog`: filter by `metadata.com.capelry.catalogPath`.
- `--catalog-slug repo`: filter by `metadata.com.capelry.catalogSlug`.
- `--catalog-url URL`: filter by `metadata.com.capelry.catalogUrl`.
- `--slug namespace/catalog/resource`: exact slug filter.
- `--filter FIELD=VALUE`: generic ARD filter. Supported public fields include `identifier`, `type`, `publisher`, `tags`, `capabilities`, `version`, `updatedAt`, `trustManifest.identityType`, `trustManifest.attestations.type`, and `metadata.com.capelry.packageType`, `trustState`, `slug`, `catalogPath`, `catalogSlug`, `catalogUrl`, `sourceRepository`, `sourceRepositoryFullName`.

Compatibility flags `--status`, `--domain`, and `--phase` are accepted but not sent because current public ARD routes do not expose those filters.

Direct ARD endpoint:

```text
POST {CAPELRY_REGISTRY_URL}/search
{"query":{"text":"query","filter":{"type":["application/vnd.capelry.skill-source+json"],"metadata.com.capelry.catalogPath":["namespace/catalog"]}},"federation":"none","pageSize":10}
```

## Inspect

```text
python3 <capelry-skill-dir>/scripts/capelry.py info namespace/catalog/resource --install-snippet agents-project
python3 <capelry-skill-dir>/scripts/capelry.py info urn:air:github.com:org:repo:skill --json
```

Default ARD resolution uses `GET {CAPELRY_REGISTRY_URL}/agents?filter=identifier = '...'` for URNs and `metadata.com.capelry.slug = 'namespace/catalog/resource'` for slug refs.

For multiple entries, use `bulk-info` for up to 25 refs or use `discover` when you need ranked shortlist output.

## Compare before installing

Inspect at least one candidate, usually two or three, before installing third-party skills. Compare:

- media type and package type
- catalog path, source repository, source path, and public `/c/...` page
- summary and detailed description
- trust state, Trust Manifest provenance, checksum, and install descriptor
- whether the capability matches this project stack

## Install

Install one resource after selecting the active harness target:

```text
python3 <capelry-skill-dir>/scripts/capelry.py install namespace/catalog/resource --target agents-project
python3 <capelry-skill-dir>/scripts/capelry.py install urn:air:github.com:org:repo:skill --target agents-project
```

Install all supported skill resources from a catalog, with a dry run first:

```text
python3 <capelry-skill-dir>/scripts/capelry.py install-catalog y30k/ai-capabilities --target agents-project --dry-run
python3 <capelry-skill-dir>/scripts/capelry.py install-catalog y30k/ai-capabilities --target agents-project --force --yes
```

Replace `agents-project` with `claude-project`, `pi-project`, or the matching target when the active harness needs a native root.

The installer resolves ARD entries by URN or `namespace/catalog/resource` slug metadata, prints trust/provenance, stages each package outside the destination, validates its Agent Skills metadata, and only then replaces the destination. Existing installs remain intact when download, extraction, checksum, or validation fails.

Supported media types:

- `application/vnd.capelry.skill+zip`: downloads the archive, verifies SHA-256 when present, and rejects unsafe archive paths.
- `application/vnd.capelry.skill-source+json`: installs from a pinned source archive or supported GitHub source descriptor.

Every installed skill must have UTF-8 `SKILL.md` frontmatter with a valid `name`, a non-empty `description`, and a parent directory matching `name`. Invalid packages fail closed. Harness-specific extra fields are warned as non-portable but may still install. Unsupported media types are not auto-installed; the CLI prints open/connect guidance.

Validate a local package without installing it:

```text
python3 <capelry-skill-dir>/scripts/capelry.py validate-skill path/to/skill
python3 <capelry-skill-dir>/scripts/capelry.py validate-skill path/to/skill --json
```

## Install target preference

Default to project-local scope. Use the active harness's native target when the user wants one harness; use `agents-project` for a shared repository only when every intended harness documents `.agents/skills` discovery.

| Harness | Project target | Global target |
| --- | --- | --- |
| Portable / Codex | `agents-project` or `codex-project` | `agents-global` or `codex-global` |
| Claude Code | `claude-project` | `claude-global` |
| Pi | `pi-project` | `pi-global` |
| OpenCode | `opencode-project` | `opencode-global` |
| Gemini CLI | `gemini-project` | `gemini-global` |
| Cursor | `cursor-project` | `cursor-global` |
| Windsurf | `windsurf-project` | `windsurf-global` |
| GitHub Copilot / VS Code | `copilot-project` | `copilot-global` |
| Cline / Roo Code | `cline-project` / `roo-project` | `cline-global` / `roo-global` |
| Junie / Kiro / Factory | `junie-project` / `kiro-project` / `factory-project` | matching `-global` target |

Run `targets --json` for exact resolved roots. The complete verified matrix and reload commands are in [references/harnesses.md](references/harnesses.md).

## Bootstrap a fresh project

When the user asks to add Capelry to a fresh repository, read and follow `BOOTSTRAP.md`. Bootstrapping installs this skill from GitHub source at `https://github.com/capelry-ai/capelry-skills`, not from Capelry.com. Identify the active harness and pass its documented project target; use `agents-project` only when that harness documents `.agents/skills`. If this package is already checked out or extracted, run `python3 scripts/bootstrap.py --target <target>`.

## Publish or package a capability

For a publishable skill package, keep files minimal:

```text
capability.yaml
SKILL.md
BOOTSTRAP.md        # optional, useful for installer/meta skills like this one
ai-catalog.json     # ARD/AI Catalog self-entry when publishing this skill
agents/openai.yaml # optional UI metadata
scripts/*.py       # optional deterministic helpers; avoid blocked extensions like .sh
references/*       # optional docs loaded on demand
assets/*           # optional output assets
```

Use `SKILL.md` as `spec.docs.readme` when you do not need a human README. Add `BOOTSTRAP.md` as `spec.docs.additional` when the skill should teach fresh-project installation. Keep portable frontmatter to the Agent Skills fields `name`, `description`, `license`, `compatibility`, `metadata`, and `allowed-tools`; `name` must match the package directory and `description` must explain what the skill does and when to use it. Run `validate-skill` before packaging.

Create a zip from inside the skill directory:

```text
python3 -m zipfile -c capelry-2.1.0.zip capability.yaml SKILL.md BOOTSTRAP.md ai-catalog.json agents scripts references
# Add assets/ only if that directory exists.
```

Collection member refs and ARD slugs should use `namespace/catalog/resource`, not old `namespace/name` refs. When this repository is served as a catalog source, keep the repository-level `.well-known/ai-catalog.json` aligned with the packaged `skills/capelry/ai-catalog.json` self-entry.

## Safety rules

- Treat skills as executable instructions. Inspect third-party `SKILL.md` and bundled scripts before running them.
- Prefer the workflow: search -> info -> compare -> install.
- Identify the active harness and pass its exact target; never claim an install is loaded until the harness's list/reload check confirms it.
- Prefer project-local installs for experiments.
- Do not run bundled scripts from newly installed skills unless the user asks or the skill documentation clearly requires it.
- Preserve exact version and checksum details when the user needs reproducibility.
- Do not self-update Capelry in the background; update only when the user asks or approves it.

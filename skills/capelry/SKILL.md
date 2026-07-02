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

## Python launcher

Use `python3` in Linux, macOS, and Pi environments. If unavailable, use the local Python 3 launcher such as `py` on Windows.

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
3. Inspect shortlisted entries with `info`; it resolves both `urn:ai:...` identifiers and `namespace/catalog/resource` slug refs through `GET /agents`.
4. Compare media type, ARD identifier, slug, catalog path, source repository, trust state, Trust Manifest/provenance, install data, and checksum when present.
5. Return a concise shortlist. Install only after confirmation unless the user requested a specific known capability.

Preferred discovery command:

```text
python3 .pi/skills/capelry/scripts/capelry.py discover "feature planning skills" --query "feature planning" --query feature --query prd --query "implementation plan" --top 5 --install-snippet pi-project
```

Manual batch flow:

```text
python3 .pi/skills/capelry/scripts/capelry.py search "feature planning" --type skill --trust-state source-hosted --limit 10
python3 .pi/skills/capelry/scripts/capelry.py search prd --expand --type skill --limit 10
python3 .pi/skills/capelry/scripts/capelry.py info <namespace/catalog/resource> --install-snippet pi-project
```

Shortlist output format:

```text
1. urn:ai:publisher.example:capability@version
   name: Display Name
   type: application/vnd.capelry.skill-source+json
   summary: ...
   source: https://github.com/org/repo
   catalog: namespace/catalog
   trust: source-hosted
   slug: namespace/catalog/resource
   page: https://capelry.com/c/namespace/catalog/resource
   install: python3 .pi/skills/capelry/scripts/capelry.py install namespace/catalog/resource --target pi-project
```

Machine-readable variant:

```text
python3 .pi/skills/capelry/scripts/capelry.py discover "feature planning skills" --query "feature planning,feature,prd,implementation plan" --top 5 --install-snippet pi-project --json
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
python3 <capelry-skill-dir>/scripts/capelry.py info namespace/catalog/resource --install-snippet pi-project
python3 <capelry-skill-dir>/scripts/capelry.py info urn:ai:github.com:org:repo:skill --json
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

```text
python3 <capelry-skill-dir>/scripts/capelry.py install namespace/catalog/resource --target pi-project
python3 <capelry-skill-dir>/scripts/capelry.py install urn:ai:github.com:org:repo:skill --target pi-project
```

Use `--target agents-project`, `--target claude-project`, or another target if Pi is not active.

The installer resolves ARD entries by URN or `namespace/catalog/resource` slug metadata, prints trust/provenance before installing, and supports:

- `application/vnd.capelry.skill+zip`: downloads archive URL, verifies SHA-256 when present, and extracts only safe paths containing `SKILL.md`.
- `application/vnd.capelry.skill-source+json`: installs from a source descriptor/ref using a declared source archive or GitHub source path.

Unsupported media types are not auto-installed; the CLI prints open/connect guidance.

## Install target preference

Default to project-local installs unless the user asks for global installation.

1. Pi project: `.pi/skills/<skill-name>`
2. Portable project default: `.agents/skills/<skill-name>`
3. Claude Code project: `.claude/skills/<skill-name>`
4. Codex project/global: `.codex/skills/<skill-name>` or `~/.codex/skills/<skill-name>`
5. Universal global fallback: `~/.agents/skills/<skill-name>`

After installing, tell the user to reload/restart their agent. For Pi, use `/reload` and then `/skill:<name>`.

## Bootstrap a fresh project

When the user asks to add Capelry to a fresh repository, read and follow `BOOTSTRAP.md`. Bootstrapping installs this skill from GitHub source at `https://github.com/capelry-ai/capelry-skills`, not from Capelry.com. Choose the project-local target for the active coding agent; if unsure, use `.agents/skills/capelry`. If this package is already checked out or extracted, run `python3 scripts/bootstrap.py`.

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

Use `SKILL.md` as `spec.docs.readme` when you do not need a human README. Add `BOOTSTRAP.md` as `spec.docs.additional` when the skill should teach fresh-project installation.

Create a zip from inside the skill directory:

```text
python3 -m zipfile -c capelry-2.0.8.zip capability.yaml SKILL.md BOOTSTRAP.md ai-catalog.json agents scripts
# Add references/ or assets/ only if those directories exist.
```

Collection member refs and ARD slugs should use `namespace/catalog/resource`, not old `namespace/name` refs.

## Safety rules

- Treat skills as executable instructions. Inspect third-party `SKILL.md` and bundled scripts before running them.
- Prefer the workflow: search -> info -> compare -> install.
- Prefer project-local installs for experiments.
- Do not run bundled scripts from newly installed skills unless the user asks or the skill documentation clearly requires it.
- Preserve exact version and checksum details when the user needs reproducibility.
- Do not self-update Capelry in the background; update only when the user asks or approves it.

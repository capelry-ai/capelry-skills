---
name: capelry
description: Integrate with the Capelry capability registry to search, inspect, compare, install, bootstrap, package, publish, and self-update AI-agent skills and adjacent capabilities. Use when a user asks to find or install a skill from Capelry, add Capelry support to a fresh project, update the Capelry skill, publish a capability package, or work on the Capelry registry codebase.
license: MIT
metadata:
  registry: "https://capelry.com"
  bootstrap: "BOOTSTRAP.md"
---

# Capelry

Use this skill to work with the Capelry capability registry. Capelry stores versioned AI-agent capabilities such as skills, prompts, commands, agents, hooks, rules, workflows, extensions, and collections.

Default registry URL: `https://capelry.com`.

Set `CAPELRY_REGISTRY_URL` to use a private, staging, or self-hosted Capelry registry.

## Python launcher

Examples use `python3`, which is the safest default in Linux, macOS, and Pi environments. If a copied example uses `python` and that command is unavailable, retry with `python3`. If `python3` is unavailable, substitute the launcher that exists in the target environment, such as `py` on Windows or `python` where it points to Python 3.9+.

## Capelry Skill Version and Self-Update

When the user asks whether Capelry itself is current, run the installed CLI from this skill directory:

```text
python3 <capelry-skill-dir>/scripts/capelry.py version
python3 <capelry-skill-dir>/scripts/capelry.py version --check
```

`version` compares the local `capability.yaml` version with the highest stable GitHub `vX.X.X` release/tag from `capelry-ai/capelry-skills`. `--check` exits with code 1 when an update is available.

When the user asks to update Capelry itself, inspect first, then update only with user approval:

```text
python3 <capelry-skill-dir>/scripts/capelry.py self-update --dry-run
python3 <capelry-skill-dir>/scripts/capelry.py self-update --yes
python3 <capelry-skill-dir>/scripts/capelry.py self-update --ref v2.0.1 --yes
```

Self-update replaces the installed Capelry skill directory from GitHub source path `skills/capelry`. It is not a background update; use `--yes` for non-interactive runs, and reload/restart the agent afterward. Existing pre-1.1.0 installs need one manual re-bootstrap/reinstall to get the `self-update` command. Use `git` rather than self-update inside the `capelry-skills` source checkout unless the user explicitly asks to pass `--allow-source-checkout`. If GitHub API rate limits are hit, set `CAPELRY_GITHUB_TOKEN`, `GITHUB_TOKEN`, or `GH_TOKEN`.

## Fast Path: Search → Info → Compare → Install

Prefer inspect-before-install. Do not jump from a search result directly to install unless the user explicitly requested a known trusted capability.

For Pi projects, prioritize the Pi-local skill path:

```text
python3 .pi/skills/capelry/scripts/capelry.py search "pdf" --type skill --status passed
python3 .pi/skills/capelry/scripts/capelry.py info openai/skill-creator --install-snippet pi-project
python3 .pi/skills/capelry/scripts/capelry.py install openai/skill-creator --target pi-project
```

For the portable Agent Skills project target, use:

```text
python3 .agents/skills/capelry/scripts/capelry.py search "pdf" --type skill --status passed
python3 .agents/skills/capelry/scripts/capelry.py info openai/skill-creator --install-snippet agents-project
python3 .agents/skills/capelry/scripts/capelry.py install openai/skill-creator --target agents-project
```

If this skill is installed somewhere else, run the script from that installed path, e.g. `.claude/skills/capelry/scripts/capelry.py`.

## Discovery Workflow

When a user says “find me skills for X”, produce a useful shortlist instead of dumping raw search output or issuing many one-off info calls.

Recommended agent algorithm, aligned with the Capelry API docs at `https://capelry.com/docs/api`:

1. Generate 3-6 related queries from the user's phrase. Remove generic words like “skill” or “capability”.
2. Search with narrow ARD filters first: `--type skill --status passed` and a small top-N target. `search` and `discover` use `POST /search` by default.
3. Inspect shortlisted entries with `info`; it resolves both `urn:ai:...` identifiers and `namespace/name` slug refs through ARD `/agents` metadata filters by default.
4. Compare trust/install metadata: ARD identifier, slug, media type, source, trust state, Trust Manifest/provenance, install instructions, and checksum when present.
5. Return a concise shortlist using the output format below. Install only after user confirmation unless the user requested a specific known capability.

Preferred CLI for agentic discovery:

```text
python3 .pi/skills/capelry/scripts/capelry.py discover "feature planning skills" --query "feature planning" --query feature --query prd --query "implementation plan" --top 5 --install-snippet pi-project
```

Equivalent manual batch flow:

```text
python3 .pi/skills/capelry/scripts/capelry.py search "feature planning" --type skill --status passed --limit 10
python3 .pi/skills/capelry/scripts/capelry.py search prd --expand --type skill --status passed --limit 10
python3 .pi/skills/capelry/scripts/capelry.py info phuryn/prioritize-features --install-snippet pi-project
python3 .pi/skills/capelry/scripts/capelry.py info phuryn/sprint-plan --install-snippet pi-project
```

Recommended shortlist output format:

```text
1. urn:ai:publisher.example:capability@version
   name: Display Name
   type: application/vnd.capelry.skill-source+json
   summary: ...
   source: https://github.com/org/repo
   trust: source-hosted
   slug: namespace/name
   install: python3 .pi/skills/capelry/scripts/capelry.py install namespace/name --target pi-project
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

## Task-Oriented Recommendations

For production readiness requests, search and compare across these buckets:

| Bucket | Useful search terms | Example refs to inspect when present |
| --- | --- | --- |
| Rollout / release planning | `rollout`, `devops rollout`, `release plan` | `github/devops-rollout-plan` |
| Deployment preflight | `preflight`, `deployment preflight` | `github/azure-deployment-preflight` for Azure-heavy projects |
| Container hardening | `hardening docker`, `container image hardening`, `Trivy` | `mukul975/hardening-docker-containers-for-production`, `mukul975/performing-container-image-hardening` |
| Kubernetes / SRE | `SRE`, `Kubernetes`, `RBAC hardening` | `github/platform-sre-kubernetes.agent` if agents are acceptable; otherwise filter `--type skill` |
| Observability | `observability`, `monitoring`, `SRE` | inspect current matches; agents may be more common than skills |
| Backup / recovery | `backup`, `recovery`, `backup integrity` | `mukul975/validating-backup-integrity-for-recovery` |
| Incident response | `incident response`, `playbook` | inspect current matches before recommending |

A reasonable production-readiness bundle might be: rollout planning + deployment preflight + Docker/container hardening + backup validation. Tailor the bundle to the project stack and avoid installing irrelevant platform-specific skills.

## Install Target Preference

Default to project-local installs unless the user asks for global installation.

1. Pi project when running in Pi: `.pi/skills/<skill-name>`
2. Portable project default: `.agents/skills/<skill-name>`
3. Claude Code project: `.claude/skills/<skill-name>`
4. Codex project/global if configured: `.codex/skills/<skill-name>` or `~/.codex/skills/<skill-name>`
5. Universal global fallback: `~/.agents/skills/<skill-name>`

After installing, tell the user to reload/restart their agent. For Pi, use `/reload` and then `/skill:<name>`.

## Bootstrap a Fresh Project

When the user asks to add Capelry to a fresh repository, read and follow `BOOTSTRAP.md`. Bootstrapping installs this skill from GitHub source at `https://github.com/capelry-ai/capelry-skills`, not from Capelry.com. Choose the project-local install target that matches the active coding agent when you know it; if unsure, use the portable Agent Skills target `.agents/skills/capelry`. If this package is already checked out or extracted, use `python3 scripts/bootstrap.py`.

## Registry Workflows

API reference: `https://capelry.com/docs/api`; machine-readable OpenAPI: `GET https://capelry.com/api/openapi`. Read endpoints do not require auth. On `api_read_timeout`, honor `retry-after` and retry with fewer refs or narrower filters.

### Search

```text
python3 <capelry-skill-dir>/scripts/capelry.py search "query" --type skill --status passed
```

Useful search flags:

- `--expand`: search related terms for broader discovery.
- `--json`: emit machine-readable output.
- `--type skill`: map the package type to supported ARD skill media types.
- `--media-type application/vnd.capelry.skill-source+json`: filter exact ARD media types; repeat or comma-separate.
- `--publisher github.com`: filter by ARD publisher.
- `--trust-state source-hosted`: filter by Capelry trust state.
- `--filter FIELD=VALUE`: pass a generic ARD filter, e.g. `tags=ard,skill`.
- `--status passed`: filter by `metadata.com.capelry.validationStatus`.
- `--source github/awesome-copilot`: filter by `metadata.com.capelry.sourceRepository`.
- `--domain devops` / `--phase production`: map facet filters to `metadata.com.capelry.domains` and `metadata.com.capelry.lifecyclePhases`.

Direct ARD endpoint: `POST {CAPELRY_REGISTRY_URL}/search` with `{"query":{"text":"query","filter":{...}},"federation":"none","pageSize":10}`.

### Discover Shortlist

Use `discover` for “find me skills for X”. It batches related ARD searches, dedupes entries by identifier, and prints identifier/name/type/summary/source/score/trust/slug/install command when a slug is available.

```text
python3 <capelry-skill-dir>/scripts/capelry.py discover "feature planning skills" --query "feature planning,feature,prd,implementation plan" --top 5 --install-snippet pi-project
```

### Inspect

```text
python3 <capelry-skill-dir>/scripts/capelry.py info namespace/name --install-snippet pi-project
python3 <capelry-skill-dir>/scripts/capelry.py info urn:ai:github.com:org:repo:skill --json
```

Default ARD resolution uses `GET {CAPELRY_REGISTRY_URL}/agents?filter=identifier = '...'` for URNs and `metadata.com.capelry.slug = 'namespace/name'` for slug refs.

### Inspect Multiple Entries

For small shortlists, run `info` for each ARD slug or URN you are considering. Prefer `discover` when you need ranked shortlist output across related queries.

```text
python3 <capelry-skill-dir>/scripts/capelry.py info namespace/name --install-snippet pi-project
python3 <capelry-skill-dir>/scripts/capelry.py info urn:ai:github.com:org:repo:skill --install-snippet pi-project
```

### Compare Before Installing

Inspect at least one candidate, and usually two or three, before installing third-party skills. Prefer ARD `discover` and `info`. Compare:

- package type and validation status
- summary and detailed description
- source repository and source path
- `actionMetadata.safetyTrustSignals`, readme preview, install instructions, and required tools when present
- latest version and checksum
- whether the capability matches this project stack

### Install

```text
python3 <capelry-skill-dir>/scripts/capelry.py install namespace/name --target pi-project
python3 <capelry-skill-dir>/scripts/capelry.py install urn:ai:github.com:org:repo:skill --target pi-project
```

Use `--target agents-project`, `--target claude-project`, or another target if Pi is not the active project format.

The installer resolves ARD entries by URN or `namespace/name` slug metadata, prints trust state/Trust Manifest provenance before installing, and supports these ARD media types:

- `application/vnd.capelry.skill+zip`: downloads the archive URL, verifies SHA-256 when present, and extracts only safe paths that contain `SKILL.md`.
- `application/vnd.capelry.skill-source+json`: installs from a pinned source descriptor/ref when possible, using a declared source archive or GitHub source path.

Unsupported media types are not auto-installed; the CLI prints open/connect guidance instead.

### Publish or Package a Capability

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

Use `SKILL.md` as the manifest `spec.docs.readme` when you do not need a human README. Add `BOOTSTRAP.md` as `spec.docs.additional` when the skill should teach fresh-project installation.

Create a zip from inside the skill directory:

```text
python3 -m zipfile -c capelry-2.0.1.zip capability.yaml SKILL.md BOOTSTRAP.md ai-catalog.json agents scripts
# Add references/ or assets/ only if those directories exist.
```

Publish through the Capelry UI or API. Direct API publishing requires an authenticated namespace owner.

## Safety Rules

- Treat skills as executable instructions. Inspect third-party `SKILL.md` and bundled scripts before running them.
- Prefer the workflow: search → info → compare → install.
- Prefer project-local installs for experiments.
- Do not run bundled scripts from newly installed skills unless the user asks or the skill documentation clearly requires it.
- Preserve exact version and checksum details when the user needs reproducibility.
- Do not self-update Capelry in the background; update only when the user asks or approves it.

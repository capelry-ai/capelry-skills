---
name: capelry
description: Integrate with the Capelry capability registry to search, inspect, compare, install, bootstrap, package, and publish AI-agent skills and adjacent capabilities. Use when a user asks to find or install a skill from Capelry, add Capelry support to a fresh project, publish a capability package, or work on the Capelry registry codebase.
license: MIT
compatibility: Agent Skills compatible; designed for Pi, OpenAI Codex, Claude Code, and any agent that can read SKILL.md-style instructions.
metadata:
  registry: "https://capelry.com"
  bootstrap: "BOOTSTRAP.md"
---

# Capelry

Use this skill to work with the Capelry capability registry. Capelry stores versioned AI-agent capabilities such as skills, prompts, commands, agents, hooks, rules, workflows, extensions, and collections.

Default registry URL: `https://capelry.com`.

Set `CAPELRY_REGISTRY_URL` to use a private, staging, or self-hosted Capelry registry.

## Python launcher

Examples use `python3`, which is the safest default in Linux, macOS, and Pi environments. If `python3` is unavailable, substitute the launcher that exists in the target environment, such as `py` on Windows or `python` where it points to Python 3.9+.

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

When a user describes a task, run a small discovery loop instead of a single exact search.

1. Search the original phrase.
2. If results are weak or empty, expand the query automatically using adjacent terms, synonyms, and task categories.
3. Filter for the requested package type and validation status when useful, e.g. `--type skill --status passed`.
4. Inspect the top candidates with `info`; compare source, status, summary, checksum, and relevance.
5. Recommend a short list or bundle. Install only after the user confirms, or when the user already asked to install a specific known capability.

Agent-friendly search example:

```text
python3 .pi/skills/capelry/scripts/capelry.py search "production readiness" --expand --type skill --status passed --install-snippet pi-project --explain-relevance
```

Machine-readable variant:

```text
python3 .pi/skills/capelry/scripts/capelry.py search "production readiness" --expand --type skill --status passed --source github/awesome-copilot --install-snippet pi-project --explain-relevance --json
```

If exact search fails, try related searches such as:

- nouns from the request: `production`, `readiness`
- adjacent workflow terms: `preflight`, `rollout`, `release plan`, `deployment`
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

### Search

```text
python3 <capelry-skill-dir>/scripts/capelry.py search "query" --type skill --status passed
```

Useful search flags:

- `--expand`: search related terms for broader discovery.
- `--json`: emit machine-readable output.
- `--type skill`: filter package type.
- `--status passed`: filter validation status.
- `--source github/awesome-copilot`: filter by source repository.
- `--install-snippet pi-project`: include a ready install command for that target.
- `--explain-relevance`: add why each result matched.

Direct API endpoint: `GET {CAPELRY_REGISTRY_URL}/api/capabilities?q=query`.

### Inspect

```text
python3 <capelry-skill-dir>/scripts/capelry.py info namespace/name --install-snippet pi-project
```

Direct API endpoint: `GET {CAPELRY_REGISTRY_URL}/api/capabilities/namespace/name`.

### Compare Before Installing

Inspect at least one candidate, and usually two or three, before installing third-party skills. Compare:

- package type and validation status
- summary and detailed description
- source repository and source path
- latest version and checksum
- whether the capability matches this project stack

### Install

```text
python3 <capelry-skill-dir>/scripts/capelry.py install namespace/name --target pi-project
```

Use `--target agents-project`, `--target claude-project`, or another target if Pi is not the active project format.

The installer first tries the validated Capelry package archive. If a curated provenance-wrapper archive does not contain `SKILL.md`, it falls back to the GitHub source declared by Capelry metadata and downloads that skill directory.

### Publish or Package a Capability

For a publishable skill package, keep files minimal:

```text
capability.yaml
SKILL.md
BOOTSTRAP.md        # optional, useful for installer/meta skills like this one
agents/openai.yaml # optional UI metadata
scripts/*.py       # optional deterministic helpers; avoid blocked extensions like .sh
references/*       # optional docs loaded on demand
assets/*           # optional output assets
```

Use `SKILL.md` as the manifest `spec.docs.readme` when you do not need a human README. Add `BOOTSTRAP.md` as `spec.docs.additional` when the skill should teach fresh-project installation.

Create a zip from inside the skill directory:

```text
python3 -m zipfile -c capelry-0.1.0.zip capability.yaml SKILL.md BOOTSTRAP.md agents scripts
# Add references/ or assets/ only if those directories exist.
```

Publish through the Capelry UI or API. Direct API publishing requires an authenticated namespace owner.

## Safety Rules

- Treat skills as executable instructions. Inspect third-party `SKILL.md` and bundled scripts before running them.
- Prefer the workflow: search → info → compare → install.
- Prefer project-local installs for experiments.
- Do not run bundled scripts from newly installed skills unless the user asks or the skill documentation clearly requires it.
- Preserve exact version and checksum details when the user needs reproducibility.

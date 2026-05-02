---
name: capelry
description: Integrate with the Capelry capability registry to search, inspect, install, bootstrap, package, and publish AI-agent skills and adjacent capabilities. Use when a user asks to find or install a skill from Capelry, add Capelry support to a fresh project, publish a capability package, or work on the Capelry registry codebase.
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

## Fast Path

Use the bundled stdlib-only Python CLI when possible:

```text
python .agents/skills/capelry/scripts/capelry.py search "pdf"
python .agents/skills/capelry/scripts/capelry.py info openai/skill-creator
python .agents/skills/capelry/scripts/capelry.py install openai/skill-creator --target agents-project
```

If this skill is installed somewhere else, run the script from that installed path, e.g. `.pi/skills/capelry/scripts/capelry.py` or `.claude/skills/capelry/scripts/capelry.py`.

## Install Target Preference

Default to project-local installs unless the user asks for global installation.

1. Portable project default: `.agents/skills/<skill-name>`
2. Pi project: `.pi/skills/<skill-name>`
3. Claude Code project: `.claude/skills/<skill-name>`
4. Codex project/global if configured: `.codex/skills/<skill-name>` or `~/.codex/skills/<skill-name>`
5. Universal global fallback: `~/.agents/skills/<skill-name>`

After installing, tell the user to reload/restart their agent. For Pi, use `/reload` and then `/skill:<name>`.

## Bootstrap a Fresh Project

When the user asks to add Capelry to a fresh repository, read and follow `BOOTSTRAP.md`. Bootstrapping installs this skill from GitHub source at `https://github.com/capelry-ai/capelry-skills`, not from Capelry.com. Choose the project-local install target that matches the active coding agent when you know it; if unsure, use the portable Agent Skills target `.agents/skills/capelry`. If this package is already checked out or extracted, use `python scripts/bootstrap.py`.

## Registry Workflows

### Search

```text
python <capelry-skill-dir>/scripts/capelry.py search "query"
```

Direct API endpoint: `GET {CAPELRY_REGISTRY_URL}/api/capabilities?q=query`.

### Inspect

```text
python <capelry-skill-dir>/scripts/capelry.py info namespace/name
```

Direct API endpoint: `GET {CAPELRY_REGISTRY_URL}/api/capabilities/namespace/name`.

### Install

```text
python <capelry-skill-dir>/scripts/capelry.py install namespace/name --target agents-project
```

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
python -m zipfile -c capelry-0.1.0.zip capability.yaml SKILL.md BOOTSTRAP.md agents scripts
# Add references/ or assets/ only if those directories exist.
```

Publish through the Capelry UI or API. Direct API publishing requires an authenticated namespace owner.

## Safety Rules

- Treat skills as executable instructions. Inspect third-party `SKILL.md` and bundled scripts before running them.
- Prefer project-local installs for experiments.
- Do not run bundled scripts from newly installed skills unless the user asks or the skill documentation clearly requires it.
- Preserve exact version and checksum details when the user needs reproducibility.

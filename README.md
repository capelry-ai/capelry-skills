<div align="center">
  <a href="https://capelry.com">
    <img src="./capelry-mark.svg" alt="Capelry logo" width="104" height="104" />
  </a>

  <h1>Capelry Skills</h1>

  <p><strong>Let your coding agent forage for the right capability.</strong> Search, inspect, install, and publish reusable agent skills from <a href="https://capelry.com">Capelry.com</a> — calm, quick, and project-local.</p>

  <p>
    <a href="https://capelry.com"><strong>Visit Capelry</strong></a>
    ·
    <a href="https://github.com/capelry-ai/capelry-skills/blob/main/skills/capelry/BOOTSTRAP.md"><strong>Bootstrap an Agent</strong></a>
    ·
    <a href="https://github.com/capelry-ai/capelry-skills"><strong>GitHub Repo</strong></a>
  </p>
</div>

---

## Why Capelry? 🌿

Your coding assistant is more useful when it can discover and install the right capabilities on demand. **Capelry is an agentic skill registry**: a place for AI agents to find reusable skills, prompts, commands, workflows, agents, hooks, rules, extensions, and collections.

This repository contains the **Capelry registry skill**: a portable Agent Skill that teaches your AI coding assistant how to use the Capelry registry. Point your agent at the bootstrap prompt, and it can install the skill into your project, search the registry, inspect capabilities, add useful skills for the task at hand, and keep itself current from GitHub releases.

> Capelry.com is the public registry experience for discovering and sharing agent capabilities: **[https://capelry.com](https://capelry.com)**.

## Table of contents

- [Quick start: point your agent here](https://github.com/capelry-ai/capelry-skills#quick-start-point-your-agent-here)
- [What your agent learns](https://github.com/capelry-ai/capelry-skills#what-your-agent-learns)
- [After install](https://github.com/capelry-ai/capelry-skills#after-install)
  - [Claude Code](https://github.com/capelry-ai/capelry-skills#claude-code)
  - [OpenAI Codex](https://github.com/capelry-ai/capelry-skills#openai-codex)
  - [Pi](https://github.com/capelry-ai/capelry-skills#pi)
  - [Cursor](https://github.com/capelry-ai/capelry-skills#cursor)
  - [Windsurf](https://github.com/capelry-ai/capelry-skills#windsurf)
  - [GitHub Copilot](https://github.com/capelry-ai/capelry-skills#github-copilot)
  - [Cline and Roo Code](https://github.com/capelry-ai/capelry-skills#cline-and-roo-code)
  - [Direct CLI](https://github.com/capelry-ai/capelry-skills#direct-cli)
- [Version and self-update](https://github.com/capelry-ai/capelry-skills#version-and-self-update)
- [Release versioning](https://github.com/capelry-ai/capelry-skills#release-versioning)
- [Testing and CI](https://github.com/capelry-ai/capelry-skills#testing-and-ci)
- [Registry URL](https://github.com/capelry-ai/capelry-skills#registry-url)
- [Repository tour](https://github.com/capelry-ai/capelry-skills#repository-tour)
- [Install targets](https://github.com/capelry-ai/capelry-skills#install-targets)
- [No native skill loader?](https://github.com/capelry-ai/capelry-skills#no-native-skill-loader)
- [Browse safely](https://github.com/capelry-ai/capelry-skills#browse-safely)

## Quick start: point your agent here

Copy this into your agent:

```text
Read and follow https://github.com/capelry-ai/capelry-skills/raw/main/skills/capelry/BOOTSTRAP.md to install the Capelry skill into this project. Choose the best project-local target for this coding agent using the bootstrap guidance; if unsure, use the portable Agent Skills default.
```

That is all that is needed. The bootstrap prompt installs the skill from GitHub source, then the installed skill uses Capelry.com for registry operations. It is designed for fresh projects and is intentionally boring in the best way:

- ✅ Python 3.9+
- ✅ Linux, macOS, and Windows friendly
- ✅ No bash required
- ✅ No curl required
- ✅ No unzip command required
- ✅ No Node.js, npm, or package manager required

After your agent follows the bootstrap prompt, reload or restart your agent so it notices the new skill.

## What your agent learns

Once installed, the Capelry skill helps your agent:

| Superpower | What it means |
| --- | --- |
| 🔎 Search | Find relevant capabilities from Capelry. |
| 🧭 Discover | Batch related searches and bulk-inspect top refs into an actionable shortlist. |
| 📖 Inspect | Read metadata, versions, source info, and checksums before installing. |
| 📦 Install | Add skills into project-local or global skill directories. |
| ⬆️ Self-update | Check the installed Capelry skill version and replace it from the latest GitHub `vX.X.X` release/tag. |
| 🛠️ Package and publish | Prepare capability archives for the registry. |

In short: describe the job, and Capelry helps your agent find the right capability without wandering the tooling swamp. 🌿

## After install

Once Capelry is installed, reload or restart your agent so it notices the new skill. Then give it a clear first mission:

```text
Use Capelry to discover a shortlist of skills that help create agent skills, inspect the best match, and install it into this project.
```

### Claude Code

Best target: `.claude/skills/capelry` for Claude Code project skills, or `.agents/skills/capelry` for the portable default.

After install:

1. Restart your Claude Code session.
2. If the skill is not auto-loaded, point Claude at the installed instructions:

```text
Read .claude/skills/capelry/SKILL.md as project instructions, then use Capelry to search for useful skills for this project.
```

If you used the portable default, swap the path for `.agents/skills/capelry/SKILL.md`.

### OpenAI Codex

Best target: `.agents/skills/capelry` for portable Agent Skills, or `.codex/skills/capelry` if your Codex setup reads that directory.

After install, restart the Codex session and prompt it with:

```text
Use the Capelry skill at .agents/skills/capelry/SKILL.md to search, inspect, and install capabilities for this project.
```

If you installed into `.codex/skills/capelry`, use that `SKILL.md` path instead.

### Pi

Best target: `.pi/skills/capelry` for Pi-native project use, or `.agents/skills/capelry` for the portable default.

In Pi, reload and enable the skill:

```text
/reload
/skill:capelry
```

Then ask Pi to search, inspect, or install from Capelry.

### Cursor

Best target: `.agents/skills/capelry`, then reference the installed `SKILL.md` from Cursor's project instructions/rules or in the agent chat.

Use this prompt to get started:

```text
Read .agents/skills/capelry/SKILL.md as project instructions. Then use Capelry to find and install a skill that helps with my current task.
```

### Windsurf

Best target: `.agents/skills/capelry`, then reference the installed `SKILL.md` from Windsurf's project instructions/rules or in the agent chat.

Use this prompt to get started:

```text
Read .agents/skills/capelry/SKILL.md as project instructions. Then use Capelry to search for relevant capabilities and recommend what to install.
```

### GitHub Copilot

Best target: `.agents/skills/capelry`.

For Copilot Chat or Copilot coding agent workflows, add a project instruction or paste:

```text
For capability discovery and installation, use the Capelry skill at .agents/skills/capelry/SKILL.md. Prefer project-local installs when adding skills.
```

### Cline and Roo Code

Best target: `.agents/skills/capelry`.

Add the installed skill file to your project rules/instructions, or paste this into the agent:

```text
Read .agents/skills/capelry/SKILL.md before searching for external capabilities. Use Capelry for skill discovery and project-local installs.
```

### Direct CLI

You can always run the bundled CLI directly from the installed skill. Examples use `python3`; substitute `py` on Windows or `python` if that is your Python 3 launcher.

For Pi project-local installs:

```text
python3 .pi/skills/capelry/scripts/capelry.py discover "feature planning skills" --query "feature planning,feature,prd,implementation plan" --top 5 --install-snippet pi-project
python3 .pi/skills/capelry/scripts/capelry.py search "skill creator" --type skill --status passed
python3 .pi/skills/capelry/scripts/capelry.py info openai/skill-creator --install-snippet pi-project
python3 .pi/skills/capelry/scripts/capelry.py bulk-info openai/skill-creator capelry/capelry --install-snippet pi-project
python3 .pi/skills/capelry/scripts/capelry.py install openai/skill-creator --target pi-project
```

For portable Agent Skills installs:

```text
python3 .agents/skills/capelry/scripts/capelry.py search "skill creator" --type skill --status passed
python3 .agents/skills/capelry/scripts/capelry.py info openai/skill-creator --install-snippet agents-project
python3 .agents/skills/capelry/scripts/capelry.py install openai/skill-creator --target agents-project
```

Agent-friendly discovery output is available with filters and JSON. `search`, `discover`, `info`, and supported `install` flows try ARD endpoints first (`POST /search` and `GET /agents`). Until every deployed registry exposes those routes, the CLI automatically falls back to the legacy Capelry API when an ARD endpoint is missing; pass `--api ard` to fail closed or `--api legacy` / `CAPELRY_USE_LEGACY_API=1` to intentionally use legacy compatibility:

```text
python3 .pi/skills/capelry/scripts/capelry.py discover "production readiness" --top 5 --install-snippet pi-project --json
python3 .pi/skills/capelry/scripts/capelry.py search "skill creator" --type skill --trust-state source-hosted --json
python3 .pi/skills/capelry/scripts/capelry.py install openai/skill-creator --target pi-project
python3 .pi/skills/capelry/scripts/capelry.py search "skill creator" --api legacy --type skill --status passed --json
```

Check and update the installed Capelry skill itself:

```text
python3 .pi/skills/capelry/scripts/capelry.py version
python3 .pi/skills/capelry/scripts/capelry.py self-update --dry-run
python3 .pi/skills/capelry/scripts/capelry.py self-update --yes
```

## Version and self-update

Yes: the Capelry skill can check its own installed version and update itself from GitHub. The bundled CLI compares the local installed `capability.yaml` version with the highest stable `vX.X.X` release/tag in `capelry-ai/capelry-skills`, then downloads `skills/capelry` from that ref.

```text
python3 <capelry-skill-dir>/scripts/capelry.py version
python3 <capelry-skill-dir>/scripts/capelry.py version --check
python3 <capelry-skill-dir>/scripts/capelry.py self-update --dry-run
python3 <capelry-skill-dir>/scripts/capelry.py self-update --yes
python3 <capelry-skill-dir>/scripts/capelry.py self-update --ref v1.1.0 --yes
```

Self-update is opt-in and filesystem-writing: it prompts in interactive terminals and requires `--yes` for non-interactive runs. It is intended for installed skill copies; use `git` to update this source checkout unless you explicitly pass `--allow-source-checkout`. Existing pre-1.1.0 installs need one manual re-bootstrap/reinstall to get the `self-update` command. Reload or restart your agent afterward. If GitHub API rate limits are hit, set `CAPELRY_GITHUB_TOKEN`, `GITHUB_TOKEN`, or `GH_TOKEN`.

## Release versioning

Release GitHub tags and releases as stable `vX.X.X` refs, for example `v1.1.0`. Keep `skills/capelry/capability.yaml` at the matching registry package version without the `v` prefix, for example `1.1.0`.

Recommended release flow:

1. Bump `skills/capelry/capability.yaml` and docs/package examples to the new `X.X.X` version.
2. Validate the CLI: `python3 -m py_compile skills/capelry/scripts/capelry.py` and `python3 skills/capelry/scripts/capelry.py version --ref vX.X.X` after the tag exists.
3. Package from `skills/capelry`: `python3 -m zipfile -c capelry-X.X.X.zip capability.yaml SKILL.md BOOTSTRAP.md ai-catalog.json agents scripts`.
4. Commit, tag, and push: `git tag -a vX.X.X -m "vX.X.X" && git push origin main vX.X.X`.
5. Create the GitHub release for `vX.X.X`, then smoke-test a 1.1.0+ install with `self-update --ref vX.X.X --yes`. For the first self-update release, pre-1.1.0 installs must be re-bootstrapped once.

## Testing and CI

The Capelry skill scripts are validated with a stdlib-only Python harness and GitHub Actions CI.

Run the same checks locally:

```text
python3 -m unittest discover -s tests
python3 -m py_compile skills/capelry/scripts/capelry.py skills/capelry/scripts/bootstrap.py
```

The fixture HTTP server in `tests/test_capelry_scripts.py` emulates legacy capability endpoints plus ARD `/search` and `/agents` so the client can evolve without third-party Python test dependencies.

## Registry URL

The Capelry registry home is:

```text
https://capelry.com
```

The bundled registry CLI defaults to Capelry.com. Override the registry only if you are using a private, staging, or self-hosted Capelry registry:

```text
CAPELRY_REGISTRY_URL=https://your-registry.example.com
```

Useful links:

- Website: [https://capelry.com](https://capelry.com)
- API docs: [https://capelry.com/docs/api](https://capelry.com/docs/api)
- OpenAPI JSON: [https://capelry.com/api/openapi](https://capelry.com/api/openapi)
- Skills repository: [https://github.com/capelry-ai/capelry-skills](https://github.com/capelry-ai/capelry-skills)
- Bootstrap source repository: [https://github.com/capelry-ai/capelry-skills](https://github.com/capelry-ai/capelry-skills)
- Bootstrap prompt: [https://github.com/capelry-ai/capelry-skills/blob/main/skills/capelry/BOOTSTRAP.md](https://github.com/capelry-ai/capelry-skills/blob/main/skills/capelry/BOOTSTRAP.md)
- Agent-readable bootstrap prompt: [https://github.com/capelry-ai/capelry-skills/raw/main/skills/capelry/BOOTSTRAP.md](https://github.com/capelry-ai/capelry-skills/raw/main/skills/capelry/BOOTSTRAP.md)
- Skill instructions: [https://github.com/capelry-ai/capelry-skills/blob/main/skills/capelry/SKILL.md](https://github.com/capelry-ai/capelry-skills/blob/main/skills/capelry/SKILL.md)

## Repository tour

| Path | Purpose |
| --- | --- |
| [`capelry-mark.svg`](https://github.com/capelry-ai/capelry-skills/blob/main/capelry-mark.svg) | Friendly Capelry mark. |
| [`skills/capelry/BOOTSTRAP.md`](https://github.com/capelry-ai/capelry-skills/blob/main/skills/capelry/BOOTSTRAP.md) | Start here: the agent-facing bootstrap prompt. |
| [`skills/capelry/SKILL.md`](https://github.com/capelry-ai/capelry-skills/blob/main/skills/capelry/SKILL.md) | The actual skill instructions agents load. |
| [`skills/capelry/capability.yaml`](https://github.com/capelry-ai/capelry-skills/blob/main/skills/capelry/capability.yaml) | Legacy Capelry package manifest. |
| [`skills/capelry/ai-catalog.json`](https://github.com/capelry-ai/capelry-skills/blob/main/skills/capelry/ai-catalog.json) | ARD/AI Catalog self-entry for the Capelry skill. |
| [`skills/capelry/agents/openai.yaml`](https://github.com/capelry-ai/capelry-skills/blob/main/skills/capelry/agents/openai.yaml) | UI/display metadata. |
| [`skills/capelry/scripts/bootstrap.py`](https://github.com/capelry-ai/capelry-skills/blob/main/skills/capelry/scripts/bootstrap.py) | OS-neutral GitHub-source bootstrap installer. |
| [`skills/capelry/scripts/capelry.py`](https://github.com/capelry-ai/capelry-skills/blob/main/skills/capelry/scripts/capelry.py) | Small stdlib-only registry and self-update CLI. |

## Install targets

Capelry prefers project-local installs, so experiments stay safely inside your repo.

| Target | Path |
| --- | --- |
| Portable project default | `.agents/skills/capelry` |
| Pi project | `.pi/skills/capelry` |
| Claude Code project | `.claude/skills/capelry` |
| Codex-style project | `.codex/skills/capelry` |
| Portable global | `~/.agents/skills/capelry` |
| Pi global | `~/.pi/agent/skills/capelry` |
| Claude Code global | `~/.claude/skills/capelry` |
| Codex-style global | `~/.codex/skills/capelry` |

## No native skill loader?

No problem. If your agent can read files and run Python, paste this:

```text
Read https://github.com/capelry-ai/capelry-skills/raw/main/skills/capelry/SKILL.md as project instructions. Then use the Capelry CLI from https://github.com/capelry-ai/capelry-skills/blob/main/skills/capelry/scripts/capelry.py for registry operations. If installing Capelry into a different project, read and follow https://github.com/capelry-ai/capelry-skills/raw/main/skills/capelry/BOOTSTRAP.md first.
```

## Browse safely

Skills are executable instructions. Prefer the workflow: search → info → compare → install. Before running third-party scripts, ask your agent to inspect the `SKILL.md` and any bundled scripts. Prefer project-local installs while exploring. You can review the source skill instructions at [https://github.com/capelry-ai/capelry-skills/blob/main/skills/capelry/SKILL.md](https://github.com/capelry-ai/capelry-skills/blob/main/skills/capelry/SKILL.md).

---

<div align="center">
  <p><strong>Ready?</strong></p>
  <p>Send your agent to <a href="https://github.com/capelry-ai/capelry-skills/raw/main/skills/capelry/BOOTSTRAP.md">BOOTSTRAP.md</a> and let it start foraging for skills. 🌿</p>
</div>

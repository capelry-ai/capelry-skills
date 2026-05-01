<div align="center">
  <a href="https://capelry.com">
    <img src="./capelry-mark.svg" alt="Capelry logo" width="104" height="104" />
  </a>

  <h1>Capelry Skills</h1>

  <p><strong>Let your coding agent forage for the right capability.</strong> Search, inspect, install, and publish reusable agent skills from <a href="https://capelry.com">Capelry.com</a> — calm, quick, and project-local.</p>

  <p>
    <a href="https://capelry.com"><strong>Visit Capelry</strong></a>
    ·
    <a href="https://github.com/capelry-ai/capelry/blob/main/skills/capelry/BOOTSTRAP.md"><strong>Bootstrap an Agent</strong></a>
    ·
    <a href="https://github.com/capelry-ai/capelry-skills"><strong>GitHub Repo</strong></a>
  </p>
</div>

---

## Why Capelry? 🌿

Your coding assistant is more useful when it can discover and install the right capabilities on demand. **Capelry is an agentic skill registry**: a place for AI agents to find reusable skills, prompts, commands, workflows, agents, hooks, rules, extensions, and collections.

This repository contains the **Capelry registry skill**: a portable Agent Skill that teaches your AI coding assistant how to use the Capelry registry. Point your agent at the bootstrap prompt, and it can install the skill into your project, search the registry, inspect capabilities, and add useful skills for the task at hand.

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
- [Registry URL](https://github.com/capelry-ai/capelry-skills#registry-url)
- [Repository tour](https://github.com/capelry-ai/capelry-skills#repository-tour)
- [Install targets](https://github.com/capelry-ai/capelry-skills#install-targets)
- [No native skill loader?](https://github.com/capelry-ai/capelry-skills#no-native-skill-loader)
- [Browse safely](https://github.com/capelry-ai/capelry-skills#browse-safely)

## Quick start: point your agent here

Copy this into your agent:

```text
Read and follow https://github.com/capelry-ai/capelry/raw/main/skills/capelry/BOOTSTRAP.md to install the Capelry skill into this project. Choose the best project-local target for this coding agent using the bootstrap guidance; if unsure, use the portable Agent Skills default.
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
| 📖 Inspect | Read metadata, versions, source info, and checksums before installing. |
| 📦 Install | Add skills into project-local or global skill directories. |
| 🛠️ Package and publish | Prepare capability archives for the registry. |

In short: describe the job, and Capelry helps your agent find the right capability without wandering the tooling swamp. 🌿

## After install

Once Capelry is installed, reload or restart your agent so it notices the new skill. Then give it a clear first mission:

```text
Use Capelry to search for a skill that helps create agent skills, inspect the best match, and install it into this project.
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

You can always run the bundled CLI directly from the installed skill:

```text
python .agents/skills/capelry/scripts/capelry.py search "skill creator"
python .agents/skills/capelry/scripts/capelry.py info openai/skill-creator
python .agents/skills/capelry/scripts/capelry.py install openai/skill-creator --target agents-project
```

For Pi project-local installs:

```text
python .agents/skills/capelry/scripts/capelry.py install openai/skill-creator --target pi-project
```

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
- Skills repository: [https://github.com/capelry-ai/capelry-skills](https://github.com/capelry-ai/capelry-skills)
- Bootstrap source repository: [https://github.com/capelry-ai/capelry](https://github.com/capelry-ai/capelry)
- Bootstrap prompt: [https://github.com/capelry-ai/capelry/blob/main/skills/capelry/BOOTSTRAP.md](https://github.com/capelry-ai/capelry/blob/main/skills/capelry/BOOTSTRAP.md)
- Agent-readable bootstrap prompt: [https://github.com/capelry-ai/capelry/raw/main/skills/capelry/BOOTSTRAP.md](https://github.com/capelry-ai/capelry/raw/main/skills/capelry/BOOTSTRAP.md)
- Skill instructions: [https://github.com/capelry-ai/capelry-skills/blob/main/skills/capelry/SKILL.md](https://github.com/capelry-ai/capelry-skills/blob/main/skills/capelry/SKILL.md)

## Repository tour

| Path | Purpose |
| --- | --- |
| [`capelry-mark.svg`](https://github.com/capelry-ai/capelry-skills/blob/main/capelry-mark.svg) | Friendly Capelry mark. |
| [`skills/capelry/BOOTSTRAP.md`](https://github.com/capelry-ai/capelry-skills/blob/main/skills/capelry/BOOTSTRAP.md) | Start here: the agent-facing bootstrap prompt. |
| [`skills/capelry/SKILL.md`](https://github.com/capelry-ai/capelry-skills/blob/main/skills/capelry/SKILL.md) | The actual skill instructions agents load. |
| [`skills/capelry/capability.yaml`](https://github.com/capelry-ai/capelry-skills/blob/main/skills/capelry/capability.yaml) | Capelry package manifest. |
| [`skills/capelry/agents/openai.yaml`](https://github.com/capelry-ai/capelry-skills/blob/main/skills/capelry/agents/openai.yaml) | UI/display metadata. |
| [`skills/capelry/scripts/bootstrap.py`](https://github.com/capelry-ai/capelry-skills/blob/main/skills/capelry/scripts/bootstrap.py) | OS-neutral GitHub-source bootstrap installer. |
| [`skills/capelry/scripts/capelry.py`](https://github.com/capelry-ai/capelry-skills/blob/main/skills/capelry/scripts/capelry.py) | Small stdlib-only registry CLI. |

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
Read https://github.com/capelry-ai/capelry-skills/raw/main/skills/capelry/SKILL.md as project instructions. Then use the Capelry CLI from https://github.com/capelry-ai/capelry-skills/blob/main/skills/capelry/scripts/capelry.py for registry operations. If installing Capelry into a different project, read and follow https://github.com/capelry-ai/capelry/raw/main/skills/capelry/BOOTSTRAP.md first.
```

## Browse safely

Skills are executable instructions. Before running third-party scripts, ask your agent to inspect the installed `SKILL.md` and any bundled scripts. Prefer project-local installs while exploring. You can review the source skill instructions at [https://github.com/capelry-ai/capelry-skills/blob/main/skills/capelry/SKILL.md](https://github.com/capelry-ai/capelry-skills/blob/main/skills/capelry/SKILL.md).

---

<div align="center">
  <p><strong>Ready?</strong></p>
  <p>Send your agent to <a href="https://github.com/capelry-ai/capelry/raw/main/skills/capelry/BOOTSTRAP.md">BOOTSTRAP.md</a> and let it start foraging for skills. 🌿</p>
</div>

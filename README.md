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
  - [Verified harness matrix](https://github.com/capelry-ai/capelry-skills#verified-harness-matrix)
  - [Direct CLI](https://github.com/capelry-ai/capelry-skills#direct-cli)
- [Version and self-update](https://github.com/capelry-ai/capelry-skills#version-and-self-update)
- [Release versioning](https://github.com/capelry-ai/capelry-skills#release-versioning)
- [Testing and CI](https://github.com/capelry-ai/capelry-skills#testing-and-ci)
- [Registry URL](https://github.com/capelry-ai/capelry-skills#registry-url)
- [User agent](https://github.com/capelry-ai/capelry-skills#user-agent)
- [Repository tour](https://github.com/capelry-ai/capelry-skills#repository-tour)
- [Install targets](https://github.com/capelry-ai/capelry-skills#install-targets)
- [No native skill loader?](https://github.com/capelry-ai/capelry-skills#no-native-skill-loader)
- [Browse safely](https://github.com/capelry-ai/capelry-skills#browse-safely)

## Quick start: point your agent here

Most users should install Capelry into the current project so each repo controls its own agent skills.

Copy this into your agent to install into this project:

```text
Read and follow https://github.com/capelry-ai/capelry-skills/raw/main/skills/capelry/BOOTSTRAP.md to install the Capelry skill into this project. Identify this coding harness, choose its documented project target, pass that target explicitly, validate the result, and run the harness-specific reload/list check.
```

If you want Capelry available across all projects on this machine, use a global install instead.

Copy this into your agent to install globally:

```text
Read and follow https://github.com/capelry-ai/capelry-skills/raw/main/skills/capelry/BOOTSTRAP.md to install the Capelry skill globally for this coding agent. Identify this coding harness, choose its documented global target, pass that target explicitly, validate the result, and run the harness-specific reload/list check.
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
| 🧭 Discover | Batch related searches into an actionable shortlist. |
| 📖 Inspect | Read metadata, versions, source info, and checksums before installing. |
| 📦 Install | Add skills to verified project/global paths for the active coding harness. |
| ✅ Validate | Enforce portable `SKILL.md` name/description requirements before replacing an install. |
| ⬆️ Self-update | Check the installed Capelry skill version and replace it from the latest GitHub `vX.X.X` release/tag. |
| 🛠️ Package and publish | Prepare capability archives for the registry. |

In short: describe the job, and Capelry helps your agent find the right capability without wandering the tooling swamp. 🌿

## After install

Once Capelry is installed, reload or restart your agent so it notices the new skill. Then give it a clear first mission:

```text
Use Capelry to discover a shortlist of skills that help create agent skills, inspect the best match, and install it into this project.
```

### Verified harness matrix

The Agent Skills standard defines package contents, not install paths. Capelry now has explicit project and global targets for the major coding harnesses and validates every installed package before it can replace an existing skill.

| Harness | Project target and path | Global target and path | Confirm after install |
| --- | --- | --- | --- |
| Portable Agent Skills | `agents-project` → `.agents/skills` | `agents-global` → `~/.agents/skills` | Reload/restart and inspect the skill list. |
| Claude Code | `claude-project` → `.claude/skills` | `claude-global` → `~/.claude/skills` | Invoke `/capelry`; restart if the top-level directory was created after startup. |
| OpenAI Codex | `codex-project` → `.agents/skills` | `codex-global` → `~/.agents/skills` | Use `/skills` or `$capelry`; `.codex/skills` is not a documented Codex root. |
| Pi | `pi-project` → `.pi/skills` | `pi-global` → `~/.pi/agent/skills` | Run `/reload`, then `/skill:capelry`. |
| OpenCode | `opencode-project` → `.opencode/skills` | `opencode-global` → `~/.config/opencode/skills` | Confirm the `skill` tool lists it and permissions allow it. |
| Gemini CLI | `gemini-project` → `.gemini/skills` | `gemini-global` → `~/.gemini/skills` | Run `/skills reload`, then `/skills list`. |
| Cursor | `cursor-project` → `.cursor/skills` | `cursor-global` → `~/.cursor/skills` | Open **Customize > Skills** or invoke `/capelry`. |
| Windsurf Cascade | `windsurf-project` → `.windsurf/skills` | `windsurf-global` → `~/.codeium/windsurf/skills` | Invoke `@capelry`. |
| GitHub Copilot / VS Code | `copilot-project` → `.github/skills` | `copilot-global` → `~/.copilot/skills` | In Copilot CLI run `/skills reload` and `/skills info capelry`. |
| Cline | `cline-project` → `.cline/skills` | `cline-global` → `~/.cline/skills` | Enable it in the Skills menu or invoke `/capelry`. |
| Roo Code | `roo-project` → `.roo/skills` | `roo-global` → `~/.roo/skills` | Confirm it is available in the current mode. |
| JetBrains Junie | `junie-project` → `.junie/skills` | `junie-global` → `~/.junie/skills` | Invoke `/capelry` or `$capelry`. |
| Kiro | `kiro-project` → `.kiro/skills` | `kiro-global` → `~/.kiro/skills` | Restart if needed; custom agents need a `skill://` resource. |
| Factory Droid | `factory-project` → `.factory/skills` | `factory-global` → `~/.factory/skills` | Start a new Droid session if absent. |

`.agents/skills` is natively documented by Codex, Pi, OpenCode, Gemini CLI, Cursor, GitHub Copilot, Roo Code, Junie, Factory, and OpenHands. It is not a documented auto-discovery path for Claude Code, Cline, or Kiro, and Windsurf's guarantee is surface-specific. Use their native targets.

See [`skills/capelry/references/harnesses.md`](skills/capelry/references/harnesses.md) for the full evidence-backed matrix, frontmatter rules, caveats, and official source links.

### Direct CLI

You can always run the bundled CLI directly from the installed skill. Examples use `python3`; substitute `py` on Windows or `python` if that is your Python 3 launcher.

List verified targets and validate a local skill:

```text
python3 <capelry-skill-dir>/scripts/capelry.py targets --json
python3 <capelry-skill-dir>/scripts/capelry.py targets --harness claude
python3 <capelry-skill-dir>/scripts/capelry.py validate-skill path/to/skill --json
```

For Pi project-local installs:

```text
python3 .pi/skills/capelry/scripts/capelry.py discover "feature planning skills" --query "feature planning,feature,prd,implementation plan" --top 5 --install-snippet pi-project
python3 .pi/skills/capelry/scripts/capelry.py search "skill creator" --type skill --trust-state source-hosted
python3 .pi/skills/capelry/scripts/capelry.py info capelry-ai/capelry-skills/capelry --install-snippet pi-project
python3 .pi/skills/capelry/scripts/capelry.py install capelry-ai/capelry-skills/capelry --target pi-project
```

For portable Agent Skills installs:

```text
python3 .agents/skills/capelry/scripts/capelry.py search "skill creator" --type skill --trust-state source-hosted
python3 .agents/skills/capelry/scripts/capelry.py info capelry-ai/capelry-skills/capelry --install-snippet agents-project
python3 .agents/skills/capelry/scripts/capelry.py install capelry-ai/capelry-skills/capelry --target agents-project
```

Agent-friendly discovery output is available with filters and JSON. `search`, `explore`, `discover`, `info`, and supported `install` flows use ARD endpoints (`POST /search`, `POST /explore`, and `GET /agents`). Human refs are catalog-aware `namespace/catalog/resource` slugs resolved through `metadata.com.capelry.slug`:

```text
python3 <capelry-skill-dir>/scripts/capelry.py discover "production readiness" --top 5 --install-snippet agents-project --json
python3 <capelry-skill-dir>/scripts/capelry.py explore "production readiness" --field metadata.com.capelry.catalogPath --limit 10
python3 <capelry-skill-dir>/scripts/capelry.py search "skill creator" --type skill --trust-state source-hosted --json
python3 <capelry-skill-dir>/scripts/capelry.py info capelry-ai/capelry-skills/capelry --install-snippet agents-project --json
python3 <capelry-skill-dir>/scripts/capelry.py install capelry-ai/capelry-skills/capelry --target agents-project
```

Replace `agents-project` with the active harness target. Install every supported skill from a catalog with a dry run first:

```text
python3 <capelry-skill-dir>/scripts/capelry.py install-catalog y30k/ai-capabilities --target agents-project --dry-run
python3 <capelry-skill-dir>/scripts/capelry.py install-catalog y30k/ai-capabilities --target agents-project --force --yes
```

Check and update the installed Capelry skill itself:

```text
python3 <capelry-skill-dir>/scripts/capelry.py version
python3 <capelry-skill-dir>/scripts/capelry.py self-update --dry-run
python3 <capelry-skill-dir>/scripts/capelry.py self-update --yes
```

## Version and self-update

Yes: the Capelry skill can check its own installed version and update itself from GitHub. The bundled CLI compares the local installed `capability.yaml` version with the highest stable `vX.X.X` release/tag in `capelry-ai/capelry-skills`, then downloads `skills/capelry` from that ref.

```text
python3 <capelry-skill-dir>/scripts/capelry.py version
python3 <capelry-skill-dir>/scripts/capelry.py version --check
python3 <capelry-skill-dir>/scripts/capelry.py self-update --dry-run
python3 <capelry-skill-dir>/scripts/capelry.py self-update --yes
python3 <capelry-skill-dir>/scripts/capelry.py self-update --ref vX.Y.Z --yes
```

Self-update is opt-in and filesystem-writing: it prompts in interactive terminals and requires `--yes` for non-interactive runs. It is intended for installed skill copies; use `git` to update this source checkout unless you explicitly pass `--allow-source-checkout`. Existing pre-1.1.0 installs need one manual re-bootstrap/reinstall to get the `self-update` command. Reload or restart your agent afterward. If GitHub API rate limits are hit, set `CAPELRY_GITHUB_TOKEN`, `GITHUB_TOKEN`, or `GH_TOKEN`.

For maintainers testing unreleased local changes from this source checkout, sync the checked-out skill into an installed target with a built-in backup:

```text
python3 skills/capelry/scripts/capelry.py sync-install --target pi-global --dry-run
python3 skills/capelry/scripts/capelry.py sync-install --target pi-global --yes
```

Use `--dest /path/to/skills/capelry` for an exact destination. `sync-install` keeps backups as `.zip` archives only; do not create persistent backup directories inside agent skill roots because agent harnesses may load them as duplicate skills. Reload or restart the agent after syncing.

## Release versioning

Release GitHub tags and releases as stable `vX.X.X` refs, for example `v2.1.0`. Keep `skills/capelry/capability.yaml` at the matching registry package version without the `v` prefix, for example `2.1.0`.

Recommended release flow:

1. Bump `skills/capelry/capability.yaml` and docs/package examples to the new `X.X.X` version.
2. Validate the CLI: `python3 -m py_compile skills/capelry/scripts/capelry.py` and `python3 skills/capelry/scripts/capelry.py version --ref vX.X.X` after the tag exists.
3. Package from `skills/capelry`: `python3 -m zipfile -c capelry-X.X.X.zip capability.yaml SKILL.md BOOTSTRAP.md ai-catalog.json agents scripts references`.
4. Commit, tag, and push: `git tag -a vX.X.X -m "vX.X.X" && git push origin main vX.X.X`.
5. Create the GitHub release for `vX.X.X`, then smoke-test a 1.1.0+ install with `self-update --ref vX.X.X --yes`. For the first self-update release, pre-1.1.0 installs must be re-bootstrapped once.

## Testing and CI

The Capelry skill scripts are validated with a stdlib-only Python harness and GitHub Actions CI.

Run the same checks locally:

```text
python3 -m unittest discover -s tests
python3 -m py_compile skills/capelry/scripts/capelry.py skills/capelry/scripts/bootstrap.py
python3 skills/capelry/scripts/capelry.py validate-skill skills/capelry
```

The fixture HTTP server in `tests/test_capelry_scripts.py` emulates ARD `/search`, `/explore`, `/agents`, and archive responses so the client can evolve without third-party Python test dependencies.

## Registry URL

The Capelry registry home is:

```text
https://capelry.com
```

The bundled registry CLI defaults to Capelry.com. Override the registry only if you are using a private, staging, or self-hosted Capelry registry:

```text
CAPELRY_REGISTRY_URL=https://your-registry.example.com
```

## User agent

The bundled client sends `User-Agent: capelry-client` by default so Capelry.com can attribute client usage. The bootstrap helper sends `capelry-client bootstrap`. To identify your integration in registry or GitHub logs, append a product token without replacing the Capelry client token:

```bash
CAPELRY_USER_AGENT_SUFFIX="my-agent/1.0" python3 .agents/skills/capelry/scripts/capelry.py search "skill creator"
```

Use `CAPELRY_USER_AGENT` only when you need a full override. Avoid personal data; use an app, agent, company, or deployment identifier.

Useful links:

- Website: [https://capelry.com](https://capelry.com)
- API docs: [https://capelry.com/docs/api](https://capelry.com/docs/api)
- OpenAPI JSON: [https://capelry.com/api/openapi](https://capelry.com/api/openapi)
- Repository AI Catalog manifest: [https://github.com/capelry-ai/capelry-skills/blob/main/.well-known/ai-catalog.json](https://github.com/capelry-ai/capelry-skills/blob/main/.well-known/ai-catalog.json)
- Skills repository: [https://github.com/capelry-ai/capelry-skills](https://github.com/capelry-ai/capelry-skills)
- Bootstrap source repository: [https://github.com/capelry-ai/capelry-skills](https://github.com/capelry-ai/capelry-skills)
- Bootstrap prompt: [https://github.com/capelry-ai/capelry-skills/blob/main/skills/capelry/BOOTSTRAP.md](https://github.com/capelry-ai/capelry-skills/blob/main/skills/capelry/BOOTSTRAP.md)
- Agent-readable bootstrap prompt: [https://github.com/capelry-ai/capelry-skills/raw/main/skills/capelry/BOOTSTRAP.md](https://github.com/capelry-ai/capelry-skills/raw/main/skills/capelry/BOOTSTRAP.md)
- Skill instructions: [https://github.com/capelry-ai/capelry-skills/blob/main/skills/capelry/SKILL.md](https://github.com/capelry-ai/capelry-skills/blob/main/skills/capelry/SKILL.md)

## Repository tour

| Path | Purpose |
| --- | --- |
| [`.well-known/ai-catalog.json`](https://github.com/capelry-ai/capelry-skills/blob/main/.well-known/ai-catalog.json) | Repository-level ARD/AI Catalog manifest. |
| [`docs/harness-compatibility-review.md`](https://github.com/capelry-ai/capelry-skills/blob/main/docs/harness-compatibility-review.md) | Full audit findings, change rationale, and verification evidence. |
| [`capelry-mark.svg`](https://github.com/capelry-ai/capelry-skills/blob/main/capelry-mark.svg) | Friendly Capelry mark. |
| [`skills/capelry/BOOTSTRAP.md`](https://github.com/capelry-ai/capelry-skills/blob/main/skills/capelry/BOOTSTRAP.md) | Start here: the agent-facing bootstrap prompt. |
| [`skills/capelry/SKILL.md`](https://github.com/capelry-ai/capelry-skills/blob/main/skills/capelry/SKILL.md) | The actual skill instructions agents load. |
| [`skills/capelry/capability.yaml`](https://github.com/capelry-ai/capelry-skills/blob/main/skills/capelry/capability.yaml) | Capelry package manifest kept in sync with ARD catalog metadata. |
| [`skills/capelry/ai-catalog.json`](https://github.com/capelry-ai/capelry-skills/blob/main/skills/capelry/ai-catalog.json) | ARD/AI Catalog self-entry for the Capelry skill. |
| [`skills/capelry/agents/openai.yaml`](https://github.com/capelry-ai/capelry-skills/blob/main/skills/capelry/agents/openai.yaml) | OpenAI UI/display metadata. |
| [`skills/capelry/references/harnesses.md`](https://github.com/capelry-ai/capelry-skills/blob/main/skills/capelry/references/harnesses.md) | Verified install paths, reload behavior, portability caveats, and official sources. |
| [`skills/capelry/scripts/bootstrap.py`](https://github.com/capelry-ai/capelry-skills/blob/main/skills/capelry/scripts/bootstrap.py) | OS-neutral, validated, transactional GitHub-source bootstrap installer. |
| [`skills/capelry/scripts/capelry.py`](https://github.com/capelry-ai/capelry-skills/blob/main/skills/capelry/scripts/capelry.py) | Small stdlib-only registry and self-update CLI. |

## Install targets

Capelry prefers project-local installs and exposes verified project/global targets for each harness in the matrix above. Query the exact machine-readable roots from any installed copy:

```text
python3 <capelry-skill-dir>/scripts/capelry.py targets
python3 <capelry-skill-dir>/scripts/capelry.py targets --harness codex --json
```

Codex targets intentionally resolve to `.agents/skills`; `.codex/skills` is not a documented Codex discovery root. Do not use a generic fallback for a harness whose official documentation does not advertise it.

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

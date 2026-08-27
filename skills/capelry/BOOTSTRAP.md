# Capelry Bootstrap

This file is the fresh-project entry point for installing the `capelry` skill.

Bootstrapping installs the skill from GitHub source, not from Capelry.com:

```text
https://github.com/capelry-ai/capelry-skills
```

After install, normal ARD-first search/inspect/install registry workflows use Capelry.com:

```text
https://capelry.com
```

## Requirements

- Python 3.9+.
- No `bash`, `curl`, `unzip`, Node.js, npm, or platform-specific package manager is required.
- Works from Linux, macOS, and Windows terminals.

Examples use `python3`; if your environment only exposes Python 3 as `python` or `py`, substitute that launcher.

## Recommended fresh-project install

Run these commands from the project root. Replace `TARGET` with the active harness's project target from the matrix below (for example `claude-project`, `codex-project`, `pi-project`, or `opencode-project`). Use `agents-project` only for a harness that documents `.agents/skills` discovery.

```text
python3 -c "import urllib.request; urllib.request.urlretrieve('https://raw.githubusercontent.com/capelry-ai/capelry-skills/main/skills/capelry/scripts/bootstrap.py', 'capelry-bootstrap.py')"
python3 capelry-bootstrap.py --target TARGET
```

For PowerShell, the same commands work. If your Python launcher is `py`, use `py` instead of `python3`:

```powershell
py -c "import urllib.request; urllib.request.urlretrieve('https://raw.githubusercontent.com/capelry-ai/capelry-skills/main/skills/capelry/scripts/bootstrap.py', 'capelry-bootstrap.py')"
py capelry-bootstrap.py --target TARGET
```

The downloaded `capelry-bootstrap.py` script fetches only the Capelry skill source, rejects unsafe archive paths, validates the Agent Skills frontmatter, and atomically replaces an existing destination only after validation succeeds.

Agent requirement: identify the active coding harness and pass the matching `--target` from the matrix below. The default `agents-project` path is natively discovered by Codex, Pi, OpenCode, Gemini CLI, Cursor, GitHub Copilot, Roo Code, Junie, Factory, and OpenHands. It is **not** a documented discovery path for Claude Code, Cline, Kiro, or every Windsurf surface; use those harnesses' native targets.

To verify the install, run `scripts/capelry.py` from the installed skill directory. For the default portable target:

```text
python3 .agents/skills/capelry/scripts/capelry.py validate-skill .agents/skills/capelry
python3 .agents/skills/capelry/scripts/capelry.py targets --json
python3 .agents/skills/capelry/scripts/capelry.py version
```

For a Pi project target:

```text
python3 .pi/skills/capelry/scripts/capelry.py search skill --type skill
python3 .pi/skills/capelry/scripts/capelry.py version
```

After install, reload or restart your agent. In Pi, run:

```text
/reload
/skill:capelry
```

## Install from a checked-out package

If you are reading this inside an extracted Capelry skill package, run the bundled OS-neutral bootstrap script from the skill directory, replacing `TARGET` with the active harness target:

```text
python3 scripts/bootstrap.py --target TARGET
```

If you are at a repository root that contains `skills/capelry`, run:

```text
python3 skills/capelry/scripts/bootstrap.py --target TARGET
```

PowerShell equivalents:

```powershell
py .\scripts\bootstrap.py --target TARGET
py .\skills\capelry\scripts\bootstrap.py --target TARGET
```

Useful options:

```text
python3 scripts/bootstrap.py --repo https://github.com/capelry-ai/capelry-skills --ref main --target agents-project
python3 scripts/bootstrap.py --repo https://github.com/capelry-ai/capelry-skills --ref vX.Y.Z --target agents-project  # example published release tag
python3 scripts/bootstrap.py --target pi-project
python3 scripts/bootstrap.py --target claude-project
python3 scripts/bootstrap.py --target codex-project       # installs to Codex's documented .agents/skills path
python3 scripts/bootstrap.py --target opencode-project
python3 scripts/bootstrap.py --target gemini-project
python3 scripts/bootstrap.py --target cursor-project
python3 scripts/bootstrap.py --target windsurf-project
python3 scripts/bootstrap.py --target copilot-project
python3 scripts/bootstrap.py --target cline-project
python3 scripts/bootstrap.py --target roo-project
python3 scripts/bootstrap.py --help                       # all project/global targets
python3 scripts/bootstrap.py --source-path skills/capelry
python3 scripts/bootstrap.py --source-path .pi/skills/capelry
python3 scripts/bootstrap.py --skills-dir .custom/skills
python3 scripts/bootstrap.py --dest /absolute/path/to/skills/capelry
```

## Environment variables

The bootstrap script reads these optional variables:

| Variable                       | Default                              | Purpose                                      |
| ------------------------------ | ------------------------------------ | -------------------------------------------- |
| `CAPELRY_BOOTSTRAP_REPOSITORY` | `https://github.com/capelry-ai/capelry-skills` | GitHub source repository                  |
| `CAPELRY_BOOTSTRAP_REF`        | `main`                               | Git ref, branch, tag, or SHA                 |
| `CAPELRY_BOOTSTRAP_PATH`       | auto-detect                          | Skill path inside the repository             |
| `CAPELRY_BOOTSTRAP_TARGET`     | unset                                | Known install target, e.g. `pi-project`      |
| `CAPELRY_BOOTSTRAP_NAME`       | `capelry`                            | Destination directory name under skills dir  |
| `CAPELRY_SKILLS_DIR`           | `.agents/skills`                     | Parent skills directory when no target is set |
| `CAPELRY_USER_AGENT_SUFFIX`    | unset                                | Product/deployment token appended to the default User-Agent |
| `CAPELRY_USER_AGENT`           | unset                                | Full User-Agent override when appending is not enough |

The installed Capelry CLI reads `CAPELRY_REGISTRY_URL` when you want registry operations to use a private, staging, or self-hosted Capelry registry. By default, registry operations use `https://capelry.com`. Registry requests send `capelry-client` as their User-Agent so Capelry.com can attribute client usage; the bootstrap helper sends `capelry-client bootstrap`. Prefer `CAPELRY_USER_AGENT_SUFFIX` for attribution in logs, and avoid personal data.

For Capelry self-update checks from GitHub, the installed CLI also reads `CAPELRY_GITHUB_TOKEN`, `GITHUB_TOKEN`, or `GH_TOKEN` when you need higher API rate limits or private-repository access.

Bash/zsh examples:

```bash
export CAPELRY_BOOTSTRAP_REPOSITORY="https://github.com/capelry-ai/capelry-skills"
export CAPELRY_BOOTSTRAP_TARGET="pi-project"
python3 scripts/bootstrap.py
```

PowerShell examples:

```powershell
$env:CAPELRY_BOOTSTRAP_REPOSITORY = "https://github.com/capelry-ai/capelry-skills"
$env:CAPELRY_BOOTSTRAP_TARGET = "pi-project"
py .\scripts\bootstrap.py
```

Windows `cmd.exe` examples:

```bat
set CAPELRY_BOOTSTRAP_REPOSITORY=https://github.com/capelry-ai/capelry-skills
set CAPELRY_BOOTSTRAP_TARGET=pi-project
py scripts\bootstrap.py
```

## Install target guidance

Prefer project scope unless the user explicitly requests a global install. Use a native target for one harness; use `agents-project` for a shared repository only when every intended harness documents `.agents/skills` discovery.

| Harness | Project path / target | Global path / target | Confirm after install |
| --- | --- | --- | --- |
| Portable Agent Skills | `.agents/skills/capelry` / `agents-project` | `~/.agents/skills/capelry` / `agents-global` | Reload/restart and check the harness's skill list. |
| Claude Code | `.claude/skills/capelry` / `claude-project` | `~/.claude/skills/capelry` / `claude-global` | Invoke `/capelry`; restart only if the top-level skills directory was created after startup. |
| OpenAI Codex | `.agents/skills/capelry` / `codex-project` | `~/.agents/skills/capelry` / `codex-global` | Use `/skills` or `$capelry`; restart only if absent. |
| Pi | `.pi/skills/capelry` / `pi-project` | `~/.pi/agent/skills/capelry` / `pi-global` | Run `/reload`, then `/skill:capelry`. |
| OpenCode | `.opencode/skills/capelry` / `opencode-project` | `~/.config/opencode/skills/capelry` / `opencode-global` | Confirm the `skill` tool lists it and permissions allow it. |
| Gemini CLI | `.gemini/skills/capelry` / `gemini-project` | `~/.gemini/skills/capelry` / `gemini-global` | Run `/skills reload`, then `/skills list`. |
| Cursor | `.cursor/skills/capelry` / `cursor-project` | `~/.cursor/skills/capelry` / `cursor-global` | Open **Customize > Skills** or invoke `/capelry`. |
| Windsurf Cascade | `.windsurf/skills/capelry` / `windsurf-project` | `~/.codeium/windsurf/skills/capelry` / `windsurf-global` | Invoke `@capelry`; reopen Cascade if absent. |
| GitHub Copilot / VS Code | `.github/skills/capelry` / `copilot-project` | `~/.copilot/skills/capelry` / `copilot-global` | In Copilot CLI run `/skills reload` and `/skills info capelry`. |
| Cline | `.cline/skills/capelry` / `cline-project` | `~/.cline/skills/capelry` / `cline-global` | Enable it in the Skills menu or invoke `/capelry`. |
| Roo Code | `.roo/skills/capelry` / `roo-project` | `~/.roo/skills/capelry` / `roo-global` | Confirm it is available in the current mode. |
| JetBrains Junie | `.junie/skills/capelry` / `junie-project` | `~/.junie/skills/capelry` / `junie-global` | Invoke `/capelry` or `$capelry`. |
| Kiro | `.kiro/skills/capelry` / `kiro-project` | `~/.kiro/skills/capelry` / `kiro-global` | Restart if needed; custom agents need a `skill://` resource. |
| Factory Droid | `.factory/skills/capelry` / `factory-project` | `~/.factory/skills/capelry` / `factory-global` | Start a new Droid session if absent, then invoke `/capelry`. |

The installed CLI's `targets` command is the machine-readable source of truth. The evidence-backed matrix, portability caveats, and official documentation links are bundled at `references/harnesses.md`.

For agents without a documented native skill loader, do not claim automatic discovery. Add or paste `SKILL.md` as explicit project instructions and tell the agent to use `scripts/capelry.py` directly.

## Local source checkout sync

If you are developing from this repository and want an installed skill to include unreleased local changes, use `sync-install` instead of manual copy commands. It validates the local skill, replaces the destination, and keeps a `.zip` archive backup by default. Do not create persistent backup directories inside agent skill roots because agent harnesses may load them as duplicate skills.

Portable project-local install:

```text
python3 skills/capelry/scripts/capelry.py sync-install --target agents-project --dry-run
python3 skills/capelry/scripts/capelry.py sync-install --target agents-project --yes
```

Pi global install for testing the active Pi skill:

```text
python3 skills/capelry/scripts/capelry.py sync-install --target pi-global --dry-run
python3 skills/capelry/scripts/capelry.py sync-install --target pi-global --yes
```

Use `--dest /absolute/path/to/skills/capelry` for an exact destination. Reload/restart the agent afterward; in Pi, run `/reload` then `/skill:capelry`.

## Use after bootstrap

Run the CLI from the installed skill directory. Replace `<capelry-skill-dir>` with the path you selected, such as `.agents/skills/capelry`, `.pi/skills/capelry`, or `.claude/skills/capelry`.

Check the installed Capelry skill version and latest GitHub `vX.X.X` release/tag:

```text
python3 <capelry-skill-dir>/scripts/capelry.py version
python3 <capelry-skill-dir>/scripts/capelry.py self-update --dry-run
```

Update the Capelry skill itself after user approval:

```text
python3 <capelry-skill-dir>/scripts/capelry.py self-update --yes
```

Search Capelry through ARD:

```text
python3 <capelry-skill-dir>/scripts/capelry.py search "skill creator" --type skill --trust-state source-hosted
```

Explore catalog-aware facet buckets:

```text
python3 <capelry-skill-dir>/scripts/capelry.py explore "skill creator" --field metadata.com.capelry.catalogPath --limit 10
```

List verified harness targets and build a discovery shortlist for the selected target:

```text
python3 <capelry-skill-dir>/scripts/capelry.py targets --json
python3 <capelry-skill-dir>/scripts/capelry.py discover "feature planning skills" --query "feature planning,feature,prd,implementation plan" --top 5 --install-snippet agents-project
```

Inspect one capability before installing:

```text
python3 <capelry-skill-dir>/scripts/capelry.py info capelry-ai/capelry-skills/capelry --install-snippet agents-project
```

Capelry v2.0.6 and later use catalog-aware ARD discovery only. Human refs use `namespace/catalog/resource` slug metadata, so use `info` for each shortlisted slug or URN before installing:

```text
python3 <capelry-skill-dir>/scripts/capelry.py info capelry-ai/capelry-skills/capelry --install-snippet agents-project
python3 <capelry-skill-dir>/scripts/capelry.py info urn:air:github.com:capelry-ai:capelry-skills:capelry --install-snippet agents-project
```

Install a skill into the portable project location:

```text
python3 <capelry-skill-dir>/scripts/capelry.py install capelry-ai/capelry-skills/capelry --target agents-project
```

Install into Pi project skills instead:

```text
python3 <capelry-skill-dir>/scripts/capelry.py install capelry-ai/capelry-skills/capelry --target pi-project
```

Install every supported skill from a catalog, with a dry run first. Replace `agents-project` with the active harness target when needed:

```text
python3 <capelry-skill-dir>/scripts/capelry.py install-catalog y30k/ai-capabilities --target agents-project --dry-run
python3 <capelry-skill-dir>/scripts/capelry.py install-catalog y30k/ai-capabilities --target agents-project --force --yes
```

PowerShell examples:

```powershell
py <capelry-skill-dir>/scripts/capelry.py search "skill creator"
py <capelry-skill-dir>/scripts/capelry.py install capelry-ai/capelry-skills/capelry --target pi-project
```

## Manual install fallback

1. Download the source archive from `https://github.com/capelry-ai/capelry-skills/archive/refs/heads/main.zip`.
2. Extract the Capelry skill directory. The bootstrap script auto-detects `skills/capelry` and `.pi/skills/capelry`; use whichever exists in the archive.
3. Copy it so `SKILL.md` lands under the active harness path in the install target table above, in a directory named exactly `capelry`.
4. Run `python3 <installed-path>/scripts/capelry.py validate-skill <installed-path>`.
5. Follow the harness-specific confirmation step from the table.

## Agent prompt fallback

If a tool has no skill installer but can read files, paste this instruction:

```text
Install the Capelry skill from https://github.com/capelry-ai/capelry-skills into this project as a project-local Agent Skill. Identify this coding harness and use its documented native skill directory from BOOTSTRAP.md; use .agents/skills/capelry only when this harness documents that path. Keep the directory name capelry so it matches SKILL.md. Use source path skills/capelry, validate the installed skill, then follow the harness-specific reload/list step before using it to install capabilities from Capelry.com.
```

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

Run these commands from the root of the project where you want agents to use Capelry. By default, they install into the portable project-local Agent Skills location. If you know the active coding agent has a native project skill directory, choose one of the target options below instead.

```text
python3 -c "import urllib.request; urllib.request.urlretrieve('https://raw.githubusercontent.com/capelry-ai/capelry-skills/main/skills/capelry/scripts/bootstrap.py', 'capelry-bootstrap.py')"
python3 capelry-bootstrap.py
```

For PowerShell, the same commands work. If your Python launcher is `py`, use `py` instead of `python3`:

```powershell
py -c "import urllib.request; urllib.request.urlretrieve('https://raw.githubusercontent.com/capelry-ai/capelry-skills/main/skills/capelry/scripts/bootstrap.py', 'capelry-bootstrap.py')"
py capelry-bootstrap.py
```

The downloaded `capelry-bootstrap.py` script fetches the skill source from `https://github.com/capelry-ai/capelry-skills` and copies only the Capelry skill directory into your project.

Agent note: if you know you are running inside Pi, Claude Code, Codex, or another coding agent with a preferred skill location, use the install target guidance below and pass the matching `--target`. If you are unsure, the default portable target is safe.

To verify the install, run `scripts/capelry.py` from the installed skill directory. `search`, `discover`, `info`, and supported `install` flows use ARD by default. For the default portable target:

```text
python3 .agents/skills/capelry/scripts/capelry.py search skill --type skill
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

If you are reading this inside an extracted Capelry skill package, run the bundled OS-neutral bootstrap script from the skill directory:

```text
python3 scripts/bootstrap.py
```

If you are at a repository root that contains `skills/capelry`, run:

```text
python3 skills/capelry/scripts/bootstrap.py
```

PowerShell equivalents:

```powershell
py .\scripts\bootstrap.py
py .\skills\capelry\scripts\bootstrap.py
```

Useful options:

```text
python3 scripts/bootstrap.py --repo https://github.com/capelry-ai/capelry-skills --ref main --target agents-project
python3 scripts/bootstrap.py --repo https://github.com/capelry-ai/capelry-skills --ref vX.Y.Z --target agents-project  # example published release tag
python3 scripts/bootstrap.py --target pi-project
python3 scripts/bootstrap.py --target claude-project
python3 scripts/bootstrap.py --target codex-project
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

The installed Capelry CLI reads `CAPELRY_REGISTRY_URL` when you want registry operations to use a private, staging, or self-hosted Capelry registry. By default, registry operations use `https://capelry.com`.

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

Prefer project-local installs unless the user asks for global installation. If the active coding agent already has a native skill location, use it. If you are unsure, use the portable default: `.agents/skills/capelry`.

| Coding agent / use case | Recommended project-local path | Bootstrap option | After install |
| ----------------------- | ------------------------------ | ---------------- | ------------- |
| Portable Agent Skills / unsure | `.agents/skills/capelry` | `--target agents-project` or no option | Tell the agent to read `.agents/skills/capelry/SKILL.md` if it does not auto-load skills. |
| Pi | `.pi/skills/capelry` | `--target pi-project` | Run `/reload`, then `/skill:capelry`. |
| Claude Code | `.claude/skills/capelry` | `--target claude-project` | Restart Claude Code; if needed, point it at `.claude/skills/capelry/SKILL.md`. |
| OpenAI Codex | `.agents/skills/capelry` or `.codex/skills/capelry` if configured | `--target agents-project` or `--target codex-project` | Restart the Codex session; if needed, point it at the installed `SKILL.md`. |
| Cursor | `.agents/skills/capelry` | `--target agents-project` | Reference `.agents/skills/capelry/SKILL.md` from project rules/instructions or chat. |
| Windsurf | `.agents/skills/capelry` | `--target agents-project` | Reference `.agents/skills/capelry/SKILL.md` from project rules/instructions or chat. |
| GitHub Copilot | `.agents/skills/capelry` | `--target agents-project` | Add a project instruction pointing Copilot at `.agents/skills/capelry/SKILL.md`. |
| Cline / Roo Code | `.agents/skills/capelry` | `--target agents-project` | Add the installed `SKILL.md` to project rules/instructions. |

Global targets are available when explicitly requested:

| Target option | Path |
| ------------- | ---- |
| `--target agents-global` | `~/.agents/skills/capelry` |
| `--target pi-global` | `~/.pi/agent/skills/capelry` |
| `--target claude-global` | `~/.claude/skills/capelry` |
| `--target codex-global` | `~/.codex/skills/capelry` |

For agents that do not have a native skill loader, add or paste `SKILL.md` as project instructions and tell the agent to use `scripts/capelry.py` for registry operations.

## Local source checkout fallback

If you are developing from this repository and want to copy the source skill directly into a portable project location:

```text
python3 -c "import shutil, pathlib; dst=pathlib.Path('.agents/skills/capelry'); shutil.rmtree(dst, ignore_errors=True); shutil.copytree(pathlib.Path('skills/capelry'), dst)"
```

PowerShell with `py`:

```powershell
py -c "import shutil, pathlib; dst=pathlib.Path('.agents/skills/capelry'); shutil.rmtree(dst, ignore_errors=True); shutil.copytree(pathlib.Path('skills/capelry'), dst)"
```

For Pi-only development in this repository, you can copy to `.pi/skills/capelry` instead and run `/reload` in Pi.

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

Build a discovery shortlist for a task:

```text
python3 <capelry-skill-dir>/scripts/capelry.py discover "feature planning skills" --query "feature planning,feature,prd,implementation plan" --top 5 --install-snippet pi-project
```

Inspect one capability before installing:

```text
python3 <capelry-skill-dir>/scripts/capelry.py info capelry-ai/capelry-skills/capelry --install-snippet pi-project
```

Capelry v2.0.6 and later use catalog-aware ARD discovery only. Human refs use `namespace/catalog/resource` slug metadata, so use `info` for each shortlisted slug or URN before installing:

```text
python3 <capelry-skill-dir>/scripts/capelry.py info capelry-ai/capelry-skills/capelry --install-snippet pi-project
python3 <capelry-skill-dir>/scripts/capelry.py info urn:ai:github.com:capelry-ai:capelry-skills:skills:capelry --install-snippet pi-project
```

Install a skill into the portable project location:

```text
python3 <capelry-skill-dir>/scripts/capelry.py install capelry-ai/capelry-skills/capelry --target agents-project
```

Install into Pi project skills instead:

```text
python3 <capelry-skill-dir>/scripts/capelry.py install capelry-ai/capelry-skills/capelry --target pi-project
```

PowerShell examples:

```powershell
py <capelry-skill-dir>/scripts/capelry.py search "skill creator"
py <capelry-skill-dir>/scripts/capelry.py install capelry-ai/capelry-skills/capelry --target pi-project
```

## Manual install fallback

1. Download the source archive from `https://github.com/capelry-ai/capelry-skills/archive/refs/heads/main.zip`.
2. Extract the Capelry skill directory. The bootstrap script auto-detects `skills/capelry` and `.pi/skills/capelry`; use whichever exists in the archive.
3. Copy it so `SKILL.md` lands at one of these paths:
   - `.agents/skills/capelry/SKILL.md`
   - `.pi/skills/capelry/SKILL.md`
   - `.claude/skills/capelry/SKILL.md`
   - `~/.agents/skills/capelry/SKILL.md`
4. Reload or restart your agent.

## Agent prompt fallback

If a tool has no skill installer but can read files, paste this instruction:

```text
Install the Capelry skill from https://github.com/capelry-ai/capelry-skills into this project as a project-local Agent Skill. Choose the best project-local skill directory for this coding agent; if unsure, use the portable Agent Skills default at .agents/skills/capelry/SKILL.md. Use the source path skills/capelry; if that path is not present, try .pi/skills/capelry. Then use it to search and install capabilities from Capelry.com.
```

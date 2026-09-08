# Capelry Bootstrap

Use this standalone entry point to install the `capelry` skill into a fresh project. Bootstrap downloads Capelry from GitHub source, not Capelry.com:

```text
https://github.com/capelry-ai/capelry-skills
```

After installation, the skill uses `https://capelry.com` for registry operations.

## Requirements

- Python 3.9+ on Linux, macOS, or Windows.
- No bash, curl, unzip, Node.js, npm, or package manager.
- Use `python3` below; substitute the local Python 3 launcher, such as `py` on Windows.

## Agent procedure

1. Work from the destination project's root.
2. Identify the active coding harness and select its project target below. Use global scope only when the user explicitly requests it. Use `agents-project` only for a harness that documents `.agents/skills` discovery.

| Harness | Project target/path | Global target/path |
| --- | --- | --- |
| Portable Agent Skills | `agents-project` — `.agents/skills` | `agents-global` — `~/.agents/skills` |
| Claude Code | `claude-project` — `.claude/skills` | `claude-global` — `~/.claude/skills` |
| OpenAI Codex | `codex-project` — `.agents/skills` | `codex-global` — `~/.agents/skills` |
| Pi | `pi-project` — `.pi/skills` | `pi-global` — `~/.pi/agent/skills` |
| OpenCode | `opencode-project` — `.opencode/skills` | `opencode-global` — `~/.config/opencode/skills` |
| Gemini CLI | `gemini-project` — `.gemini/skills` | `gemini-global` — `~/.gemini/skills` |
| Cursor | `cursor-project` — `.cursor/skills` | `cursor-global` — `~/.cursor/skills` |
| Windsurf | `windsurf-project` — `.windsurf/skills` | `windsurf-global` — `~/.codeium/windsurf/skills` |
| GitHub Copilot / VS Code | `copilot-project` — `.github/skills` | `copilot-global` — `~/.copilot/skills` |
| Cline | `cline-project` — `.cline/skills` | `cline-global` — `~/.cline/skills` |
| Roo Code | `roo-project` — `.roo/skills` | `roo-global` — `~/.roo/skills` |
| JetBrains Junie | `junie-project` — `.junie/skills` | `junie-global` — `~/.junie/skills` |
| Kiro | `kiro-project` — `.kiro/skills` | `kiro-global` — `~/.kiro/skills` |
| Factory Droid | `factory-project` — `.factory/skills` | `factory-global` — `~/.factory/skills` |

3. If the destination exists, inspect its version and do not replace it without approval. Initial commands use `--no-replace` to fail closed.
4. Download the OS-neutral helper, run it with the selected target, then remove it:

```text
python3 -c "import urllib.request; urllib.request.urlretrieve('https://raw.githubusercontent.com/capelry-ai/capelry-skills/main/skills/capelry/scripts/bootstrap.py', 'capelry-bootstrap.py')"
python3 capelry-bootstrap.py --target TARGET --no-replace
python3 -c "from pathlib import Path; Path('capelry-bootstrap.py').unlink(missing_ok=True)"
```

PowerShell with `py` uses the same arguments:

```powershell
py -c "import urllib.request; urllib.request.urlretrieve('https://raw.githubusercontent.com/capelry-ai/capelry-skills/main/skills/capelry/scripts/bootstrap.py', 'capelry-bootstrap.py')"
py capelry-bootstrap.py --target TARGET --no-replace
py -c "from pathlib import Path; Path('capelry-bootstrap.py').unlink(missing_ok=True)"
```

If replacement was approved, rerun the helper without `--no-replace` before deleting it.

If the helper already exists in a checkout/package, skip downloading the helper and run it directly. Bootstrap still downloads GitHub source at the selected ref; use the installed CLI's `sync-install` for unreleased local content.

```text
python3 skills/capelry/scripts/bootstrap.py --target TARGET --no-replace
# From inside an extracted skills/capelry directory:
python3 scripts/bootstrap.py --target TARGET --no-replace
```

5. Verify the installed package without contacting the registry. Replace `<installed-capelry>` with the resulting path:

```text
python3 <installed-capelry>/scripts/capelry.py validate-skill <installed-capelry>
python3 <installed-capelry>/scripts/capelry.py targets --harness TARGET
python3 <installed-capelry>/scripts/capelry.py --help
```

6. Follow the helper's printed `Next:` instruction to reload/list the skill. Filesystem installation alone does not prove that the harness discovered it. For Pi, run `/reload`, then `/skill:capelry`.

## Invocation options

Apply these options to the helper invocation before deleting it:

```text
python3 capelry-bootstrap.py --target pi-project --no-replace
python3 capelry-bootstrap.py --target claude-project --no-replace
python3 capelry-bootstrap.py --target codex-project --no-replace
python3 capelry-bootstrap.py --ref vX.Y.Z --target agents-project --no-replace
python3 capelry-bootstrap.py --source-path skills/capelry --target TARGET --no-replace
python3 capelry-bootstrap.py --skills-dir .custom/skills --no-replace
python3 capelry-bootstrap.py --dest /absolute/path/to/skills/capelry --no-replace
python3 capelry-bootstrap.py --help
```

The default source ref is `main`; use a published `vX.Y.Z` when reproducibility matters.

Optional environment variables:

| Variable | Default | Purpose |
| --- | --- | --- |
| `CAPELRY_BOOTSTRAP_REPOSITORY` | Capelry GitHub repository | Alternate GitHub source |
| `CAPELRY_BOOTSTRAP_REF` | `main` | Branch, tag, or SHA |
| `CAPELRY_BOOTSTRAP_PATH` | auto-detect | Skill path in the repository |
| `CAPELRY_BOOTSTRAP_TARGET` | unset | Install target |
| `CAPELRY_BOOTSTRAP_NAME` | `capelry` | Destination directory name |
| `CAPELRY_SKILLS_DIR` | `.agents/skills` | Parent directory without a target |
| `CAPELRY_HTTP_TIMEOUT` | `30` | Per-network-operation timeout, 1–300 seconds |
| `CAPELRY_USER_AGENT_SUFFIX` | unset | Non-personal product/deployment identifier |
| `CAPELRY_USER_AGENT` | unset | Full User-Agent override |

The helper sends `User-Agent: capelry-client bootstrap`. Do not include personal data.

## Manual fallback

If the helper cannot run:

1. Download `https://github.com/capelry-ai/capelry-skills/archive/refs/heads/main.zip`.
2. Extract `skills/capelry`.
3. Copy it to the selected path as a directory named `capelry`.
4. Run the three local verification/activation steps above.

Do not bootstrap from Capelry.com, install globally without a request, or overwrite an existing installation without approval.

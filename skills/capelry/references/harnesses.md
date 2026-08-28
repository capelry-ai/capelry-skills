# Verified coding-harness install matrix

Reviewed against official documentation on 2026-08-27. This is the source of truth for choosing Capelry `--target` values. Harness behavior changes quickly; re-check the linked source before changing a path.

## Portable package contract

Capelry installs a strict portable core from the [Agent Skills specification](https://agentskills.io/specification):

- A skill is a directory containing a UTF-8 file named exactly `SKILL.md`.
- YAML frontmatter requires `name` and `description`.
- `name` is 1-64 lowercase letters, digits, and single hyphens; it must match the parent directory.
- `description` is 1-1024 characters and explains both what the skill does and when to use it.
- Portable optional fields are `license`, `compatibility` (1-500 characters), `metadata` (string map), and experimental `allowed-tools`.
- Scripts, references, and assets may live beside `SKILL.md`; instructions should reference them relative to the skill root.

The specification defines package contents, not install locations. Each harness defines its own discovery roots. `.agents/skills` is a documented cross-client convention, but it is not universal.

## Supported targets

| Harness | Project path / Capelry target | Global path / Capelry target | Portable `.agents/skills` | Confirm after install |
| --- | --- | --- | --- | --- |
| Portable Agent Skills | `.agents/skills` / `agents-project` | `~/.agents/skills` / `agents-global` | Native convention | Use the active harness's list/reload command. |
| Claude Code | `.claude/skills` / `claude-project` | `~/.claude/skills` / `claude-global` | **Not documented** | Invoke `/<name>`. Changes are watched, but restart if the top-level skills directory was created after startup. |
| OpenAI Codex | `.agents/skills` / `codex-project` | `~/.agents/skills` / `codex-global` | Yes; this is Codex's documented path | Use `/skills` or `$<name>`; Codex detects changes, with restart as fallback. Admin scope is `/etc/codex/skills` and is intentionally not an ordinary user target. |
| Pi | `.pi/skills` / `pi-project` | `~/.pi/agent/skills` / `pi-global` | Yes, project and global | Run `/reload`, then `/skill:<name>`. Project skills load only for trusted projects. |
| OpenCode | `.opencode/skills` / `opencode-project` | `~/.config/opencode/skills` / `opencode-global` | Yes; Claude paths also work | Restart if needed and confirm the `skill` tool advertises the name. Check `permission.skill` if hidden. |
| Gemini CLI | `.gemini/skills` / `gemini-project` | `~/.gemini/skills` / `gemini-global` | Yes, project and global | Run `/skills reload`, then `/skills list`. Activation requires consent. |
| Cursor | `.cursor/skills` / `cursor-project` | `~/.cursor/skills` / `cursor-global` | Yes; Claude and Codex paths also work | Open **Customize > Skills** or invoke `/<name>` in Agent chat. User skills do not travel to remote/cloud workers. |
| GitHub Copilot and VS Code | `.github/skills` / `copilot-project` | `~/.copilot/skills` / `copilot-global` | Yes; project Claude path also works | In Copilot CLI run `/skills reload` and `/skills info <name>`. Commit project skills for cloud agents. |
| Windsurf Cascade | `.windsurf/skills` / `windsurf-project` | `~/.codeium/windsurf/skills` / `windsurf-global` | Documented for Devin Desktop, not promised for every Cascade surface | Invoke `@<name>`; reopen Cascade if absent. Use the native target for predictable Cascade loading. |
| Cline | `.cline/skills` / `cline-project` | `~/.cline/skills` / `cline-global` | **Not documented**; project `.claude/skills` is supported | Confirm the skill is enabled in the Skills menu or invoke `/<name>`. |
| Roo Code | `.roo/skills` / `roo-project` | `~/.roo/skills` / `roo-global` | Yes, project and global | Roo watches `SKILL.md`; confirm the current mode exposes the skill. |
| JetBrains Junie | `.junie/skills` / `junie-project` | `~/.junie/skills` / `junie-global` | Yes, project and global | Invoke `/<name>` or `$<name>`; restart if it is not suggested. |
| Kiro | `.kiro/skills` / `kiro-project` | `~/.kiro/skills` / `kiro-global` | **Not documented** | Restart if needed and invoke `/<name>`. Custom agents must include a matching `skill://` resource. |
| Factory Droid | `.factory/skills` / `factory-project` | `~/.factory/skills` / `factory-global` | Yes; `.agent/skills` also works | Start a new Droid session if the skill is not visible, then invoke `/<name>`. |
| OpenHands | `.agents/skills` / `agents-project` | `~/.agents/skills` / `agents-global` | Primary modern path | Start a new conversation and confirm the skill is advertised. |

`codex-project` and `codex-global` intentionally alias `.agents/skills`. `.codex/skills` is **not** a documented Codex discovery root, even though Cursor accepts it as a compatibility location.

Use native targets for Claude Code, Cline, Kiro, and Windsurf Cascade. For repositories intentionally shared among the other documented consumers, `agents-project` is the lowest-duplication choice.

## Why these harnesses

The matrix covers the objective's required Claude Code, Codex, Pi, and OpenCode surfaces, plus widely deployed editor, CLI, cloud-agent, and open-source products with first-party Agent Skills documentation: Gemini CLI, Cursor, GitHub Copilot/VS Code, Windsurf, Cline, Roo Code, Junie, Kiro, Factory, and OpenHands. Other clients listed in the official [Agent Skills client showcase](https://agentskills.io/clients) can use `agents-project` only when their own documentation confirms that discovery path.

Do not invent a native target for a harness that only supports rules, commands, generic context files, or manually pasted prompts. For such a harness, install nowhere automatically: tell the user to provide `SKILL.md` as explicit project instructions and run the bundled Capelry CLI directly.

## Frontmatter portability

A local harness may accept extensions such as Cursor `paths` or Claude Code `disable-model-invocation`, but these are not portable across all clients. Claude skill upload/package flows reject fields outside the six standard fields. Capelry therefore:

1. Requires the portable `name` and `description` contract for every automatic install.
2. Requires the install directory to match `name`.
3. Warns when non-standard fields make the package harness-specific.
4. Stages and validates before replacing an existing install.

Run:

```text
python3 <capelry-skill-dir>/scripts/capelry.py validate-skill path/to/skill
python3 <capelry-skill-dir>/scripts/capelry.py targets --json
```

## Official sources

- Agent Skills specification and client integration: https://agentskills.io/specification and https://agentskills.io/client-implementation/adding-skills-support
- Claude Code: https://code.claude.com/docs/en/skills
- OpenAI Codex: https://developers.openai.com/codex/skills
- Pi: https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/skills.md
- OpenCode: https://opencode.ai/docs/skills/
- Gemini CLI: https://geminicli.com/docs/cli/skills/ and https://geminicli.com/docs/cli/creating-skills/
- Cursor: https://cursor.com/docs/skills
- GitHub Copilot: https://docs.github.com/en/copilot/concepts/agents/about-agent-skills and https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/add-skills
- Windsurf Cascade: https://docs.windsurf.com/windsurf/cascade/skills
- Cline: https://docs.cline.bot/customization/skills
- Roo Code: https://docs.roocode.com/features/skills
- JetBrains Junie: https://junie.jetbrains.com/docs/agent-skills.html
- Kiro: https://kiro.dev/docs/skills/
- Factory Droid: https://docs.factory.ai/harness/skills
- OpenHands: https://docs.openhands.dev/overview/skills

---
name: capelry
description: Find, inspect, compare, validate, and install AI-agent capabilities from Capelry. Use when users ask to discover skills for a task, resolve a Capelry slug or ARD URN, install a capability or catalog, bootstrap or update Capelry, select a coding-harness target, sync a local Capelry checkout, validate an Agent Skills package, or prepare a capability archive for publishing.
license: MIT
metadata:
  registry: "https://capelry.com"
  bootstrap: "BOOTSTRAP.md"
---

# Capelry

Use the bundled stdlib-only CLI instead of reasoning through raw registry payloads. Default registry: `https://capelry.com`; set `CAPELRY_REGISTRY_URL` for a private, staging, or self-hosted registry.

Resolve `<cli>` to this installed skill's `scripts/capelry.py`, independently of the destination project. Resolve linked references from this skill directory. Run project-local install commands from the destination project's root. Use `python3` on Linux/macOS/Pi or a local Python 3 launcher such as `py` on Windows.

## Choose the workflow

| User intent | Workflow |
| --- | --- |
| Find capabilities for a task | Use cost-controlled discovery below |
| Inspect a known slug or URN | Run `info`; summarize its decision signals |
| Install a known capability | Select a target, run `info`, inspect third-party instructions, then `install` |
| Install skills from a catalog | Read [CLI installation guidance](references/cli.md#install); dry-run before confirmation |
| Explore catalogs, types, or trust states | Run `explore`; read [CLI details](references/cli.md) for advanced filters |
| Select an install target | Run `targets --harness <name>`; read the [verified harness matrix](references/harnesses.md) |
| Validate an Agent Skills package | Run `validate-skill path/to/skill` |
| Bootstrap a fresh project | Read and follow `BOOTSTRAP.md` |
| Check, update, or sync Capelry | Read [maintenance guidance](references/maintenance.md); updates require approval |
| Package or publish a capability | Read [packaging guidance](references/maintenance.md#package-another-capability) |

## Select the target

Default to project-local scope unless the user explicitly requests global installation. Identify the active harness and pass its explicit target:

```text
python3 <cli> targets --harness <name>
python3 <cli> targets --scope project --json
```

Use `.agents/skills` only for harnesses that document it. Follow the successful command's `next` instruction and distinguish “files installed” from “the harness confirmed the skill is visible.” Keep `discover` and `bulk-info` target-neutral unless a target was selected.

## Cost-controlled discovery

For “find me a skill for X,” use one bounded operation rather than LLM-generated search loops:

```text
python3 <cli> discover "the user's task" --top 3 --max-queries 4 --search-limit 10 --type skill --trust-state source-hosted --install-snippet <active-target>
```

Defaults are at most 4 search requests × 10 results. The CLI preserves meaningful punctuation and Unicode, removes standalone generic words, expands related terms, deduplicates results, ranks by the best observed registry score, and reports the request/candidate budget.

1. Run `discover` once. Prefer concise text; use `--json` for automation or exact field extraction.
2. Return at most 3–5 candidates; never paste raw registry payloads.
3. Inspect only the best 1–3 third-party candidates in one command:

```text
python3 <cli> bulk-info namespace/catalog/one namespace/catalog/two --install-snippet <active-target>
```

4. Compare task fit, media type, source, catalog, trust identity/provenance, checksum, and install target. Mark missing evidence explicitly. `source-hosted` describes provenance; it is not a safety endorsement.
5. Install only after confirmation unless the user requested that exact known capability.

If results are empty or unsuitable, inspect the emitted queries and retry once with a task-specific `--query` or a larger bounded budget. Preserve requested source/trust filters. If no suitable result remains, say so instead of recommending a weak match. Use `--no-expand` for one precise request.

## Known capability fast path

Use three-part slugs (`namespace/catalog/resource`) or ARD URNs such as `urn:air:...`; do not introduce old two-segment refs.

```text
python3 <cli> info namespace/catalog/resource --install-snippet <active-target>
python3 <cli> install namespace/catalog/resource --target <active-target>
```

`info` resolves exact refs through `/agents`. Normally inspect no more than three refs with `bulk-info`.

## Install and validate

The installer supports:

- `application/vnd.capelry.skill+zip`: verifies SHA-256 metadata when present and rejects unsafe archive paths.
- `application/vnd.capelry.skill-source+json`: installs a pinned archive or supported GitHub source descriptor and verifies a declared source-archive checksum.

It stages on the destination filesystem, validates UTF-8 Agent Skills frontmatter and the name/directory match, then replaces transactionally. Existing installs remain intact after download, extraction, checksum, or validation failure. Unsupported media types receive manual open/connect guidance.

Validate without installing:

```text
python3 <cli> validate-skill path/to/skill
python3 <cli> validate-skill path/to/skill --json
```

For catalog installs, read [the CLI install section](references/cli.md#install), dry-run, review every destination/replacement, and obtain confirmation before the writing command.

## Maintenance and bootstrap

- Fresh project: follow `BOOTSTRAP.md`; acquisition comes from GitHub, not Capelry.com.
- Version check: `python3 <cli> version --check`.
- Self-update: read [maintenance guidance](references/maintenance.md#version-and-self-update), show a dry run, and update only after user approval.
- Source checkout: use Git; use `sync-install` only when a maintainer requests unreleased local content in an installed target.
- Advanced ARD/search details: read [the CLI reference](references/cli.md) only when needed.

## Network identity

Registry requests use `User-Agent: capelry-client` and a per-operation 30-second timeout. Set `CAPELRY_HTTP_TIMEOUT` to 1–300 seconds when needed. Prefer `CAPELRY_USER_AGENT_SUFFIX` for a non-personal product/deployment identifier; use `CAPELRY_USER_AGENT` only for a full override.

## Safety rules

- Treat third-party skills as executable instructions; inspect `SKILL.md` and bundled scripts before running them.
- Follow search → inspect → compare → install.
- Default to project-local installs for experiments; require an explicit request for global scope.
- Do not run newly installed scripts unless requested or clearly required by inspected documentation.
- Preserve exact versions and checksums when reproducibility matters.
- Never self-update in the background or without approval.

# Capelry CLI reference

Read this file for advanced CLI flags, catalog installation, ARD field mapping, or direct API integration. The normal discovery and single-capability install workflow is in `../SKILL.md`.

## Contents

- [ARD hierarchy](#ard-hierarchy)
- [Search and discovery](#search-and-discovery)
- [Supported filters](#supported-filters)
- [Explore](#explore)
- [Inspect](#inspect)
- [Install](#install)
- [Direct ARD contracts](#direct-ard-contracts)

## ARD hierarchy

```text
Namespace page: /c/{namespace}
Catalog page:   /c/{namespace}/{catalog}
Resource page:  /c/{namespace}/{catalog}/{resource}
ARD slug:       namespace/catalog/resource
Catalog path:   namespace/catalog
```

Exact slug resolution uses `metadata.com.capelry.slug`; catalog scoping uses `metadata.com.capelry.catalogPath`.

## Search and discovery

Use `discover` for an agent-facing shortlist:

```text
python3 <cli> discover "feature planning" --top 3 --max-queries 4 --search-limit 10 --type skill --trust-state source-hosted --install-snippet agents-project
```

Cost controls:

- `--max-queries`: maximum search requests; default 4, hard cap 10.
- `--search-limit`: results requested per discovery query; default 10, API cap 100.
- `--top`: shortlist length; default 3, cap 25.
- `--no-expand`: use only the compact user query and explicit `--query` values; compaction removes standalone generic words without discarding punctuation or Unicode.
- `--query`: add intentional terms; repeat or comma-separate. Explicit terms are prioritized inside the query budget.

The command reports `requestCount`, `perRequestLimit`, and `candidateEnvelope` in JSON and prints the queries/budget in text mode, including when no results match. Duplicate identifiers keep their first payload, best numeric registry score, and unique matched-query list.

If the first shortlist is empty or unsuitable, inspect those queries and retry once with a task-specific `--query` or a larger bounded budget. Keep the original source/trust constraints. Report no suitable match after that retry rather than weakening the selection standard.

Use `search` for a precise low-level query:

```text
python3 <cli> search "pdf" --type skill --trust-state source-hosted --limit 10
python3 <cli> search "deployment" --expand --max-queries 4 --json
```

`--expand` is opt-in for `search`; expansion obeys `--max-queries`.

## Supported filters

- `--type skill`: maps a package type to supported ARD media types.
- `--media-type application/vnd.capelry.skill-source+json`: exact media type; repeat or comma-separate.
- `--publisher github.com`: ARD publisher.
- `--trust-state source-hosted`: `metadata.com.capelry.trustState`.
- `--source owner/repo`: GitHub `metadata.com.capelry.sourceRepositoryFullName`.
- `--source https://github.com/owner/repo`: exact `metadata.com.capelry.sourceRepository`.
- `--catalog namespace/catalog`: `metadata.com.capelry.catalogPath`.
- `--catalog-slug repo`: `metadata.com.capelry.catalogSlug`.
- `--catalog-url URL`: `metadata.com.capelry.catalogUrl`.
- `--slug namespace/catalog/resource`: exact slug.
- `--filter FIELD=VALUE`: generic supported ARD filter; repeat as needed.

Public generic fields include `identifier`, `type`, `publisher`, `tags`, `capabilities`, `version`, `updatedAt`, `trustManifest.identityType`, `trustManifest.attestations.type`, and Capelry metadata fields for package type, trust state, slug, catalog, and source repository.

Compatibility flags `--status`, `--domain`, and `--phase` are accepted but not sent because public ARD routes do not expose them.

## Explore

Use one facet query to narrow a broad search:

```text
python3 <cli> explore "production readiness" --field metadata.com.capelry.catalogPath --field type --limit 10
python3 <cli> explore --catalog capelry-ai/capelry-skills --json
```

Default facets cover type, package type, trust state, catalog path, and source repository.

## Inspect

```text
python3 <cli> info namespace/catalog/resource --install-snippet agents-project
python3 <cli> info urn:air:github.com:org:repo:skill --json
python3 <cli> bulk-info namespace/catalog/one namespace/catalog/two --install-snippet agents-project
```

`bulk-info` accepts at most 25 refs. Keep agent-driven comparisons to 1–3 finalists. Detail summaries include media type, source path/ref, catalog, trust state and identity, provenance, checksum when present, page, and install command.

## Install

```text
python3 <cli> install namespace/catalog/resource --target agents-project
python3 <cli> install-catalog namespace/catalog --target agents-project --dry-run
python3 <cli> install-catalog namespace/catalog --target agents-project --force --yes
```

The installer prints trust/provenance before writing. For a catalog, always dry-run first, review every destination and proposed replacement, then obtain confirmation. Use `--force` only when replacement was approved and `--yes` only after reviewing the non-interactive plan. `--keep-going` records individual entry failures and continues with later entries; it does not turn an initial catalog lookup failure into success.

Automatic media types:

- `application/vnd.capelry.skill+zip`
- `application/vnd.capelry.skill-source+json`

Other media types return manual open/connect guidance.

## Direct ARD contracts

Search:

```text
POST {CAPELRY_REGISTRY_URL}/search
{"query":{"text":"query","filter":{"type":["application/vnd.capelry.skill-source+json"]}},"federation":"none","pageSize":10}
```

Explore:

```text
POST {CAPELRY_REGISTRY_URL}/explore
{"query":{"text":"query"},"resultType":{"facets":[{"field":"metadata.com.capelry.catalogPath","limit":10}]}}
```

Inspect exact refs:

```text
GET {CAPELRY_REGISTRY_URL}/agents?filter=identifier%20%3D%20'urn%3Aair%3A...'
GET {CAPELRY_REGISTRY_URL}/agents?filter=metadata.com.capelry.slug%20%3D%20'namespace%2Fcatalog%2Fresource'
```

Prefer the CLI because it handles quoting, error shapes, safe install paths, checksums, concise output, and bounded network waits. Each network operation times out after 30 seconds by default; this is not a whole-command deadline. Set `CAPELRY_HTTP_TIMEOUT` to an integer from 1 to 300 when a different limit is required.

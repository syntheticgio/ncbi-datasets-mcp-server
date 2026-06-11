# Design: `list_data_types` tool

**Date:** 2026-06-10
**Branch:** `feature/list-data-types`

## Goal

Let a user ask "what kind of data can I get from NCBI Datasets?" and receive a
comprehensive, readable report from the MCP server describing the data report
schema types NCBI Datasets provides — with a path to the existing tools that
actually fetch that data.

## Background

NCBI Datasets packages metadata as **data report schemas**
(https://www.ncbi.nlm.nih.gov/datasets/docs/v2/reference-docs/data-reports/).
The docs index names 11 schema types:

1. Gene report — gene record metadata
2. Gene product report — gene identifiers, genomic locations, transcripts, products
3. Genome assembly report — accession, organism, assembly statistics, annotation info
4. Genome sequence report — sequence accessions, chromosome, length
5. MicroBIGG-E report — accession, organism, location, biosample information
6. Prokaryote gene report — gene identifiers, protein info, taxonomic scope
7. Prokaryote gene location report — identifiers, organism, genomic locations
8. Taxonomy report — general information about a taxonomic identifier
9. Taxonomy names report — names associated with a taxonomic identifier
10. Virus report — virus record metadata
11. Virus annotation report — identifiers, sample info, genomic locations, products

## Decisions (from brainstorming)

- **Data source:** Static curated catalog stored in the repo (offline, fast,
  testable). Each entry includes a live docs URL for the authoritative schema.
- **Interface:** A single new tool, `list_data_types`.
- **Granularity:** Single overview by default; optional `report_type` argument
  drills into one type's full field categories.
- **Tool mapping:** Each entry cross-references which existing server tools
  produce that data; types with no current tool are marked not-yet-supported.

## Architecture

Follows the existing domain pattern. The catalog is static data — no REST/CLI.

- **New module `src/ncbi_datasets_mcp/domains/catalog.py`**
  - Holds the curated catalog as a structured Python object (a list of
    `DataReportType` dataclasses).
  - `overview() -> dict` — renders all 11 types.
  - `describe(report_type: str) -> dict` — renders one type in full, or returns
    an error dict with available types if the key is unknown.
  - Keeps rendering here so `server.py` stays registration-only (matches the
    current convention).

- **New tool in `server.py`: `list_data_types(report_type: str | None = None)`**
  - Thin wrapper, same try/except shape as the other tools.
  - `report_type=None` → `catalog.overview()`.
  - `report_type="genome-assembly"` → `catalog.describe(...)`.

### Catalog entry shape

Each of the 11 entries (`DataReportType`) has:

- `key` — stable slug (e.g. `genome-assembly`)
- `title` — display name
- `summary` — one-line description (from the official NCBI index)
- `field_categories` — list of the main field groups (e.g. genome assembly →
  accession & identifiers; organism/taxonomy; assembly statistics; annotation
  info; submission / BioProject / BioSample)
- `docs_url` — link to the authoritative schema page
- `produced_by` — list of existing server tool names that return this data, or
  empty list meaning "not yet supported in this server"

### Tool → report-type mapping (initial)

- `genome-assembly` → `genome_summary_by_taxon`, `genome_summary_by_accession`
- `genome-sequence` → `genome_summary_by_taxon`, `genome_summary_by_accession`
  (sequence-level fields available in the downloaded package /
  `dataformat_genome_tsv`)
- `taxonomy` → `taxonomy_summary`
- `taxonomy-names` → `taxonomy_summary`
- All others (gene, gene-product, MicroBIGG-E, prokaryote-gene,
  prokaryote-gene-location, virus, virus-annotation) → `[]` (not yet supported)

## Output shape

Returns a structured `dict` (consistent with the other summary tools):

- `report` — a human-readable rendered string (Markdown-ish), so Claude can
  present it directly.
- `data_types` — the structured catalog (list of entries) so Claude can filter
  or reformat.

Overview lists each type with its summary + producing tools. Detail
(`report_type` given) adds `field_categories` and `docs_url` for that one type.

## Error handling

No network or filesystem access, so the only failure mode is a bad argument.

- Unknown `report_type` → `{"error": ..., "available_types": [...]}` listing
  valid keys.
- Loose matching: a bare `"genome"` returns an error that suggests
  `genome-assembly` and `genome-sequence` (does not silently pick one).

## Testing

Pure functions, fully deterministic. `tests/unit/test_domains_catalog.py`:

1. `overview()` includes all 11 types.
2. `describe()` for a known type returns its `field_categories` and `docs_url`.
3. Unknown type returns the error with `available_types`.
4. Loose `"genome"` returns suggestions for both genome types.
5. Every entry's `produced_by` tool names actually exist as registered tools in
   `server.py` (guards against the mapping drifting out of sync).

## Docs

- Add `list_data_types` to the README tool table and a short "Discovering
  available data" note communicating the server can describe what data NCBI
  Datasets provides.
- Add a CHANGELOG entry.

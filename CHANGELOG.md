# Changelog

All notable changes to this project will be documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

## [0.1.0] — Initial release

### Added
- `ensure_cli` tool: detect and auto-install `datasets`/`dataformat` binaries from NCBI FTP
- `genome_summary_by_taxon`: search genome assemblies by organism name or tax ID (REST)
- `genome_summary_by_accession`: fetch metadata for known accessions (REST)
- `genome_download_by_taxon`: download genome packages by taxon (CLI)
- `genome_download_by_accession`: download genome packages by accession (CLI)
- `rehydrate_genome_package`: fetch sequence files for dehydrated packages (CLI)
- `dataformat_genome_tsv`: convert genome JSONL data reports to TSV (CLI)
- `taxonomy_summary`: get lineage, rank, and names for a taxon (REST)
- `taxonomy_download`: download taxonomy packages (CLI)
- Desktop Extension manifest (`.mcpb`) with `NCBI_AUTO_INSTALL=true` default
- `scripts/gen_enums.py` to regenerate enums from the live NCBI OpenAPI spec
- `scripts/build_mcpb.py` to produce a distributable `.mcpb` bundle
- GitHub Actions CI: lint, unit test matrix (Python 3.10–3.12), nightly integration tests, PyPI trusted publish on tag

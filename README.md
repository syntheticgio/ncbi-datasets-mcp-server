# ncbi-datasets-mcp
NOTE: This is not affiliated with NCBI or NCBI Datasets, this is a user provided tool.

An MCP server that gives Claude access to [NCBI Datasets v2](https://www.ncbi.nlm.nih.gov/datasets/docs/v2/) — discover what data NCBI Datasets offers, search genome assembly metadata, retrieve taxonomy records, and download data packages without leaving your conversation.

## Tools

| Tool | Transport | Description |
|------|-----------|-------------|
| `ensure_cli` | — | Install the NCBI CLI tools (run once, or set `NCBI_AUTO_INSTALL=true`) |
| `list_data_types` | — | Describe what kinds of data NCBI Datasets provides; optional per-type detail |
| `genome_summary_by_taxon` | REST | Search genome assemblies by organism name or tax ID |
| `genome_summary_by_accession` | REST | Fetch assembly metadata for known accessions |
| `genome_download_by_taxon` | CLI | Download a genome package by taxon |
| `genome_download_by_accession` | CLI | Download a genome package by accession |
| `rehydrate_genome_package` | CLI | Fetch sequence files for a dehydrated package |
| `dataformat_genome_tsv` | CLI | Convert a genome JSONL data report to TSV |
| `taxonomy_summary` | REST | Get lineage, rank, and names for a taxon |
| `taxonomy_download` | CLI | Download a taxonomy package |

### Discovering available data

Not sure what NCBI Datasets offers? Ask "what kind of data can I get from
datasets?" and the server's `list_data_types` tool returns a readable catalog of
every data report type — genes, genome assemblies, genome sequences, taxonomy,
viruses, and more — along with which tools retrieve each one. Pass a specific
type (e.g. `genome-assembly`) for its full field list and schema documentation
link.

## Installation

### Option 1 — Desktop Extension (recommended for Claude Desktop users)

1. Download `ncbi-datasets.mcpb` from the [Releases](../../releases) page.
2. Double-click the file and click **Install** in Claude Desktop.
3. Optionally enter your [NCBI API key](https://www.ncbi.nlm.nih.gov/account/) and download directory.

The NCBI CLI tools are downloaded automatically on first use (`NCBI_AUTO_INSTALL=true` is set by default in the extension).

### Option 2 — JSON config (Claude Desktop / Claude Code)

Add to `claude_desktop_config.json` (macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "ncbi-datasets": {
      "command": "uvx",
      "args": ["ncbi-datasets-mcp"],
      "env": {
        "NCBI_API_KEY": "your_key_here",
        "NCBI_DOWNLOAD_DIR": "/path/to/downloads",
        "NCBI_AUTO_INSTALL": "true"
      }
    }
  }
}
```

Requires [uv](https://docs.astral.sh/uv/getting-started/installation/) (`curl -LsSf https://astral.sh/uv/install.sh | sh`).

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `NCBI_API_KEY` | *(none)* | NCBI API key — raises rate limit to 10 req/s |
| `NCBI_DOWNLOAD_DIR` | `~/Downloads/ncbi_datasets` | Default download location |
| `NCBI_AUTO_INSTALL` | `false` | Auto-install CLI tools on startup |
| `NCBI_MAX_RESULTS` | `20` | Cap for summary tool result counts |
| `NCBI_REQUEST_TIMEOUT` | `300` | Seconds before a download times out |
| `NCBI_CLI_PATH` | *(auto)* | Override path to `datasets` binary |
| `NCBI_DATAFORMAT_PATH` | *(auto)* | Override path to `dataformat` binary |

## Development

```bash
# Install with dev extras
pip install -e ".[dev]"

# Run unit tests
pytest

# Run all tests including live network calls
pytest -m integration

# Regenerate enums from the current NCBI OpenAPI spec
python scripts/gen_enums.py

# Run the server locally (stdio transport)
ncbi-datasets-mcp
```

## Architecture

```
src/ncbi_datasets_mcp/
  server.py           FastMCP app — tool registrations only
  config.py           Pydantic-settings env config
  cli/
    locator.py        Find datasets/dataformat (config → PATH → cache)
    installer.py      Download binaries from NCBI FTP
    runner.py         Async subprocess wrapper
  rest/
    client.py         httpx client for metadata/summary endpoints
  domains/
    _generated_enums.py  Vendored enums from OpenAPI spec
    common.py         Shared utilities (output dir, filename sanitising)
    genome.py         Genome CLI arg builders + response shaping
    taxonomy.py       Taxonomy CLI arg builders
  models/
    responses.py      Shared DownloadResult dataclass
```

Summary tools (no file I/O) → REST API.  
Download and format-conversion tools → NCBI CLI binaries.

## Cite

If you use NCBI Datasets in your research, please cite:
> NCBI Datasets. National Center for Biotechnology Information. https://www.ncbi.nlm.nih.gov/datasets/

## License

MIT

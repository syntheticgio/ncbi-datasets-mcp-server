# list_data_types Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a `list_data_types` MCP tool that returns a comprehensive, readable catalog of the 11 NCBI Datasets data report schema types, with optional per-type drill-down and cross-references to the existing tools that fetch each type.

**Architecture:** A new static-data module `domains/catalog.py` holds the curated catalog (a list of `DataReportType` dataclasses) plus `overview()` and `describe()` rendering functions. A thin `list_data_types` tool in `server.py` wraps them, matching the existing tool pattern. No network or filesystem — pure, deterministic functions.

**Tech Stack:** Python 3.11+, `dataclasses`, FastMCP, pytest.

---

### Task 1: Catalog data model and entries

**Files:**
- Create: `src/ncbi_datasets_mcp/domains/catalog.py`
- Test: `tests/unit/test_domains_catalog.py`

- [ ] **Step 1: Write the failing test**

Create `tests/unit/test_domains_catalog.py`:

```python
"""Unit tests for domains/catalog.py."""

from ncbi_datasets_mcp.domains import catalog


EXPECTED_KEYS = {
    "gene",
    "gene-product",
    "genome-assembly",
    "genome-sequence",
    "microbigg-e",
    "prokaryote-gene",
    "prokaryote-gene-location",
    "taxonomy",
    "taxonomy-names",
    "virus",
    "virus-annotation",
}


class TestCatalogData:
    def test_has_all_eleven_report_types(self):
        keys = {entry.key for entry in catalog.DATA_REPORT_TYPES}
        assert keys == EXPECTED_KEYS

    def test_every_entry_is_fully_populated(self):
        for entry in catalog.DATA_REPORT_TYPES:
            assert entry.title
            assert entry.summary
            assert entry.field_categories
            assert entry.docs_url.startswith("https://www.ncbi.nlm.nih.gov/")
            assert isinstance(entry.produced_by, list)

    def test_keys_are_unique(self):
        keys = [entry.key for entry in catalog.DATA_REPORT_TYPES]
        assert len(keys) == len(set(keys))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_domains_catalog.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'ncbi_datasets_mcp.domains.catalog'`

- [ ] **Step 3: Write the catalog module**

Create `src/ncbi_datasets_mcp/domains/catalog.py`:

```python
"""Static catalog of NCBI Datasets data report schema types.

Describes the kinds of metadata NCBI Datasets packages up (genes, genome
assemblies, taxonomy, viruses, etc.) and which tools in this server return
each type. Sourced from:
https://www.ncbi.nlm.nih.gov/datasets/docs/v2/reference-docs/data-reports/
"""

from dataclasses import dataclass

_DOCS_BASE = (
    "https://www.ncbi.nlm.nih.gov/datasets/docs/v2/reference-docs/data-reports/"
)


@dataclass(frozen=True)
class DataReportType:
    """One NCBI Datasets data report schema type."""

    key: str
    title: str
    summary: str
    field_categories: list[str]
    docs_url: str
    produced_by: list[str]


DATA_REPORT_TYPES: list[DataReportType] = [
    DataReportType(
        key="gene",
        title="Gene report",
        summary="Gene record metadata.",
        field_categories=[
            "Gene identifiers (Gene ID, symbol, synonyms)",
            "Description and gene type",
            "Organism and taxonomy",
            "Genomic ranges and orientation",
            "Reference standards and Ensembl cross-references",
        ],
        docs_url=_DOCS_BASE + "gene/",
        produced_by=[],
    ),
    DataReportType(
        key="gene-product",
        title="Gene product report",
        summary=(
            "Gene record identifiers, genomic locations, transcripts, and "
            "products."
        ),
        field_categories=[
            "Gene identifiers and symbol",
            "Genomic locations",
            "Transcripts (accession, length, exons)",
            "Protein products (accession, name, length)",
        ],
        docs_url=_DOCS_BASE + "gene-product/",
        produced_by=[],
    ),
    DataReportType(
        key="genome-assembly",
        title="Genome assembly report",
        summary=(
            "Genome record accession, organism, assembly statistics, and "
            "annotation info."
        ),
        field_categories=[
            "Assembly accession and paired accession (RefSeq/GenBank)",
            "Organism and taxonomy",
            "Assembly statistics (contig/scaffold N50, total length, GC%)",
            "Assembly level, source, and release date",
            "Annotation info (provider, release, gene counts)",
            "BioProject, BioSample, and submitter",
        ],
        docs_url=_DOCS_BASE + "genome-assembly/",
        produced_by=["genome_summary_by_taxon", "genome_summary_by_accession"],
    ),
    DataReportType(
        key="genome-sequence",
        title="Genome sequence report",
        summary="Genome assembly sequence accessions, chromosome, and length.",
        field_categories=[
            "Sequence accession (GenBank/RefSeq)",
            "Chromosome / molecule name and role",
            "Sequence length",
            "Assembly unit and assigned molecule type",
        ],
        docs_url=_DOCS_BASE + "genome-sequence/",
        produced_by=[
            "genome_summary_by_taxon",
            "genome_summary_by_accession",
            "dataformat_genome_tsv",
        ],
    ),
    DataReportType(
        key="microbigg-e",
        title="MicroBIGG-E report",
        summary=(
            "MicroBIGG-E record accession, organism, location, and biosample "
            "information."
        ),
        field_categories=[
            "Element symbol and name (AMR / virulence / stress genes)",
            "Organism and taxonomy",
            "Genomic location (contig, start, stop, strand)",
            "Assembly and BioSample accessions",
            "Identity and coverage metrics",
        ],
        docs_url=_DOCS_BASE + "microbigge/",
        produced_by=[],
    ),
    DataReportType(
        key="prokaryote-gene",
        title="Prokaryote gene report",
        summary="Prokaryote gene record identifiers, protein info, and taxonomic scope.",
        field_categories=[
            "Gene identifiers and symbol",
            "Protein name and accession",
            "Taxonomic scope",
            "Conserved domain / functional annotation",
        ],
        docs_url=_DOCS_BASE + "prokaryote-gene/",
        produced_by=[],
    ),
    DataReportType(
        key="prokaryote-gene-location",
        title="Prokaryote gene location report",
        summary="Prokaryote gene location record identifiers, organism, and genomic locations.",
        field_categories=[
            "Gene and protein identifiers",
            "Organism and taxonomy",
            "Genomic locations (accession, range, strand)",
        ],
        docs_url=_DOCS_BASE + "prokaryote-gene-location/",
        produced_by=[],
    ),
    DataReportType(
        key="taxonomy",
        title="Taxonomy report",
        summary="General information about a taxonomic identifier.",
        field_categories=[
            "Tax ID and scientific name",
            "Rank",
            "Lineage (parent tax IDs)",
            "Counts of child taxa and genomes",
        ],
        docs_url=_DOCS_BASE + "taxonomy/",
        produced_by=["taxonomy_summary"],
    ),
    DataReportType(
        key="taxonomy-names",
        title="Taxonomy names report",
        summary="Detailed information about names associated with a taxonomic identifier.",
        field_categories=[
            "Tax ID",
            "Scientific name",
            "Common names and synonyms",
            "Name classes (authority, includes, genbank common name)",
        ],
        docs_url=_DOCS_BASE + "taxonomy-names/",
        produced_by=["taxonomy_summary"],
    ),
    DataReportType(
        key="virus",
        title="Virus report",
        summary="Virus record metadata.",
        field_categories=[
            "Nucleotide accession",
            "Organism and taxonomy",
            "Isolate, host, and geographic location",
            "Collection date and release date",
            "Completeness and length",
        ],
        docs_url=_DOCS_BASE + "virus/",
        produced_by=[],
    ),
    DataReportType(
        key="virus-annotation",
        title="Virus annotation report",
        summary=(
            "Virus record identifiers, sample information, genomic locations, "
            "and products."
        ),
        field_categories=[
            "Nucleotide accession and identifiers",
            "Sample information (isolate, host, location)",
            "Genomic locations of genes/mature peptides",
            "Protein products (name, accession)",
        ],
        docs_url=_DOCS_BASE + "virus-annotation/",
        produced_by=[],
    ),
]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_domains_catalog.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add src/ncbi_datasets_mcp/domains/catalog.py tests/unit/test_domains_catalog.py
git commit -m "Add data report type catalog data model"
```

---

### Task 2: overview() and describe() rendering functions

**Files:**
- Modify: `src/ncbi_datasets_mcp/domains/catalog.py` (append functions)
- Test: `tests/unit/test_domains_catalog.py` (append tests)

- [ ] **Step 1: Write the failing tests**

Append to `tests/unit/test_domains_catalog.py`:

```python
class TestOverview:
    def test_lists_all_types(self):
        result = catalog.overview()
        assert len(result["data_types"]) == 11
        # Rendered report mentions every title
        for entry in catalog.DATA_REPORT_TYPES:
            assert entry.title in result["report"]

    def test_overview_entries_omit_field_categories(self):
        result = catalog.overview()
        first = result["data_types"][0]
        assert "field_categories" not in first
        assert "summary" in first
        assert "produced_by" in first

    def test_report_notes_unsupported_types(self):
        result = catalog.overview()
        assert "not yet" in result["report"].lower()


class TestDescribe:
    def test_known_type_returns_full_detail(self):
        result = catalog.describe("genome-assembly")
        entry = result["data_type"]
        assert entry["key"] == "genome-assembly"
        assert entry["field_categories"]
        assert entry["docs_url"].startswith("https://")
        assert "genome_summary_by_taxon" in entry["produced_by"]
        assert "Genome assembly report" in result["report"]

    def test_unknown_type_returns_error_with_available(self):
        result = catalog.describe("bogus")
        assert "error" in result
        assert "bogus" in result["error"]
        assert set(result["available_types"]) == EXPECTED_KEYS

    def test_loose_genome_suggests_both(self):
        result = catalog.describe("genome")
        assert "error" in result
        assert "genome-assembly" in result["error"]
        assert "genome-sequence" in result["error"]

    def test_describe_is_case_insensitive(self):
        result = catalog.describe("Genome-Assembly")
        assert result["data_type"]["key"] == "genome-assembly"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/unit/test_domains_catalog.py -v`
Expected: FAIL with `AttributeError: module ... has no attribute 'overview'`

- [ ] **Step 3: Append the functions to `catalog.py`**

Append to `src/ncbi_datasets_mcp/domains/catalog.py`:

```python
_BY_KEY = {entry.key: entry for entry in DATA_REPORT_TYPES}


def _tools_phrase(produced_by: list[str]) -> str:
    if produced_by:
        return "Retrieve with: " + ", ".join(produced_by)
    return "Not yet supported by this server (see docs link)."


def overview() -> dict:
    """Readable overview of all NCBI Datasets data report types.

    Returns a dict with a rendered ``report`` string and a structured
    ``data_types`` list (summary-level, no field categories).
    """
    lines = [
        "# NCBI Datasets data report types",
        "",
        (
            "NCBI Datasets packages metadata as the following data report "
            "schemas. Call list_data_types with a report_type for the full "
            "field list of any one type."
        ),
        "",
    ]
    data_types = []
    for entry in DATA_REPORT_TYPES:
        lines.append(f"## {entry.title}  (`{entry.key}`)")
        lines.append(entry.summary)
        lines.append(_tools_phrase(entry.produced_by))
        lines.append("")
        data_types.append(
            {
                "key": entry.key,
                "title": entry.title,
                "summary": entry.summary,
                "produced_by": entry.produced_by,
                "docs_url": entry.docs_url,
            }
        )
    return {"report": "\n".join(lines), "data_types": data_types}


def describe(report_type: str) -> dict:
    """Full detail for one data report type.

    Returns a dict with a rendered ``report`` and a structured ``data_type``.
    On an unknown key, returns ``{"error": ..., "available_types": [...]}``.
    """
    key = report_type.strip().lower()
    entry = _BY_KEY.get(key)
    if entry is None:
        matches = [k for k in _BY_KEY if key and key in k]
        hint = ""
        if matches:
            hint = " Did you mean: " + ", ".join(sorted(matches)) + "?"
        return {
            "error": f"Unknown report_type '{report_type}'.{hint}",
            "available_types": list(_BY_KEY),
        }

    lines = [
        f"# {entry.title}  (`{entry.key}`)",
        "",
        entry.summary,
        "",
        "## Field categories",
    ]
    lines += [f"- {cat}" for cat in entry.field_categories]
    lines += ["", _tools_phrase(entry.produced_by), "", f"Schema docs: {entry.docs_url}"]

    return {
        "report": "\n".join(lines),
        "data_type": {
            "key": entry.key,
            "title": entry.title,
            "summary": entry.summary,
            "field_categories": entry.field_categories,
            "produced_by": entry.produced_by,
            "docs_url": entry.docs_url,
        },
    }
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/test_domains_catalog.py -v`
Expected: PASS (all tests in the file)

- [ ] **Step 5: Commit**

```bash
git add src/ncbi_datasets_mcp/domains/catalog.py tests/unit/test_domains_catalog.py
git commit -m "Add overview and describe rendering for data type catalog"
```

---

### Task 3: Register the list_data_types tool

**Files:**
- Modify: `src/ncbi_datasets_mcp/server.py`
- Test: `tests/unit/test_domains_catalog.py` (append a tool-mapping integrity test)

> **Note:** The package entry point is `ncbi_datasets_mcp.server:main` (`pyproject.toml` `[project.scripts]`), so `src/ncbi_datasets_mcp/server.py` is the file FastMCP loads and the one to edit. A near-duplicate root `server.py` exists but is not loaded by the installed script; leave it alone.

- [ ] **Step 1: Add a tool-mapping integrity test**

Append to `tests/unit/test_domains_catalog.py`:

```python
class TestToolMappingIntegrity:
    def test_produced_by_names_are_real_tools(self):
        import inspect

        from ncbi_datasets_mcp import server as server_mod

        defined = {
            name
            for name, obj in inspect.getmembers(server_mod)
            if inspect.iscoroutinefunction(obj)
        }
        referenced = {
            tool
            for entry in catalog.DATA_REPORT_TYPES
            for tool in entry.produced_by
        }
        missing = referenced - defined
        assert not missing, f"catalog references unknown tools: {missing}"
```

- [ ] **Step 2: Run test to verify current state**

Run: `pytest tests/unit/test_domains_catalog.py::TestToolMappingIntegrity -v`
Expected: PASS — the referenced tools (`genome_summary_by_taxon`, `genome_summary_by_accession`, `taxonomy_summary`, `dataformat_genome_tsv`) already exist in `ncbi_datasets_mcp.server`.

- [ ] **Step 3: Add the import and tool**

In `src/ncbi_datasets_mcp/server.py`, add to the domain imports near the top (alongside the existing `from ncbi_datasets_mcp.domains import genome as genome_domain`):

```python
from ncbi_datasets_mcp.domains import catalog as catalog_domain
```

Then add this tool (place it after `ensure_cli`, before the genome tools, so discovery reads naturally):

```python
@mcp.tool()
async def list_data_types(report_type: str | None = None) -> dict[str, Any]:
    """Describe the kinds of data NCBI Datasets can provide.

    Call with no arguments for a readable overview of every NCBI Datasets
    data report type (genes, genome assemblies, sequences, taxonomy, viruses,
    and more), including which other tools in this server retrieve each one.

    Pass a report_type (e.g. "genome-assembly", "taxonomy", "virus") to get
    that type's full field categories and a link to its schema documentation.

    Args:
        report_type: Optional data report type key. Omit to list all types.
                     Unknown values return the list of valid keys.
    """
    try:
        if report_type is None:
            return catalog_domain.overview()
        return catalog_domain.describe(report_type)
    except Exception as exc:
        return {"error": str(exc), "report_type": report_type}
```

- [ ] **Step 4: Run the full test suite**

Run: `pytest -m "not integration" -v`
Expected: PASS (existing tests + new catalog tests, including TestToolMappingIntegrity)

- [ ] **Step 5: Commit**

```bash
git add src/ncbi_datasets_mcp/server.py tests/unit/test_domains_catalog.py
git commit -m "Register list_data_types tool"
```

---

### Task 4: Documentation

**Files:**
- Modify: `README.md`
- Modify: `CHANGELOG.md`

- [ ] **Step 1: Update the README tool table**

In `README.md`, add this row to the Tools table as the first data row (right after the `ensure_cli` row):

```markdown
| `list_data_types` | — | Describe what kinds of data NCBI Datasets provides; optional per-type detail |
```

- [ ] **Step 2: Add a discovery note to the README**

In `README.md`, immediately after the Tools table, add:

```markdown
### Discovering available data

Not sure what NCBI Datasets offers? Ask "what kind of data can I get from
datasets?" and the server's `list_data_types` tool returns a readable catalog of
every data report type — genes, genome assemblies, genome sequences, taxonomy,
viruses, and more — along with which tools retrieve each one. Pass a specific
type (e.g. `genome-assembly`) for its full field list and schema documentation
link.
```

- [ ] **Step 3: Add a CHANGELOG entry**

In `CHANGELOG.md`, under the top/unreleased section, add:

```markdown
### Added
- `list_data_types` tool — describes the NCBI Datasets data report schema types
  (gene, genome assembly, genome sequence, taxonomy, virus, and more), with an
  optional `report_type` argument for per-type field detail and docs links.
```

- [ ] **Step 4: Verify docs render and nothing else broke**

Run: `pytest -m "not integration" -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add README.md CHANGELOG.md
git commit -m "Document list_data_types tool"
```

---

## Notes for the implementer

- `pytest` async tests work via the project's existing config (see other
  `async def test_*`). Don't add asyncio markers the repo doesn't already use.
- The catalog is the single source of truth for the tool mapping; Task 3's
  integrity test is what keeps it honest. If you add a tool name to
  `produced_by`, that test must still pass.
- Keys are lowercase, hyphenated, and match the NCBI docs slugs except
  `microbigg-e` (NCBI's page slug is `microbigge`; the `docs_url` reflects the
  real slug while the key stays readable).

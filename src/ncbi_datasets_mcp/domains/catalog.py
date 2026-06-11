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
        summary=(
            "Prokaryote gene record identifiers, protein info, and taxonomic "
            "scope."
        ),
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
        summary=(
            "Prokaryote gene location record identifiers, organism, and "
            "genomic locations."
        ),
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
        summary=(
            "Detailed information about names associated with a taxonomic "
            "identifier."
        ),
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
    lines += [
        "",
        _tools_phrase(entry.produced_by),
        "",
        f"Schema docs: {entry.docs_url}",
    ]

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

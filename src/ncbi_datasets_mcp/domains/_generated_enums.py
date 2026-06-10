# AUTO-GENERATED — do not edit by hand.
# Run `python scripts/gen_enums.py` to regenerate from the NCBI OpenAPI spec.
# Spec last fetched: 2026-03-16 (date shown on NCBI REST API docs page)
# Source: https://www.ncbi.nlm.nih.gov/datasets/docs/v2/openapi3/openapi3.docs.yaml

from enum import Enum


class AssemblyLevel(str, Enum):
    """Genome assembly level filter."""
    CHROMOSOME = "chromosome"
    COMPLETE_GENOME = "complete_genome"
    CONTIG = "contig"
    SCAFFOLD = "scaffold"


class AssemblySource(str, Enum):
    """Genome assembly source database."""
    ALL = "all"
    GENBANK = "genbank"
    REFSEQ = "refseq"


class GenomeInclude(str, Enum):
    """Data types to include in a genome download package."""
    GENOME = "genome"
    RNA = "rna"
    PROTEIN = "protein"
    CDS = "cds"
    GFF3 = "gff3"
    GBFF = "gbff"
    SEQ_REPORT = "seq-report"
    NONE = "none"

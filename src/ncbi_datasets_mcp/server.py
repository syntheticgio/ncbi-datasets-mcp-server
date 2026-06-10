"""NCBI Datasets MCP Server.

Tools exposed:
  Setup:    ensure_cli
  Genome:   genome_summary_by_taxon, genome_summary_by_accession,
            genome_download_by_taxon, genome_download_by_accession,
            rehydrate_genome_package, dataformat_genome_tsv
  Taxonomy: taxonomy_summary, taxonomy_download
"""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from mcp.server.fastmcp import FastMCP

from ncbi_datasets_mcp.cli.installer import install_cli
from ncbi_datasets_mcp.cli.locator import locate_cli
from ncbi_datasets_mcp.cli.runner import CLIError, CLINotFoundError, run_datasets
from ncbi_datasets_mcp.config import settings
from ncbi_datasets_mcp.domains import genome as genome_domain
from ncbi_datasets_mcp.domains import taxonomy as taxonomy_domain
from ncbi_datasets_mcp.rest.client import (
    get_genome_summary_by_accession,
    get_genome_summary_by_taxon,
    get_taxonomy_summary,
)

logger = logging.getLogger(__name__)


# ── Lifespan: optional auto-install on startup ───────────────────────────────

@asynccontextmanager
async def _lifespan(app: FastMCP) -> AsyncIterator[None]:
    if settings.ncbi_auto_install and locate_cli() is None:
        logger.info("NCBI_AUTO_INSTALL=true — downloading CLI tools...")
        result = await install_cli()
        if result.success:
            logger.info(result.message)
        else:
            logger.warning("CLI auto-install failed: %s", result.message)
    yield


mcp = FastMCP(
    "ncbi-datasets",
    lifespan=_lifespan,
    dependencies=["httpx", "tenacity", "pydantic-settings", "platformdirs"],
)


# ── Helper: consistent error dict ────────────────────────────────────────────

def _cli_not_found_error(exc: CLINotFoundError) -> dict[str, str]:
    return {
        "error": str(exc),
        "action_required": "Call the ensure_cli tool to install the NCBI CLI tools.",
    }


# ── Setup ─────────────────────────────────────────────────────────────────────

@mcp.tool()
async def ensure_cli() -> dict[str, Any]:
    """Check whether the NCBI datasets/dataformat CLI tools are installed and,
    if not, download and install them automatically. Call this tool once before
    using any download or format-conversion tools.

    Returns the install status, binary paths, and version string.
    """
    binaries = locate_cli()
    if binaries is not None:
        try:
            ver_result = await run_datasets(["--version"])
            return {
                "status": "already_installed",
                "datasets_path": str(binaries.datasets),
                "dataformat_path": str(binaries.dataformat),
                "version": ver_result.stdout.strip(),
            }
        except CLIError:
            pass  # fall through to reinstall

    result = await install_cli()
    if result.success:
        return {
            "status": "installed",
            "datasets_path": str(result.datasets_path),
            "dataformat_path": str(result.dataformat_path),
            "version": result.version,
            "message": result.message,
        }
    return {
        "status": "failed",
        "message": result.message,
        "manual_install_url": (
            "https://www.ncbi.nlm.nih.gov/datasets/docs/v2/"
            "command-line-tools/download-and-install/"
        ),
    }


# ── Genome summary (REST) ─────────────────────────────────────────────────────

@mcp.tool()
async def genome_summary_by_taxon(
    taxon: str,
    assembly_level: list[str] | None = None,
    assembly_source: str | None = None,
    reference_only: bool = False,
    annotated_only: bool = False,
    limit: int = 20,
) -> dict[str, Any]:
    """Search NCBI for genome assemblies matching a taxon name or tax ID.

    Returns assembly metadata including accession numbers, organism info,
    assembly statistics, annotation status, and submission details.

    Args:
        taxon: Taxon name (e.g. "human", "Mus musculus") or NCBI tax ID
        assembly_level: Filter by level — chromosome, complete_genome, contig, scaffold
        assembly_source: Filter by source — all, genbank, refseq
        reference_only: Return only reference/representative genomes
        annotated_only: Return only annotated genomes
        limit: Maximum number of assemblies to return (capped by server config)
    """
    try:
        return await get_genome_summary_by_taxon(
            taxon=taxon,
            assembly_level=assembly_level,
            assembly_source=assembly_source,
            reference_only=reference_only,
            annotated_only=annotated_only,
            limit=limit,
        )
    except Exception as exc:
        return {"error": str(exc), "taxon": taxon}


@mcp.tool()
async def genome_summary_by_accession(accessions: list[str]) -> dict[str, Any]:
    """Retrieve genome assembly metadata for one or more NCBI accessions.

    Args:
        accessions: RefSeq or GenBank assembly accessions
                    (e.g. ["GCF_000001405.40", "GCA_000001405.29"])
    """
    try:
        return await get_genome_summary_by_accession(accessions)
    except Exception as exc:
        return {"error": str(exc), "accessions": accessions}


# ── Genome downloads (CLI) ────────────────────────────────────────────────────

@mcp.tool()
async def genome_download_by_accession(
    accessions: list[str],
    include: list[str] | None = None,
    output_dir: str | None = None,
    dehydrated: bool = False,
) -> dict[str, Any]:
    """Download a genome data package for one or more assembly accessions.

    Returns the local path to the downloaded ZIP file.

    Args:
        accessions: RefSeq/GenBank assembly accessions
        include: Data types — genome, rna, protein, cds, gff3, gbff, seq-report.
                 Defaults to ["genome"].
        output_dir: Directory for the download. Uses NCBI_DOWNLOAD_DIR if omitted.
        dehydrated: Download a lightweight dehydrated package (use
                    rehydrate_genome_package to fetch the actual sequence files).
    """
    try:
        result = await genome_domain.download_genome_by_accession(
            accessions=accessions,
            include=include,
            output_dir=output_dir,
            dehydrated=dehydrated,
        )
        return result.to_dict()
    except CLINotFoundError as exc:
        return _cli_not_found_error(exc)
    except CLIError as exc:
        return {"error": str(exc), "stderr": exc.stderr}
    except Exception as exc:
        return {"error": str(exc)}


@mcp.tool()
async def genome_download_by_taxon(
    taxon: str,
    include: list[str] | None = None,
    output_dir: str | None = None,
    dehydrated: bool = False,
    reference_only: bool = False,
) -> dict[str, Any]:
    """Download genome data packages for assemblies matching a taxon.

    For taxa with many assemblies, use dehydrated=True first, then call
    rehydrate_genome_package to fetch only the data you need.

    Args:
        taxon: Taxon name or NCBI tax ID
        include: Data types — genome, rna, protein, cds, gff3, gbff, seq-report
        output_dir: Directory for the download
        dehydrated: Download a dehydrated package (recommended for large taxa)
        reference_only: Download only the reference/representative genome
    """
    try:
        result = await genome_domain.download_genome_by_taxon(
            taxon=taxon,
            include=include,
            output_dir=output_dir,
            dehydrated=dehydrated,
            reference_only=reference_only,
        )
        return result.to_dict()
    except CLINotFoundError as exc:
        return _cli_not_found_error(exc)
    except CLIError as exc:
        return {"error": str(exc), "stderr": exc.stderr}
    except Exception as exc:
        return {"error": str(exc)}


@mcp.tool()
async def rehydrate_genome_package(package_path: str) -> dict[str, Any]:
    """Fetch the full sequence files for a dehydrated genome package.

    Args:
        package_path: Path to the dehydrated ZIP file or its extracted directory.
    """
    try:
        return await genome_domain.rehydrate_genome_package(package_path)
    except CLINotFoundError as exc:
        return _cli_not_found_error(exc)
    except CLIError as exc:
        return {"error": str(exc), "stderr": exc.stderr}
    except FileNotFoundError as exc:
        return {"error": str(exc)}
    except Exception as exc:
        return {"error": str(exc)}


@mcp.tool()
async def dataformat_genome_tsv(
    jsonl_path: str,
    fields: list[str] | None = None,
) -> str:
    """Convert a genome JSONL data report from a downloaded package to TSV.

    Args:
        jsonl_path: Path to the genome data_report.jsonl file inside the package.
        fields: Optional list of fields to include. Omit to use the default set.
    """
    try:
        return await genome_domain.dataformat_genome_tsv(jsonl_path, fields)
    except CLINotFoundError as exc:
        return f"Error: {exc}. Call ensure_cli first."
    except (CLIError, FileNotFoundError) as exc:
        return f"Error: {exc}"
    except Exception as exc:
        return f"Error: {exc}"


# ── Taxonomy (REST + CLI) ─────────────────────────────────────────────────────

@mcp.tool()
async def taxonomy_summary(taxon: str) -> dict[str, Any]:
    """Get taxonomy metadata for a taxon — lineage, rank, scientific name,
    common names, and child taxa.

    Args:
        taxon: Taxon name (e.g. "human", "Bacteria") or NCBI tax ID
    """
    try:
        return await get_taxonomy_summary(taxon)
    except Exception as exc:
        return {"error": str(exc), "taxon": taxon}


@mcp.tool()
async def taxonomy_download(
    taxon: str,
    output_dir: str | None = None,
) -> dict[str, Any]:
    """Download a taxonomy data package for a given taxon.

    Args:
        taxon: Taxon name or NCBI tax ID
        output_dir: Directory for the download
    """
    try:
        result = await taxonomy_domain.download_taxonomy(taxon, output_dir)
        return result.to_dict()
    except CLINotFoundError as exc:
        return _cli_not_found_error(exc)
    except CLIError as exc:
        return {"error": str(exc), "stderr": exc.stderr}
    except Exception as exc:
        return {"error": str(exc)}


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()

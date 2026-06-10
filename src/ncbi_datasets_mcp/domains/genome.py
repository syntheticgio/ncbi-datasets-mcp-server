"""Genome domain: CLI arg construction and response shaping.

Summary/metadata calls go through rest.client; this module handles
download and format-conversion operations that require the CLI.
"""

from pathlib import Path
from typing import Any, Optional

from ncbi_datasets_mcp.cli.runner import run_dataformat, run_datasets
from ncbi_datasets_mcp.domains._generated_enums import GenomeInclude
from ncbi_datasets_mcp.domains.common import extract_warnings, resolve_output_dir, safe_filename
from ncbi_datasets_mcp.models.responses import DownloadResult


def _resolve_include(include: list[str] | None) -> list[GenomeInclude]:
    """Validate and coerce include strings to GenomeInclude enum members."""
    raw = include or ["genome"]
    return [GenomeInclude(v) for v in raw]


def _download_tail_args(
    output_path: Path,
    include: list[GenomeInclude],
    dehydrated: bool,
) -> list[str]:
    args: list[str] = ["--filename", str(output_path)]
    for inc in include:
        args += ["--include", inc.value]
    if dehydrated:
        args.append("--dehydrated")
    return args


def _make_download_result(output_file: Path, command: str, stderr: str) -> DownloadResult:
    size = output_file.stat().st_size if output_file.exists() else None
    return DownloadResult(
        path=str(output_file),
        exists=output_file.exists(),
        size_bytes=size,
        command=command,
        warnings=extract_warnings(stderr),
    )


async def download_genome_by_accession(
    accessions: list[str],
    include: list[str] | None = None,
    output_dir: Optional[str] = None,
    dehydrated: bool = False,
) -> DownloadResult:
    include_types = _resolve_include(include)
    out_dir = resolve_output_dir(output_dir)
    label = safe_filename("_".join(accessions[:3]))
    output_file = out_dir / f"genome_{label}.zip"

    args = (
        ["download", "genome", "accession"]
        + accessions
        + _download_tail_args(output_file, include_types, dehydrated)
    )
    result = await run_datasets(args)
    return _make_download_result(
        output_file,
        command=f"datasets download genome accession {' '.join(accessions)}",
        stderr=result.stderr,
    )


async def download_genome_by_taxon(
    taxon: str,
    include: list[str] | None = None,
    output_dir: Optional[str] = None,
    dehydrated: bool = False,
    reference_only: bool = False,
) -> DownloadResult:
    include_types = _resolve_include(include)
    out_dir = resolve_output_dir(output_dir)
    output_file = out_dir / f"genome_{safe_filename(taxon)}.zip"

    args = (
        ["download", "genome", "taxon", taxon]
        + _download_tail_args(output_file, include_types, dehydrated)
    )
    if reference_only:
        args.append("--reference")

    result = await run_datasets(args)
    return _make_download_result(
        output_file,
        command=f"datasets download genome taxon {taxon}",
        stderr=result.stderr,
    )


async def rehydrate_genome_package(package_path: str) -> dict[str, Any]:
    path = Path(package_path)
    if not path.exists():
        raise FileNotFoundError(f"Package not found: {package_path}")

    # datasets rehydrate works on the directory containing the ZIP
    target_dir = path.parent if path.is_file() else path
    result = await run_datasets(["rehydrate", "--directory", str(target_dir)])

    return {
        "package_path": package_path,
        "status": "rehydrated",
        "output": result.stdout.strip() or "Rehydration complete.",
        "warnings": extract_warnings(result.stderr),
    }


async def dataformat_genome_tsv(
    jsonl_path: str,
    fields: list[str] | None = None,
) -> str:
    """Convert a genome JSONL data report to TSV via dataformat."""
    path = Path(jsonl_path)
    if not path.exists():
        raise FileNotFoundError(f"JSONL file not found: {jsonl_path}")

    args = ["tsv", "genome", "--inputfile", str(path)]
    if fields:
        args += ["--fields", ",".join(fields)]

    result = await run_dataformat(args)
    return result.stdout

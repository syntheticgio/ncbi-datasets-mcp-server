"""Taxonomy domain: CLI arg construction and response shaping."""

from ncbi_datasets_mcp.cli.runner import run_datasets
from ncbi_datasets_mcp.domains.common import resolve_output_dir, safe_filename
from ncbi_datasets_mcp.models.responses import DownloadResult


async def download_taxonomy(
    taxon: str,
    output_dir: str | None = None,
) -> DownloadResult:
    out_dir = resolve_output_dir(output_dir)
    output_file = out_dir / f"taxonomy_{safe_filename(taxon)}.zip"

    args = ["download", "taxonomy", "taxon", taxon, "--filename", str(output_file)]
    await run_datasets(args)

    size = output_file.stat().st_size if output_file.exists() else None
    return DownloadResult(
        path=str(output_file),
        exists=output_file.exists(),
        size_bytes=size,
        command=f"datasets download taxonomy taxon {taxon}",
    )

"""Shared domain utilities."""

from pathlib import Path
from typing import Optional

from ncbi_datasets_mcp.config import settings


def resolve_output_dir(output_dir: Optional[str]) -> Path:
    """Return an absolute, writable output directory.

    Priority: caller-supplied path → NCBI_DOWNLOAD_DIR env → OS downloads dir.
    Creates the directory if it doesn't exist.
    """
    if output_dir:
        path = Path(output_dir).expanduser().resolve()
        path.mkdir(parents=True, exist_ok=True)
        return path
    return settings.ncbi_download_dir


def safe_filename(label: str, max_len: int = 64) -> str:
    """Sanitise an arbitrary string for use in a filename."""
    safe = label.replace(" ", "_")
    for ch in r'/\:*?"<>|':
        safe = safe.replace(ch, "_")
    return safe[:max_len]


def extract_warnings(stderr: str) -> list[str]:
    """Pull warning lines from CLI stderr output."""
    return [
        line.strip()
        for line in stderr.splitlines()
        if line.strip() and "warning" in line.lower()
    ]

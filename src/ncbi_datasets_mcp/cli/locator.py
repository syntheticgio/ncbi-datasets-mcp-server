"""Locate the datasets and dataformat CLI binaries.

Resolution order:
  1. Explicit paths from NCBI_CLI_PATH / NCBI_DATAFORMAT_PATH env vars
  2. PATH (conda installs, user-managed installs)
  3. Managed cache directory (binaries downloaded by installer.py)
"""

import platform
import shutil
from dataclasses import dataclass
from pathlib import Path

import platformdirs

from ncbi_datasets_mcp.config import settings

# Stable cache dir for binaries downloaded by this server
CACHE_DIR = Path(platformdirs.user_cache_dir("ncbi-datasets-mcp"))


def _exe(name: str) -> str:
    """Append .exe on Windows."""
    return f"{name}.exe" if platform.system() == "Windows" else name


@dataclass
class CLIBinaries:
    datasets: Path
    dataformat: Path

    def is_valid(self) -> bool:
        return self.datasets.is_file() and self.dataformat.is_file()


def locate_cli() -> CLIBinaries | None:
    """Return CLIBinaries if both tools are found, otherwise None."""
    datasets_name = _exe("datasets")
    dataformat_name = _exe("dataformat")

    # 1. Explicit config overrides
    if settings.ncbi_cli_path and settings.ncbi_dataformat_path:
        candidate = CLIBinaries(settings.ncbi_cli_path, settings.ncbi_dataformat_path)
        if candidate.is_valid():
            return candidate

    # 2. System PATH
    d = shutil.which(datasets_name)
    df = shutil.which(dataformat_name)
    if d and df:
        return CLIBinaries(Path(d), Path(df))

    # 3. Managed cache dir
    cached = CLIBinaries(CACHE_DIR / datasets_name, CACHE_DIR / dataformat_name)
    if cached.is_valid():
        return cached

    return None


def get_install_dir() -> Path:
    """Return (and create) the managed binary cache directory."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return CACHE_DIR

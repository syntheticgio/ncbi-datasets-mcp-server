"""Environment-driven configuration for ncbi-datasets-mcp."""

from pathlib import Path
from typing import Optional

import platformdirs
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # ignore stray env vars from host process
    )

    # NCBI API key — increases rate limit from 3 to 10 req/s
    ncbi_api_key: Optional[str] = None

    # Default download directory for genome/taxonomy packages
    ncbi_download_dir: Path = Path(platformdirs.user_downloads_dir()) / "ncbi_datasets"

    # Explicit override paths for the CLI binaries (optional)
    ncbi_cli_path: Optional[Path] = None
    ncbi_dataformat_path: Optional[Path] = None

    # CLI lifecycle
    ncbi_auto_install: bool = False  # set True in .mcpb manifest defaults
    ncbi_cli_version: str = "latest"  # "latest" or a pinned semver e.g. "16.26.0"

    # Request behaviour
    ncbi_max_results: int = 20
    ncbi_request_timeout: float = 300.0  # seconds — covers large genome downloads

    @field_validator("ncbi_download_dir")
    @classmethod
    def ensure_download_dir_exists(cls, v: Path) -> Path:
        v.mkdir(parents=True, exist_ok=True)
        return v


# Module-level singleton — imported by other modules
settings = Settings()

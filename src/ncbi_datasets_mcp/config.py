"""Environment-driven configuration for ncbi-datasets-mcp."""

import os
import sys
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

    @field_validator("ncbi_download_dir", mode="before")
    @classmethod
    def _expand_download_dir(cls, v: object) -> object:
        """Expand shell-style ``${VAR}`` / ``$VAR`` / ``~`` in the configured path.

        Some MCP hosts pass user-config defaults through verbatim (e.g. the
        literal string ``${HOME}/Downloads/ncbi_datasets``) instead of expanding
        them. pathlib does not expand these, so without this we would try to
        mkdir a directory literally named ``${HOME}`` at the filesystem root.
        """
        if isinstance(v, (str, Path)):
            raw = str(v).strip()
            expanded = os.path.expandvars(os.path.expanduser(raw))
            # Blank value, or expansion failure (var undefined → "$" token
            # survives): fall back to the platform default so we never operate
            # on an empty path or a literal "${...}".
            if not raw or "$" in expanded:
                import platformdirs

                return Path(platformdirs.user_downloads_dir()) / "ncbi_datasets"
            return Path(expanded)
        return v

    @field_validator("ncbi_download_dir")
    @classmethod
    def ensure_download_dir_exists(cls, v: Path) -> Path:
        try:
            v.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            # A bad download dir must never crash server startup — downloads
            # can still be redirected per-request. Warn and carry on.
            print(
                f"[ncbi-datasets-mcp] warning: could not create download dir {v!r}: {exc}",
                file=sys.stderr,
            )
        return v


# Module-level singleton — imported by other modules
settings = Settings()

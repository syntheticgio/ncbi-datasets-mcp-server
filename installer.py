"""Download the NCBI datasets/dataformat CLI binaries for the current platform.

Binaries are single static files published by NCBI at predictable FTP URLs:
  https://ftp.ncbi.nlm.nih.gov/pub/datasets/command-line/v2/{platform}/{binary}
"""

import asyncio
import platform
import stat
from dataclasses import dataclass
from pathlib import Path

import httpx

from ncbi_datasets_mcp.cli.locator import CLIBinaries, _exe, get_install_dir

FTP_BASE = "https://ftp.ncbi.nlm.nih.gov/pub/datasets/command-line/v2"

# Maps (system, machine) → NCBI FTP platform path
_PLATFORM_MAP: dict[tuple[str, str], str] = {
    ("Linux", "x86_64"): "linux-amd64",
    ("Linux", "aarch64"): "linux-arm64",
    ("Linux", "armv7l"): "linux-arm",
    ("Darwin", "x86_64"): "mac",
    ("Darwin", "arm64"): "mac",   # Universal binary covers Apple Silicon
    ("Windows", "AMD64"): "win64",
    ("Windows", "x86_64"): "win64",
}


@dataclass
class InstallResult:
    success: bool
    datasets_path: Path | None = None
    dataformat_path: Path | None = None
    version: str | None = None
    message: str = ""


def detect_platform() -> str:
    """Return the NCBI FTP sub-path for the current OS/arch, or raise."""
    system = platform.system()
    machine = platform.machine()
    key = (system, machine)
    if key in _PLATFORM_MAP:
        return _PLATFORM_MAP[key]
    raise RuntimeError(
        f"Unsupported platform: {system}/{machine}. "
        "Install manually: "
        "https://www.ncbi.nlm.nih.gov/datasets/docs/v2/command-line-tools/download-and-install/"
    )


async def _download_binary(url: str, dest: Path, client: httpx.AsyncClient) -> None:
    """Stream a binary from *url* to *dest*, then mark it executable."""
    async with client.stream("GET", url) as response:
        response.raise_for_status()
        dest.parent.mkdir(parents=True, exist_ok=True)
        with dest.open("wb") as fh:
            async for chunk in response.aiter_bytes(chunk_size=65_536):
                fh.write(chunk)

    if platform.system() != "Windows":
        dest.chmod(dest.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)


async def install_cli() -> InstallResult:
    """Download both binaries into the managed cache dir and verify them."""
    try:
        platform_path = detect_platform()
    except RuntimeError as exc:
        return InstallResult(success=False, message=str(exc))

    install_dir = get_install_dir()
    datasets_dest = install_dir / _exe("datasets")
    dataformat_dest = install_dir / _exe("dataformat")

    datasets_url = f"{FTP_BASE}/{platform_path}/{_exe('datasets')}"
    dataformat_url = f"{FTP_BASE}/{platform_path}/{_exe('dataformat')}"

    async with httpx.AsyncClient(follow_redirects=True, timeout=120.0) as client:
        try:
            await _download_binary(datasets_url, datasets_dest, client)
            await _download_binary(dataformat_url, dataformat_dest, client)
        except httpx.HTTPError as exc:
            return InstallResult(success=False, message=f"Download failed: {exc}")

    # Smoke-test: run --version on the freshly installed binary
    try:
        proc = await asyncio.create_subprocess_exec(
            str(datasets_dest),
            "--version",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=15.0)
        version = stdout.decode().strip()
    except Exception as exc:
        return InstallResult(
            success=False,
            message=f"Binary installed but verification failed: {exc}",
        )

    return InstallResult(
        success=True,
        datasets_path=datasets_dest,
        dataformat_path=dataformat_dest,
        version=version,
        message=f"Installed {version} → {install_dir}",
    )

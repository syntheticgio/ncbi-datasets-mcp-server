"""Async subprocess wrappers for the datasets and dataformat CLI tools.

Responsibilities:
  - Resolve binary paths via locator.locate_cli()
  - Inject API key argument when configured
  - Apply timeout, capture stdout/stderr
  - Map non-zero exit codes to structured CLIError
"""

import asyncio
from dataclasses import dataclass

from ncbi_datasets_mcp.cli.locator import locate_cli
from ncbi_datasets_mcp.config import settings


class CLINotFoundError(Exception):
    """Raised when datasets/dataformat cannot be located on the system."""


class CLIError(Exception):
    """Raised when a CLI command exits with a non-zero status code."""

    def __init__(self, message: str, stderr: str, returncode: int) -> None:
        super().__init__(message)
        self.stderr = stderr
        self.returncode = returncode


@dataclass
class RunResult:
    stdout: str
    stderr: str
    returncode: int


def _require_cli():
    binaries = locate_cli()
    if binaries is None:
        raise CLINotFoundError(
            "NCBI CLI tools (datasets/dataformat) are not installed. "
            "Call the ensure_cli tool to install them, or set NCBI_AUTO_INSTALL=true."
        )
    return binaries


async def run_datasets(args: list[str], timeout: float | None = None) -> RunResult:
    """Run `datasets [--api-key KEY] <args>` and return the result."""
    binaries = _require_cli()
    effective_timeout = timeout or settings.ncbi_request_timeout

    cmd: list[str] = [str(binaries.datasets)]
    if settings.ncbi_api_key:
        cmd += ["--api-key", settings.ncbi_api_key]
    cmd += args

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout_b, stderr_b = await asyncio.wait_for(
            proc.communicate(), timeout=effective_timeout
        )
    except asyncio.TimeoutError:
        proc.kill()
        await proc.communicate()
        raise CLIError(
            f"datasets timed out after {effective_timeout}s",
            stderr="",
            returncode=-1,
        )

    result = RunResult(
        stdout=stdout_b.decode("utf-8", errors="replace"),
        stderr=stderr_b.decode("utf-8", errors="replace"),
        returncode=proc.returncode,
    )
    if proc.returncode != 0:
        raise CLIError(
            f"datasets exited {proc.returncode}: {result.stderr.strip()}",
            stderr=result.stderr,
            returncode=proc.returncode,
        )
    return result


async def run_dataformat(
    args: list[str],
    stdin: str | None = None,
    timeout: float = 60.0,
) -> RunResult:
    """Run `dataformat <args>`, optionally piping *stdin* to the process."""
    binaries = _require_cli()

    proc = await asyncio.create_subprocess_exec(
        str(binaries.dataformat),
        *args,
        stdin=asyncio.subprocess.PIPE if stdin else None,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout_b, stderr_b = await asyncio.wait_for(
            proc.communicate(input=stdin.encode() if stdin else None),
            timeout=timeout,
        )
    except asyncio.TimeoutError:
        proc.kill()
        await proc.communicate()
        raise CLIError("dataformat timed out", stderr="", returncode=-1)

    result = RunResult(
        stdout=stdout_b.decode("utf-8", errors="replace"),
        stderr=stderr_b.decode("utf-8", errors="replace"),
        returncode=proc.returncode,
    )
    if proc.returncode != 0:
        raise CLIError(
            f"dataformat exited {proc.returncode}: {result.stderr.strip()}",
            stderr=result.stderr,
            returncode=proc.returncode,
        )
    return result

"""Unit tests for cli/runner.py."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ncbi_datasets_mcp.cli.runner import (
    CLIError,
    CLINotFoundError,
    run_dataformat,
    run_datasets,
)


def _make_process(stdout: bytes, stderr: bytes, returncode: int):
    proc = MagicMock()
    proc.returncode = returncode
    proc.communicate = AsyncMock(return_value=(stdout, stderr))
    proc.kill = MagicMock()
    return proc


class TestRunDatasets:
    async def test_success_returns_run_result(self, mock_locate_cli):
        proc = _make_process(b'{"total_count": 1}', b"", 0)
        with patch("asyncio.create_subprocess_exec", return_value=proc):
            result = await run_datasets(["summary", "genome", "taxon", "human"])
        assert result.returncode == 0
        assert "total_count" in result.stdout

    async def test_injects_api_key_when_configured(self, mock_locate_cli):
        proc = _make_process(b"ok", b"", 0)
        captured: list = []

        async def fake_exec(*args, **kwargs):
            captured.extend(args)
            return proc

        with (
            patch("asyncio.create_subprocess_exec", side_effect=fake_exec),
            patch(
                "ncbi_datasets_mcp.cli.runner.settings"
            ) as mock_settings,
        ):
            mock_settings.ncbi_api_key = "my-test-key"
            mock_settings.ncbi_request_timeout = 60.0
            await run_datasets(["--version"])

        assert "--api-key" in captured
        assert "my-test-key" in captured

    async def test_raises_cli_error_on_nonzero_exit(self, mock_locate_cli):
        proc = _make_process(b"", b"Error: bad accession", 1)
        with patch("asyncio.create_subprocess_exec", return_value=proc):
            with pytest.raises(CLIError) as exc_info:
                await run_datasets(["download", "genome", "accession", "INVALID"])
        assert exc_info.value.returncode == 1
        assert "bad accession" in exc_info.value.stderr

    async def test_raises_cli_not_found_when_no_binaries(self, monkeypatch):
        monkeypatch.setattr("ncbi_datasets_mcp.cli.runner.locate_cli", lambda: None)
        with pytest.raises(CLINotFoundError, match="ensure_cli"):
            await run_datasets(["--version"])

    async def test_raises_cli_error_on_timeout(self, mock_locate_cli):
        proc = _make_process(b"", b"", 0)

        async def slow_communicate(input=None):
            await asyncio.sleep(100)
            return b"", b""

        proc.communicate = slow_communicate

        with (
            patch("asyncio.create_subprocess_exec", return_value=proc),
            patch(
                "ncbi_datasets_mcp.cli.runner.settings"
            ) as mock_settings,
        ):
            mock_settings.ncbi_api_key = None
            mock_settings.ncbi_request_timeout = 0.01
            with pytest.raises(CLIError, match="timed out"):
                await run_datasets(["download", "genome", "taxon", "human"])


class TestRunDataformat:
    async def test_success(self, mock_locate_cli):
        proc = _make_process(b"col1\tcol2\n", b"", 0)
        with patch("asyncio.create_subprocess_exec", return_value=proc):
            result = await run_dataformat(["tsv", "genome"], stdin='{"key": "value"}')
        assert "col1" in result.stdout

    async def test_raises_cli_error_on_failure(self, mock_locate_cli):
        proc = _make_process(b"", b"unknown flag", 2)
        with patch("asyncio.create_subprocess_exec", return_value=proc):
            with pytest.raises(CLIError):
                await run_dataformat(["tsv", "genome", "--bad-flag"])

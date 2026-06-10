"""Shared pytest fixtures."""

from pathlib import Path

import pytest

from ncbi_datasets_mcp.cli.locator import CLIBinaries
from ncbi_datasets_mcp.cli.runner import RunResult


@pytest.fixture
def fake_binaries(tmp_path: Path) -> CLIBinaries:
    """Return a CLIBinaries pointing at real (empty) files in tmp_path."""
    datasets = tmp_path / "datasets"
    dataformat = tmp_path / "dataformat"
    datasets.touch()
    dataformat.touch()
    return CLIBinaries(datasets=datasets, dataformat=dataformat)


@pytest.fixture
def ok_run_result() -> RunResult:
    return RunResult(stdout='{"reports": []}', stderr="", returncode=0)


@pytest.fixture
def mock_locate_cli(monkeypatch, fake_binaries):
    """Patch locate_cli to always return fake_binaries."""
    monkeypatch.setattr(
        "ncbi_datasets_mcp.cli.runner.locate_cli", lambda: fake_binaries
    )
    return fake_binaries

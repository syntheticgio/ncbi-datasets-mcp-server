"""Unit tests for cli/locator.py."""

from pathlib import Path
from unittest.mock import patch

from ncbi_datasets_mcp.cli.locator import CLIBinaries, locate_cli


def _make_binaries(tmp_path: Path) -> tuple[Path, Path]:
    d = tmp_path / "datasets"
    df = tmp_path / "dataformat"
    d.touch()
    df.touch()
    return d, df


class TestLocateCLI:
    def test_returns_none_when_nothing_found(self, tmp_path):
        with (
            patch("ncbi_datasets_mcp.cli.locator.settings") as mock_settings,
            patch("ncbi_datasets_mcp.cli.locator.shutil.which", return_value=None),
            patch("ncbi_datasets_mcp.cli.locator.CACHE_DIR", tmp_path / "empty"),
        ):
            mock_settings.ncbi_cli_path = None
            mock_settings.ncbi_dataformat_path = None
            assert locate_cli() is None

    def test_finds_on_path(self, tmp_path):
        d, df = _make_binaries(tmp_path)

        def fake_which(name):
            return str(d) if "datasets" in name else str(df)

        with (
            patch("ncbi_datasets_mcp.cli.locator.settings") as mock_settings,
            patch("ncbi_datasets_mcp.cli.locator.shutil.which", side_effect=fake_which),
        ):
            mock_settings.ncbi_cli_path = None
            mock_settings.ncbi_dataformat_path = None
            result = locate_cli()
            assert result is not None
            assert result.datasets == d
            assert result.dataformat == df

    def test_finds_in_cache_dir(self, tmp_path):
        d, df = _make_binaries(tmp_path)
        with (
            patch("ncbi_datasets_mcp.cli.locator.settings") as mock_settings,
            patch("ncbi_datasets_mcp.cli.locator.shutil.which", return_value=None),
            patch("ncbi_datasets_mcp.cli.locator.CACHE_DIR", tmp_path),
        ):
            mock_settings.ncbi_cli_path = None
            mock_settings.ncbi_dataformat_path = None
            result = locate_cli()
            assert result is not None
            assert result.is_valid()

    def test_explicit_config_takes_priority(self, tmp_path):
        d, df = _make_binaries(tmp_path)
        with patch("ncbi_datasets_mcp.cli.locator.settings") as mock_settings:
            mock_settings.ncbi_cli_path = d
            mock_settings.ncbi_dataformat_path = df
            result = locate_cli()
            assert result is not None
            assert result.datasets == d

    def test_explicit_config_skipped_if_files_missing(self, tmp_path):
        with (
            patch("ncbi_datasets_mcp.cli.locator.settings") as mock_settings,
            patch("ncbi_datasets_mcp.cli.locator.shutil.which", return_value=None),
            patch("ncbi_datasets_mcp.cli.locator.CACHE_DIR", tmp_path / "empty"),
        ):
            mock_settings.ncbi_cli_path = tmp_path / "nonexistent_datasets"
            mock_settings.ncbi_dataformat_path = tmp_path / "nonexistent_dataformat"
            assert locate_cli() is None


class TestCLIBinaries:
    def test_is_valid_true_when_files_exist(self, tmp_path):
        d, df = _make_binaries(tmp_path)
        assert CLIBinaries(d, df).is_valid()

    def test_is_valid_false_when_file_missing(self, tmp_path):
        d = tmp_path / "datasets"
        d.touch()
        assert not CLIBinaries(d, tmp_path / "missing").is_valid()

"""Unit tests for cli/installer.py."""

from unittest.mock import patch

import pytest

from ncbi_datasets_mcp.cli.installer import FTP_BASE, detect_platform


class TestDetectPlatform:
    """Verify correct FTP sub-path is selected for each platform."""

    @pytest.mark.parametrize(
        "system, machine, expected",
        [
            ("Linux", "x86_64", "linux-amd64"),
            ("Linux", "aarch64", "linux-arm64"),
            ("Linux", "armv7l", "linux-arm"),
            ("Darwin", "x86_64", "mac"),
            ("Darwin", "arm64", "mac"),
            ("Windows", "AMD64", "win64"),
        ],
    )
    def test_known_platforms(self, system, machine, expected):
        with (
            patch("ncbi_datasets_mcp.cli.installer.platform.system", return_value=system),
            patch("ncbi_datasets_mcp.cli.installer.platform.machine", return_value=machine),
        ):
            assert detect_platform() == expected

    def test_unsupported_platform_raises(self):
        with (
            patch("ncbi_datasets_mcp.cli.installer.platform.system", return_value="FreeBSD"),
            patch("ncbi_datasets_mcp.cli.installer.platform.machine", return_value="x86_64"),
        ):
            with pytest.raises(RuntimeError, match="Unsupported platform"):
                detect_platform()


class TestDownloadURLConstruction:
    """Verify FTP URLs are formed correctly for each platform."""

    def test_linux_amd64_url(self):
        base = f"{FTP_BASE}/linux-amd64"
        assert base.startswith("https://ftp.ncbi.nlm.nih.gov")
        assert "linux-amd64" in base

    def test_mac_url(self):
        assert f"{FTP_BASE}/mac/datasets" == (
            "https://ftp.ncbi.nlm.nih.gov/pub/datasets/command-line/v2/mac/datasets"
        )

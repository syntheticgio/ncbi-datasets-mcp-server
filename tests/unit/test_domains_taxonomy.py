"""Unit tests for domains/taxonomy.py."""

from pathlib import Path
from unittest.mock import patch

from ncbi_datasets_mcp.cli.runner import RunResult
from ncbi_datasets_mcp.domains import taxonomy as taxonomy_domain


def _ok() -> RunResult:
    return RunResult(stdout="", stderr="", returncode=0)


class TestDownloadTaxonomy:
    async def test_builds_correct_args(self, tmp_path):
        captured: list = []

        async def fake_run(args, **kwargs):
            captured.extend(args)
            return _ok()

        with (
            patch("ncbi_datasets_mcp.domains.taxonomy.run_datasets", side_effect=fake_run),
            patch(
                "ncbi_datasets_mcp.domains.taxonomy.resolve_output_dir",
                return_value=tmp_path,
            ),
        ):
            await taxonomy_domain.download_taxonomy("Homo sapiens")

        assert "download" in captured
        assert "taxonomy" in captured
        assert "taxon" in captured
        assert "Homo sapiens" in captured
        assert "--filename" in captured

    async def test_output_filename_is_sanitised(self, tmp_path):
        captured: list = []

        async def fake_run(args, **kwargs):
            captured.extend(args)
            return _ok()

        with (
            patch("ncbi_datasets_mcp.domains.taxonomy.run_datasets", side_effect=fake_run),
            patch(
                "ncbi_datasets_mcp.domains.taxonomy.resolve_output_dir",
                return_value=tmp_path,
            ),
        ):
            await taxonomy_domain.download_taxonomy("Homo sapiens")

        filename_idx = captured.index("--filename")
        output_path = captured[filename_idx + 1]
        # Spaces should be replaced so the path is shell-safe
        assert " " not in Path(output_path).name

"""Unit tests for domains/genome.py — arg construction and response shaping."""

from unittest.mock import patch

import pytest

from ncbi_datasets_mcp.cli.runner import RunResult
from ncbi_datasets_mcp.domains import genome as genome_domain
from ncbi_datasets_mcp.models.responses import DownloadResult


def _ok(stdout: str = "") -> RunResult:
    return RunResult(stdout=stdout, stderr="", returncode=0)


class TestDownloadGenomeByAccession:
    async def test_builds_correct_args_and_returns_result(self, tmp_path):
        captured: list = []

        async def fake_run(args, **kwargs):
            captured.extend(args)
            return _ok()

        with (
            patch("ncbi_datasets_mcp.domains.genome.run_datasets", side_effect=fake_run),
            patch(
                "ncbi_datasets_mcp.domains.genome.resolve_output_dir",
                return_value=tmp_path,
            ),
        ):
            # Create the expected output file so exists check passes
            (tmp_path / "genome_GCF_000001405.40.zip").touch()
            result = await genome_domain.download_genome_by_accession(
                accessions=["GCF_000001405.40"],
                include=["genome", "gff3"],
            )

        assert "download" in captured
        assert "genome" in captured
        assert "accession" in captured
        assert "GCF_000001405.40" in captured
        assert "--include" in captured
        assert "gff3" in captured
        assert isinstance(result, DownloadResult)

    async def test_default_include_is_genome(self, tmp_path):
        captured: list = []

        async def fake_run(args, **kwargs):
            captured.extend(args)
            return _ok()

        with (
            patch("ncbi_datasets_mcp.domains.genome.run_datasets", side_effect=fake_run),
            patch(
                "ncbi_datasets_mcp.domains.genome.resolve_output_dir",
                return_value=tmp_path,
            ),
        ):
            await genome_domain.download_genome_by_accession(["GCF_000001405.40"])

        include_idx = captured.index("--include")
        assert captured[include_idx + 1] == "genome"

    async def test_dehydrated_flag_included(self, tmp_path):
        captured: list = []

        async def fake_run(args, **kwargs):
            captured.extend(args)
            return _ok()

        with (
            patch("ncbi_datasets_mcp.domains.genome.run_datasets", side_effect=fake_run),
            patch(
                "ncbi_datasets_mcp.domains.genome.resolve_output_dir",
                return_value=tmp_path,
            ),
        ):
            await genome_domain.download_genome_by_accession(
                ["GCF_000001405.40"], dehydrated=True
            )

        assert "--dehydrated" in captured


class TestDownloadGenomeByTaxon:
    async def test_reference_only_flag(self, tmp_path):
        captured: list = []

        async def fake_run(args, **kwargs):
            captured.extend(args)
            return _ok()

        with (
            patch("ncbi_datasets_mcp.domains.genome.run_datasets", side_effect=fake_run),
            patch(
                "ncbi_datasets_mcp.domains.genome.resolve_output_dir",
                return_value=tmp_path,
            ),
        ):
            await genome_domain.download_genome_by_taxon("human", reference_only=True)

        assert "--reference" in captured
        assert "taxon" in captured
        assert "human" in captured


class TestDataformatGenomeTsv:
    async def test_builds_correct_args(self, tmp_path):
        jsonl_file = tmp_path / "data_report.jsonl"
        jsonl_file.write_text('{"accessionVersion": "GCF_000001405.40"}\n')
        captured: list = []

        async def fake_run(args, **kwargs):
            captured.extend(args)
            return RunResult(stdout="col1\tcol2\n", stderr="", returncode=0)

        with patch("ncbi_datasets_mcp.domains.genome.run_dataformat", side_effect=fake_run):
            result = await genome_domain.dataformat_genome_tsv(
                str(jsonl_file), fields=["accession", "organism-name"]
            )

        assert "tsv" in captured
        assert "genome" in captured
        assert "--fields" in captured
        assert "col1" in result

    async def test_raises_when_file_missing(self):
        with pytest.raises(FileNotFoundError):
            await genome_domain.dataformat_genome_tsv("/nonexistent/path.jsonl")


class TestRehydrateGenomePackage:
    async def test_calls_rehydrate_with_correct_dir(self, tmp_path):
        zip_file = tmp_path / "genome.zip"
        zip_file.touch()
        captured: list = []

        async def fake_run(args, **kwargs):
            captured.extend(args)
            return _ok("Completed rehydration")

        with patch("ncbi_datasets_mcp.domains.genome.run_datasets", side_effect=fake_run):
            result = await genome_domain.rehydrate_genome_package(str(zip_file))

        assert "rehydrate" in captured
        assert "--directory" in captured
        assert result["status"] == "rehydrated"

    async def test_raises_when_path_missing(self):
        with pytest.raises(FileNotFoundError):
            await genome_domain.rehydrate_genome_package("/nonexistent/package.zip")

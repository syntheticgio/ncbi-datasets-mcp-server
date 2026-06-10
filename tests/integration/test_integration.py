"""Integration tests against the live NCBI Datasets API.

Run with:  pytest -m integration
Skipped by default in CI unless explicitly requested.

These tests use small, stable taxa/accessions unlikely to change:
- Human reference genome (GCF_000001405.40)
- NCBI tax ID 9606 (Homo sapiens)
"""

import pytest

from ncbi_datasets_mcp.rest.client import (
    get_genome_summary_by_accession,
    get_genome_summary_by_taxon,
    get_taxonomy_summary,
)


@pytest.mark.integration
async def test_genome_summary_by_taxon_human():
    result = await get_genome_summary_by_taxon(
        taxon="9606", reference_only=True, limit=5
    )
    assert "reports" in result
    assert len(result["reports"]) >= 1
    report = result["reports"][0]
    assert "accession" in report


@pytest.mark.integration
async def test_genome_summary_by_accession():
    result = await get_genome_summary_by_accession(["GCF_000001405.40"])
    assert "reports" in result
    assert result["reports"][0]["accession"] == "GCF_000001405.40"


@pytest.mark.integration
async def test_taxonomy_summary_human():
    result = await get_taxonomy_summary("9606")
    assert "reports" in result
    reports = result["reports"]
    assert len(reports) >= 1
    # Verify we got human taxonomy back
    tax_report = reports[0]
    assert "taxonomy" in tax_report
    assert tax_report["taxonomy"]["tax_id"] == 9606

"""Unit tests for rest/client.py — params construction and error handling."""

from unittest.mock import patch

import httpx
import pytest
import respx

from ncbi_datasets_mcp.rest.client import (
    BASE_URL,
    get_genome_summary_by_accession,
    get_genome_summary_by_taxon,
    get_taxonomy_summary,
)

GENOME_TAXON_URL = f"{BASE_URL}/genome/taxon/human/dataset_report"
GENOME_ACC_URL = f"{BASE_URL}/genome/accession/GCF_000001405.40/dataset_report"
TAXONOMY_URL = f"{BASE_URL}/taxonomy/taxon/9606/dataset_report"

MOCK_GENOME_RESPONSE = {"reports": [{"accession": "GCF_000001405.40"}], "total_count": 1}
MOCK_TAXONOMY_RESPONSE = {"reports": [{"taxonomy": {"tax_id": 9606}}], "total_count": 1}


class TestGetGenomeSummaryByTaxon:
    @respx.mock
    async def test_basic_request(self):
        respx.get(GENOME_TAXON_URL).mock(
            return_value=httpx.Response(200, json=MOCK_GENOME_RESPONSE)
        )
        result = await get_genome_summary_by_taxon("human")
        assert result["total_count"] == 1
        assert result["reports"][0]["accession"] == "GCF_000001405.40"

    @respx.mock
    async def test_assembly_level_filter_in_params(self):
        route = respx.get(GENOME_TAXON_URL).mock(
            return_value=httpx.Response(200, json=MOCK_GENOME_RESPONSE)
        )
        await get_genome_summary_by_taxon("human", assembly_level=["chromosome", "scaffold"])
        request = route.calls.last.request
        query = request.url.query.decode() if isinstance(request.url.query, bytes) else request.url.query
        assert "chromosome" in query
        assert "scaffold" in query

    @respx.mock
    async def test_reference_only_flag(self):
        route = respx.get(GENOME_TAXON_URL).mock(
            return_value=httpx.Response(200, json=MOCK_GENOME_RESPONSE)
        )
        await get_genome_summary_by_taxon("human", reference_only=True)
        request = route.calls.last.request
        query = request.url.query.decode() if isinstance(request.url.query, bytes) else request.url.query
        assert "reference_only=true" in query

    @respx.mock
    async def test_limit_capped_by_settings(self):
        route = respx.get(GENOME_TAXON_URL).mock(
            return_value=httpx.Response(200, json=MOCK_GENOME_RESPONSE)
        )
        with patch("ncbi_datasets_mcp.rest.client.settings") as mock_settings:
            mock_settings.ncbi_max_results = 5
            mock_settings.ncbi_api_key = None
            await get_genome_summary_by_taxon("human", limit=100)

        request = route.calls.last.request
        query = request.url.query.decode() if isinstance(request.url.query, bytes) else request.url.query
        assert "page_size=5" in query

    @respx.mock
    async def test_api_key_injected_in_header(self):
        route = respx.get(GENOME_TAXON_URL).mock(
            return_value=httpx.Response(200, json=MOCK_GENOME_RESPONSE)
        )
        with patch("ncbi_datasets_mcp.rest.client.settings") as mock_settings:
            mock_settings.ncbi_api_key = "test-key-123"
            mock_settings.ncbi_max_results = 20
            await get_genome_summary_by_taxon("human")

        request = route.calls.last.request
        assert request.headers.get("api-key") == "test-key-123"

    @respx.mock
    async def test_raises_on_404(self):
        respx.get(GENOME_TAXON_URL).mock(return_value=httpx.Response(404))
        with pytest.raises(httpx.HTTPStatusError):
            await get_genome_summary_by_taxon("human")


class TestGetGenomeSummaryByAccession:
    @respx.mock
    async def test_single_accession(self):
        respx.get(GENOME_ACC_URL).mock(
            return_value=httpx.Response(200, json=MOCK_GENOME_RESPONSE)
        )
        result = await get_genome_summary_by_accession(["GCF_000001405.40"])
        assert result["total_count"] == 1

    @respx.mock
    async def test_multiple_accessions_joined(self):
        url = f"{BASE_URL}/genome/accession/GCF_000001405.40,GCF_000001215.4/dataset_report"
        respx.get(url).mock(
            return_value=httpx.Response(200, json={"reports": [], "total_count": 0})
        )
        await get_genome_summary_by_accession(
            ["GCF_000001405.40", "GCF_000001215.4"]
        )


class TestGetTaxonomySummary:
    @respx.mock
    async def test_basic_request(self):
        respx.get(TAXONOMY_URL).mock(
            return_value=httpx.Response(200, json=MOCK_TAXONOMY_RESPONSE)
        )
        result = await get_taxonomy_summary("9606")
        assert result["total_count"] == 1

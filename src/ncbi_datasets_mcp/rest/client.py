"""Async REST client for NCBI Datasets v2 API.

Used for metadata/summary endpoints that return JSON inline.
Downloads go through the CLI (cli/runner.py) which handles streaming.

Rate limits:
  - 3 req/s without an API key
  - 10 req/s with an API key
Tenacity retries handle transient 429 / 5xx responses.
"""

from typing import Any

import httpx
from tenacity import (
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)

from ncbi_datasets_mcp.config import settings

BASE_URL = "https://api.ncbi.nlm.nih.gov/datasets/v2"


def _should_retry(exc: BaseException) -> bool:
    return (
        isinstance(exc, httpx.HTTPStatusError)
        and exc.response.status_code in (429, 500, 502, 503, 504)
    )


def _make_client() -> httpx.AsyncClient:
    headers: dict[str, str] = {"Accept": "application/json"}
    if settings.ncbi_api_key:
        headers["api-key"] = settings.ncbi_api_key
    return httpx.AsyncClient(base_url=BASE_URL, headers=headers, timeout=30.0)


@retry(
    retry=retry_if_exception(_should_retry),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    stop=stop_after_attempt(3),
    reraise=True,
)
async def _get(client: httpx.AsyncClient, path: str, params: dict | None = None) -> dict:
    response = await client.get(path, params=params)
    response.raise_for_status()
    return response.json()


async def get_genome_summary_by_taxon(
    taxon: str,
    assembly_level: list[str] | None = None,
    assembly_source: str | None = None,
    reference_only: bool = False,
    annotated_only: bool = False,
    limit: int | None = None,
) -> dict[str, Any]:
    """GET /genome/taxon/{taxon}/dataset_report"""
    page_size = min(limit or settings.ncbi_max_results, settings.ncbi_max_results)
    params: dict[str, Any] = {"page_size": page_size}
    if assembly_level:
        # httpx sends repeated keys as multiple query params, which NCBI expects
        params["filters.assembly_level"] = assembly_level
    if assembly_source:
        params["filters.assembly_source"] = assembly_source
    if reference_only:
        params["filters.reference_only"] = "true"
    if annotated_only:
        params["filters.has_annotation"] = "true"

    async with _make_client() as client:
        return await _get(client, f"/genome/taxon/{taxon}/dataset_report", params=params)


async def get_genome_summary_by_accession(accessions: list[str]) -> dict[str, Any]:
    """GET /genome/accession/{accessions}/dataset_report"""
    async with _make_client() as client:
        return await _get(
            client,
            f"/genome/accession/{','.join(accessions)}/dataset_report",
        )


async def get_taxonomy_summary(taxon: str) -> dict[str, Any]:
    """GET /taxonomy/taxon/{taxon}/dataset_report"""
    async with _make_client() as client:
        return await _get(client, f"/taxonomy/taxon/{taxon}/dataset_report")

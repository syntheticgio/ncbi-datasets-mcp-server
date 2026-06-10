"""Unit tests for domains/catalog.py."""

from ncbi_datasets_mcp.domains import catalog


EXPECTED_KEYS = {
    "gene",
    "gene-product",
    "genome-assembly",
    "genome-sequence",
    "microbigg-e",
    "prokaryote-gene",
    "prokaryote-gene-location",
    "taxonomy",
    "taxonomy-names",
    "virus",
    "virus-annotation",
}


class TestCatalogData:
    def test_has_all_eleven_report_types(self):
        keys = {entry.key for entry in catalog.DATA_REPORT_TYPES}
        assert keys == EXPECTED_KEYS

    def test_every_entry_is_fully_populated(self):
        for entry in catalog.DATA_REPORT_TYPES:
            assert entry.title
            assert entry.summary
            assert entry.field_categories
            assert entry.docs_url.startswith("https://www.ncbi.nlm.nih.gov/")
            assert isinstance(entry.produced_by, list)

    def test_keys_are_unique(self):
        keys = [entry.key for entry in catalog.DATA_REPORT_TYPES]
        assert len(keys) == len(set(keys))

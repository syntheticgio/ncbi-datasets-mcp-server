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


class TestOverview:
    def test_lists_all_types(self):
        result = catalog.overview()
        assert len(result["data_types"]) == 11
        # Rendered report mentions every title
        for entry in catalog.DATA_REPORT_TYPES:
            assert entry.title in result["report"]

    def test_overview_entries_omit_field_categories(self):
        result = catalog.overview()
        first = result["data_types"][0]
        assert "field_categories" not in first
        assert "summary" in first
        assert "produced_by" in first

    def test_report_notes_unsupported_types(self):
        result = catalog.overview()
        assert "not yet" in result["report"].lower()


class TestDescribe:
    def test_known_type_returns_full_detail(self):
        result = catalog.describe("genome-assembly")
        entry = result["data_type"]
        assert entry["key"] == "genome-assembly"
        assert entry["field_categories"]
        assert entry["docs_url"].startswith("https://")
        assert "genome_summary_by_taxon" in entry["produced_by"]
        assert "Genome assembly report" in result["report"]

    def test_unknown_type_returns_error_with_available(self):
        result = catalog.describe("bogus")
        assert "error" in result
        assert "bogus" in result["error"]
        assert set(result["available_types"]) == EXPECTED_KEYS

    def test_loose_genome_suggests_both(self):
        result = catalog.describe("genome")
        assert "error" in result
        assert "genome-assembly" in result["error"]
        assert "genome-sequence" in result["error"]

    def test_describe_is_case_insensitive(self):
        result = catalog.describe("Genome-Assembly")
        assert result["data_type"]["key"] == "genome-assembly"

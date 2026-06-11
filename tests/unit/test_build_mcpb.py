"""Unit tests for build_mcpb.py."""

import json
import sys
import zipfile
from pathlib import Path

import pytest

# build_mcpb.py lives at the repo root, not in a package — add it to path.
ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))
import build_mcpb  # noqa: E402


class TestPyprojectVersion:
    def test_reads_version_from_real_pyproject(self):
        version = build_mcpb._pyproject_version()
        assert version is not None
        parts = version.split(".")
        assert len(parts) == 3
        assert all(p.isdigit() for p in parts)

    def test_returns_none_when_file_missing(self, tmp_path, monkeypatch):
        monkeypatch.setattr(build_mcpb, "ROOT", tmp_path)
        assert build_mcpb._pyproject_version() is None

    def test_returns_none_when_version_absent(self, tmp_path, monkeypatch):
        (tmp_path / "pyproject.toml").write_text("[project]\nname = 'x'\n")
        monkeypatch.setattr(build_mcpb, "ROOT", tmp_path)
        assert build_mcpb._pyproject_version() is None


class TestBuild:
    def test_produces_mcpb_file(self, tmp_path):
        out = build_mcpb.build(version="9.9.9", out_dir=tmp_path)
        assert out.exists()
        assert out.name == "ncbi-datasets-9.9.9.mcpb"

    def test_bundle_contains_manifest(self, tmp_path):
        out = build_mcpb.build(version="9.9.9", out_dir=tmp_path)
        with zipfile.ZipFile(out) as zf:
            assert "manifest.json" in zf.namelist()

    def test_manifest_version_matches_requested(self, tmp_path):
        out = build_mcpb.build(version="9.9.9", out_dir=tmp_path)
        with zipfile.ZipFile(out) as zf:
            manifest = json.loads(zf.read("manifest.json"))
        assert manifest["version"] == "9.9.9"

    def test_version_defaults_to_pyproject(self, tmp_path):
        expected = build_mcpb._pyproject_version()
        out = build_mcpb.build(version=None, out_dir=tmp_path)
        with zipfile.ZipFile(out) as zf:
            manifest = json.loads(zf.read("manifest.json"))
        assert manifest["version"] == expected

    def test_root_path_resolves_correctly(self):
        # Guard against the ROOT regression: manifest.json must exist at ROOT.
        assert (build_mcpb.ROOT / "manifest.json").exists(), (
            f"manifest.json not found at {build_mcpb.ROOT} — "
            "ROOT is likely pointing to the wrong directory"
        )

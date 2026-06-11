#!/usr/bin/env python3
"""Build ncbi-datasets.mcpb — a Claude Desktop Extension bundle.

The .mcpb is a ZIP archive containing manifest.json plus any bundled assets.
For this Python server, the manifest points to `uvx ncbi-datasets-mcp`, so
the archive only needs the manifest (and optional icon). The Python package
itself is fetched from PyPI by uvx at install time.

Usage:
    python scripts/build_mcpb.py [--version VERSION] [--out DIR]

Requires: an icon at assets/icon.png (optional but recommended for the registry)
"""

import argparse
import json
import shutil
import sys
import zipfile
from pathlib import Path

import re

ROOT = Path(__file__).parent.parent


def _pyproject_version() -> str | None:
    pyproject = ROOT / "pyproject.toml"
    if not pyproject.exists():
        return None
    # Match `version = "x.y.z"` under [project] without pulling in a TOML parser.
    # Reads only up to 50 lines to stay fast; the version field is always near the top.
    text = "\n".join(pyproject.read_text().splitlines()[:50])
    m = re.search(r'^version\s*=\s*"([^"]+)"', text, re.MULTILINE)
    return m.group(1) if m else None


def load_manifest() -> dict:
    manifest_path = ROOT / "manifest.json"
    with manifest_path.open() as fh:
        return json.load(fh)


def sync_version(manifest: dict, version: str) -> dict:
    """Keep manifest version in sync with pyproject.toml version."""
    manifest = manifest.copy()
    manifest["version"] = version
    return manifest


def build(version: str | None, out_dir: Path) -> Path:
    manifest = load_manifest()

    if not version:
        version = _pyproject_version() or manifest.get("version", "0.0.0")
    manifest = sync_version(manifest, version)

    out_dir.mkdir(parents=True, exist_ok=True)
    bundle_path = out_dir / f"ncbi-datasets-{version}.mcpb"

    with zipfile.ZipFile(bundle_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        # manifest.json is the only required file
        zf.writestr("manifest.json", json.dumps(manifest, indent=2))

        # Optional icon
        icon_path = ROOT / "assets" / "icon.png"
        if icon_path.exists():
            zf.write(icon_path, "icon.png")
            print(f"  + icon.png")
        else:
            print(
                "  (no assets/icon.png found — bundle will work but won't show an icon)",
                file=sys.stderr,
            )

    size_kb = bundle_path.stat().st_size // 1024
    print(f"Built {bundle_path} ({size_kb} KB)")
    return bundle_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Build ncbi-datasets.mcpb")
    parser.add_argument("--version", help="Override version (default: from manifest.json)")
    parser.add_argument("--out", default="dist", help="Output directory (default: dist/)")
    args = parser.parse_args()

    bundle_path = build(version=args.version, out_dir=Path(args.out))
    print(f"\nTo install: double-click {bundle_path.name} in Finder/Explorer")
    print(f"Or: open Claude Desktop → Settings → Extensions → Install from file")


if __name__ == "__main__":
    main()

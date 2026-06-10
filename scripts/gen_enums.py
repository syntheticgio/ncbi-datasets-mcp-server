#!/usr/bin/env python3
"""Regenerate src/ncbi_datasets_mcp/domains/_generated_enums.py from the
NCBI Datasets OpenAPI v3 specification.

Usage:
    python scripts/gen_enums.py

Requires: pyyaml, httpx  (both in dev extras: pip install -e ".[dev]")
"""

import sys
from datetime import date
from pathlib import Path

try:
    import httpx
    import yaml
except ImportError:
    sys.exit("Install dev extras first:  pip install -e '.[dev]'")

SPEC_URL = "https://www.ncbi.nlm.nih.gov/datasets/docs/v2/openapi3/openapi3.docs.yaml"
OUT_FILE = (
    Path(__file__).parent.parent
    / "src/ncbi_datasets_mcp/domains/_generated_enums.py"
)

# Enum schemas we care about — map spec schema name → Python class name + docstring
WANTED: dict[str, tuple[str, str]] = {
    "V2AssemblyDatasetDescriptorsFilterAssemblyLevel": (
        "AssemblyLevel",
        "Genome assembly level filter.",
    ),
    "V2AssemblyDatasetDescriptorsFilterAssemblySource": (
        "AssemblySource",
        "Genome assembly source database.",
    ),
    "V2AssemblyDatasetRequestInclude": (
        "GenomeInclude",
        "Data types to include in a genome download package.",
    ),
}


def _fetch_spec() -> dict:
    print(f"Fetching spec from {SPEC_URL} ...")
    with httpx.Client(timeout=60.0, follow_redirects=True) as client:
        response = client.get(SPEC_URL)
        response.raise_for_status()
    return yaml.safe_load(response.text)


def _extract_enums(spec: dict) -> dict[str, list[str]]:
    schemas = spec.get("components", {}).get("schemas", {})
    result: dict[str, list[str]] = {}
    for spec_name, (class_name, _) in WANTED.items():
        schema = schemas.get(spec_name)
        if schema is None:
            print(f"  WARNING: schema '{spec_name}' not found in spec", file=sys.stderr)
            continue
        enum_values = schema.get("enum", [])
        if not enum_values:
            print(f"  WARNING: no enum values for '{spec_name}'", file=sys.stderr)
            continue
        result[class_name] = enum_values
    return result


def _python_member_name(value: str) -> str:
    """Convert an enum string value to a SCREAMING_SNAKE_CASE Python identifier."""
    return value.upper().replace("-", "_").replace(" ", "_").replace(".", "_")


def _render(enums: dict[str, list[str]]) -> str:
    today = date.today().isoformat()
    lines = [
        "# AUTO-GENERATED — do not edit by hand.",
        f"# Run `python scripts/gen_enums.py` to regenerate from the NCBI OpenAPI spec.",
        f"# Spec last fetched: {today}",
        f"# Source: {SPEC_URL}",
        "",
        "from enum import Enum",
        "",
    ]
    for class_name, values in enums.items():
        _, docstring = next(
            (v for k, v in WANTED.items() if v[0] == class_name),
            (class_name, ""),
        )
        lines.append("")
        lines.append(f"class {class_name}(str, Enum):")
        lines.append(f'    """{docstring}"""')
        for val in values:
            lines.append(f"    {_python_member_name(val)} = {val!r}")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    spec = _fetch_spec()
    enums = _extract_enums(spec)
    if not enums:
        sys.exit("No enums extracted — check WANTED mapping against current spec.")
    source = _render(enums)
    OUT_FILE.write_text(source)
    print(f"Written {len(enums)} enums → {OUT_FILE}")
    for cls, vals in enums.items():
        print(f"  {cls}: {vals}")


if __name__ == "__main__":
    main()

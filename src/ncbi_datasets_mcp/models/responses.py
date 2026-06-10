"""Shared response models for MCP tool outputs."""

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class DownloadResult:
    """Result returned by all download tools."""

    path: str
    exists: bool
    command: str
    size_bytes: Optional[int] = None
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "path": self.path,
            "exists": self.exists,
            "command": self.command,
        }
        if self.size_bytes is not None:
            result["size_bytes"] = self.size_bytes
            result["size_mb"] = round(self.size_bytes / 1_048_576, 2)
        if self.warnings:
            result["warnings"] = self.warnings
        return result

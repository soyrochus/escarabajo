"""Minimal MCP client shim for test usage."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from Escarabajo.server import EscarabajoServer


class MiniMCPClient:
    """Tiny helper that mirrors MCP tool invocation for tests."""

    def __init__(self, repo_root: Path):
        self.server = EscarabajoServer(repo_root)

    def call(self, tool: str, payload: Dict[str, Any] | None = None) -> Any:
        return self.server.invoke(tool, payload or {})


__all__ = ["MiniMCPClient"]

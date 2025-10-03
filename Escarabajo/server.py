"""MCP server façade for Escarabajo.

The implementation prefers FastMCP when available, but falls back to a minimal
callable server object so the module remains importable without optional
dependencies installed.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Dict

from .prompts import get_prompt, list_prompts
from .sync import SyncManager

try:  # pragma: no cover - optional dependency
    from mcp.server.fastmcp import FastMCPServer  # type: ignore
except Exception:  # pragma: no cover
    FastMCPServer = None  # type: ignore


ToolHandler = Callable[[Dict[str, Any]], Any]


class EscarabajoServer:
    """Simple synchronous MCP-compatible server wrapper."""

    def __init__(self, repo_root: Path | None = None):
        self.repo_root = repo_root or Path.cwd()
        self.manager = SyncManager(self.repo_root)
        self._tools: Dict[str, ToolHandler] = {
            "scan_repo": self._tool_scan_repo,
            "sync_all": self._tool_sync_all,
            "sync_paths": self._tool_sync_paths,
            "get_text_path": self._tool_get_text_path,
            "list_kb": self._tool_list_kb,
            "purge_outputs": self._tool_purge_outputs,
            "config_get": self._tool_config_get,
            "config_set": self._tool_config_set,
            "list_prompts": self._tool_list_prompts,
            "get_prompt": self._tool_get_prompt,
            "read_text": self._tool_read_text,
        }

    # ------------------------------------------------------------------
    def tool_names(self) -> list[str]:
        return sorted(self._tools)

    def invoke(self, name: str, payload: Dict[str, Any] | None = None) -> Any:
        if name not in self._tools:
            raise KeyError(f"Unknown tool '{name}'")
        handler = self._tools[name]
        data = payload or {}
        return handler(data)

    # ------------------------------------------------------------------
    # Tool handlers
    def _tool_scan_repo(self, payload: Dict[str, Any]) -> Any:
        return self.manager.scan_repo(
            globs=payload.get("globs"),
            exclude_globs=payload.get("exclude_globs"),
        )

    def _tool_sync_all(self, payload: Dict[str, Any]) -> Any:
        return self.manager.sync_all(
            globs=payload.get("globs"),
            exclude_globs=payload.get("exclude_globs"),
            ocr=payload.get("ocr"),
        )

    def _tool_sync_paths(self, payload: Dict[str, Any]) -> Any:
        paths = payload.get("paths", [])
        return self.manager.sync_paths(paths, ocr=payload.get("ocr"))

    def _tool_get_text_path(self, payload: Dict[str, Any]) -> Any:
        return self.manager.get_text_path(payload["src"], ocr=payload.get("ocr"))

    def _tool_list_kb(self, payload: Dict[str, Any]) -> Any:  # pylint: disable=unused-argument
        return self.manager.list_kb()

    def _tool_purge_outputs(self, payload: Dict[str, Any]) -> Any:
        return self.manager.purge_outputs(globs=payload.get("globs"))

    def _tool_config_get(self, payload: Dict[str, Any]) -> Any:  # pylint: disable=unused-argument
        return self.manager.config_get()

    def _tool_config_set(self, payload: Dict[str, Any]) -> Any:
        updates = payload or {}
        if not isinstance(updates, dict):
            raise TypeError("Expected payload to be a dict")
        return self.manager.config_set(updates)

    def _tool_list_prompts(self, payload: Dict[str, Any]) -> Any:  # pylint: disable=unused-argument
        return list_prompts()

    def _tool_get_prompt(self, payload: Dict[str, Any]) -> Any:
        return get_prompt(payload["name"])

    def _tool_read_text(self, payload: Dict[str, Any]) -> Any:
        if "out" not in payload:
            raise KeyError("read_text requires 'out'")
        return self.manager.read_text(payload["out"], max_bytes=payload.get("max_bytes"))


def create_server(repo_root: Path | None = None):
    """Create a server backed either by FastMCP or the simple wrapper."""

    if FastMCPServer is None:
        return EscarabajoServer(repo_root)

    manager = SyncManager(repo_root or Path.cwd())
    server = FastMCPServer("Escarabajo")

    @server.tool("scan_repo")  # type: ignore[attr-defined]
    def scan_repo(payload: Dict[str, Any]) -> Any:
        return manager.scan_repo(
            globs=payload.get("globs"),
            exclude_globs=payload.get("exclude_globs"),
        )

    @server.tool("sync_all")  # type: ignore[attr-defined]
    def sync_all(payload: Dict[str, Any]) -> Any:
        return manager.sync_all(
            globs=payload.get("globs"),
            exclude_globs=payload.get("exclude_globs"),
            ocr=payload.get("ocr"),
        )

    @server.tool("sync_paths")  # type: ignore[attr-defined]
    def sync_paths(payload: Dict[str, Any]) -> Any:
        return manager.sync_paths(payload.get("paths", []), ocr=payload.get("ocr"))

    @server.tool("get_text_path")  # type: ignore[attr-defined]
    def get_text_path(payload: Dict[str, Any]) -> Any:
        return manager.get_text_path(payload["src"], ocr=payload.get("ocr"))

    @server.tool("list_kb")  # type: ignore[attr-defined]
    def list_kb(payload: Dict[str, Any]) -> Any:  # pylint: disable=unused-argument
        return manager.list_kb()

    @server.tool("purge_outputs")  # type: ignore[attr-defined]
    def purge_outputs(payload: Dict[str, Any]) -> Any:
        return manager.purge_outputs(globs=payload.get("globs"))

    @server.tool("config_get")  # type: ignore[attr-defined]
    def config_get(payload: Dict[str, Any]) -> Any:  # pylint: disable=unused-argument
        return manager.config_get()

    @server.tool("config_set")  # type: ignore[attr-defined]
    def config_set(payload: Dict[str, Any]) -> Any:
        return manager.config_set(payload or {})

    @server.tool("list_prompts")  # type: ignore[attr-defined]
    def tool_list_prompts(payload: Dict[str, Any]) -> Any:  # pylint: disable=unused-argument
        return list_prompts()

    @server.tool("get_prompt")  # type: ignore[attr-defined]
    def tool_get_prompt(payload: Dict[str, Any]) -> Any:
        return get_prompt(payload["name"])

    @server.tool("read_text")  # type: ignore[attr-defined]
    def tool_read_text(payload: Dict[str, Any]) -> Any:
        return manager.read_text(payload["out"], max_bytes=payload.get("max_bytes"))

    return server


__all__ = ["create_server", "EscarabajoServer"]

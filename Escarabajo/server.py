"""MCP server façade for Escarabajo.

The implementation prefers FastMCP when available, but falls back to a minimal
callable server object so the module remains importable without optional
dependencies installed.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Dict, Optional

from .prompts import get_prompt, list_prompts
from .sync import SyncManager

try:  # pragma: no cover - optional dependency
    from mcp.server.fastmcp import FastMCP
except Exception:  # pragma: no cover
    FastMCP = None  # type: ignore


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
        return get_prompt(payload["name"], params=payload.get("params"))

    def _tool_read_text(self, payload: Dict[str, Any]) -> Any:
        if "out" not in payload:
            raise KeyError("read_text requires 'out'")
        return self.manager.read_text(payload["out"], max_bytes=payload.get("max_bytes"))


def create_server(repo_root: Path | None = None):
    """Create a server backed either by FastMCP or the simple wrapper."""

    if FastMCP is None:
        return EscarabajoServer(repo_root)

    manager = SyncManager(repo_root or Path.cwd())
    server = FastMCP(name="Escarabajo", instructions="Escarabajo synchronizes binary docs to Markdown.")

    @server.tool()
    def scan_repo(
        globs: list[str] | None = None,
        exclude_globs: list[str] | None = None
    ) -> Any:
        """Scan repository for extractable documents (DOCX, PPTX, PDF).
        
        Args:
            globs: File patterns to include (default: ["**/*.docx", "**/*.pptx", "**/*.pdf"])
            exclude_globs: File patterns to exclude (default: [".git/**", "node_modules/**"])
            
        Returns:
            Dictionary with list of discovered files
        """
        return manager.scan_repo(globs=globs, exclude_globs=exclude_globs)

    @server.tool()
    def sync_all(
        globs: list[str] | None = None,
        exclude_globs: list[str] | None = None,
        ocr: bool = False
    ) -> Any:
        """Extract content from all discovered documents into Markdown format.
        
        Args:
            globs: File patterns to include
            exclude_globs: File patterns to exclude  
            ocr: Enable OCR for scanned PDFs
            
        Returns:
            Summary of processing results with counts and output paths
        """
        return manager.sync_all(globs=globs, exclude_globs=exclude_globs, ocr=ocr)

    @server.tool()
    def sync_paths(
        paths: list[str],
        ocr: bool = False
    ) -> Any:
        """Extract content from specific document files.
        
        Args:
            paths: List of file paths to process
            ocr: Enable OCR for scanned PDFs
            
        Returns:
            Processing results for each file
        """
        return manager.sync_paths(paths, ocr=ocr)

    @server.tool()
    def get_text_path(
        src: str,
        ocr: bool = False
    ) -> Any:
        """Get the extracted Markdown path for a source document, ensuring extraction is complete.
        
        Args:
            src: Source document path (relative to repository root)
            ocr: Enable OCR for scanned PDFs
            
        Returns:
            Dictionary with the output Markdown file path
        """
        return manager.get_text_path(src, ocr=ocr)

    @server.tool()
    def list_kb() -> Any:
        """List all extracted documents in the knowledge base.
        
        Returns:
            Dictionary with list of available knowledge base items
        """
        return manager.list_kb()

    @server.tool()
    def purge_outputs(
        globs: list[str] | None = None
    ) -> Any:
        """Delete generated Markdown files to force re-extraction.
        
        Args:
            globs: File patterns to delete (default: all generated files)
            
        Returns:
            List of deleted files
        """
        return manager.purge_outputs(globs=globs)

    @server.tool()
    def config_get() -> Any:
        """Get current Escarabajo configuration.
        
        Returns:
            Current configuration settings
        """
        return manager.config_get()

    @server.tool()
    def config_set(
        updates: Optional[dict[str, Any]] = None
    ) -> Any:
        """Update Escarabajo configuration settings.
        
        Args:
            updates: Configuration settings to update
            
        Returns:
            Updated configuration
        """
        return manager.config_set(updates or {})

    @server.tool()
    def list_prompts() -> Any:
        """List available analysis prompt templates.
        
        Returns:
            Dictionary with available prompt names
        """
        return list_prompts()

    @server.tool()
    def get_prompt(
        name: str,
        params: Optional[dict[str, Any]] = None
    ) -> Any:
        """Get a specific analysis prompt template.
        
        Args:
            name: Name of the prompt template
            params: Optional parameters for the prompt template
            
        Returns:
            Dictionary with the prompt template
        """
        return get_prompt(name, params=params)

    @server.tool()
    def read_text(
        out: str,
        max_bytes: int | None = None
    ) -> Any:
        """Read content from an extracted Markdown file.
        
        Args:
            out: Path to the extracted Markdown file
            max_bytes: Maximum bytes to read (optional)
            
        Returns:
            Dictionary with file content and metadata
        """
        return manager.read_text(out, max_bytes=max_bytes)

    return server


__all__ = ["create_server", "EscarabajoServer"]

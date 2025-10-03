"""Module entry point for Escarabajo.

The module tries to launch a FastMCP stdio server when the dependency is
installed. Otherwise it falls back to a lightweight JSON-over-stdio loop that
mirrors the tool surface for local experimentation.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .cli import main as cli_main
from .server import EscarabajoServer, create_server


def _run_stdio(server: EscarabajoServer) -> None:
    """Very small JSON-over-stdio loop used when FastMCP is not available."""

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
            tool = request.get("tool")
            payload = request.get("payload")
            result = server.invoke(tool, payload)
            response = {"ok": True, "result": result}
        except Exception as exc:  # pragma: no cover
            response = {"ok": False, "error": str(exc)}
        sys.stdout.write(json.dumps(response) + "\n")
        sys.stdout.flush()


def entrypoint(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Escarabajo MCP server")
    parser.add_argument("--cli", action="store_true", help="Run the command line interface instead of the server")
    parser.add_argument("--repo", type=Path, help="Repository root (defaults to current working directory)")
    args, remaining = parser.parse_known_args(argv)

    if args.cli:
        return cli_main(list(remaining))

    repo_root = args.repo or Path.cwd()
    server = create_server(repo_root)
    # If FastMCP is available, prefer running it. We detect by attribute presence.
    if hasattr(server, "run"):
        server.run()  # type: ignore[attr-defined]
        return 0
    if hasattr(server, "serve"):
        server.serve()  # type: ignore[attr-defined]
        return 0
    _run_stdio(server)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(entrypoint())

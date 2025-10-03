"""Module entry point for Escarabajo.

By default this behaves like the CLI (`python -m Escarabajo sync`). Pass
`--mcp` to start the MCP server instead. The server prefers the FastMCP
implementation when installed and otherwise falls back to a lightweight
JSON-over-stdio loop for local experimentation.
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
    parser = argparse.ArgumentParser(description="Escarabajo entrypoint")
    parser.add_argument(
        "--mcp",
        action="store_true",
        help="Run the MCP server instead of the CLI",
    )
    parser.add_argument(
        "--repo",
        type=Path,
        help="Repository root (defaults to current working directory)",
    )
    args, remaining = parser.parse_known_args(argv)

    if not args.mcp:
        return cli_main(list(remaining))

    repo_root = args.repo or Path.cwd()
    server = create_server(repo_root)
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

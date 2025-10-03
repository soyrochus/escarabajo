# Escarabajo MCP Server

Escarabajo (Scarab) is a local-first MCP server that keeps binary documents in sync with clean Markdown so downstream agents can search, summarise, and reason over source material. Every tool call blocks until the requested Markdown exists and is up to date, making Escarabajo a reliable path oracle rather than a generic file store.

![Escarabajo logo](image/escarabajo-small.png)

## Highlights

- Deterministic `.Escarabajo/kb/` cache with one-to-one `<source> → <source>.md` mapping
- Synchronous extraction pipeline for DOCX, PPTX, and PDF (optional OCR) with per-file locks
- Provenance-rich `.Escarabajo/index.json` including hashes, mtimes, byte counts, and durations
- Respect for repo boundaries, `.gitignore`, and configurable glob/ignore patterns
- Prompt pack surface plus optional Markdown streaming (`read_text`) when `expose_content=true`

## Repository Layout

- `.Escarabajo/` – Generated workspace housing runtime config, index metadata, and cached Markdown outputs.
  - `config.yaml` – User-editable synchronization settings and feature flags.
  - `index.json` – Provenance ledger capturing hashes, mtimes, and extraction results.
  - `kb/<source>.md` – Canonical Markdown generated from each source binary.
- `Escarabajo/` – Python package providing the MCP server and CLI implementation.
  - `__main__.py` – Module entry point that boots the MCP server when invoked with `python -m`.
  - `cli.py` – Command-line interface wiring for local developer workflows.
  - `config.py` – Utilities for loading, validating, and persisting `.Escarabajo/config.yaml`.
  - `fsutil.py` – Filesystem helpers for hashing, atomic writes, and path normalization.
  - `indexdb.py` – Logic for reading and updating `.Escarabajo/index.json` atomically.
  - `prompts.py` – Registry of built-in MCP prompt templates exposed via `list_prompts`/`get_prompt`.
  - `server.py` – FastMCP tool registrations and request handling logic.
  - `sync.py` – Core synchronization workflows reused by CLI and MCP tools.
  - `extract/` – Format-specific adapters that convert DOCX, PPTX, and PDF assets to Markdown.
    - `docx.py` – DOCX extraction via Mammoth with Markdown normalization.
    - `pptx.py` – PowerPoint slide parsing and outline Markdown rendering.
    - `pdf.py` – PDF text extraction (PyMuPDF/pdfminer) with optional OCR annotations.
- `tests/` – Pytest suite validating extraction, sync behaviour, and MCP endpoints.
  - `test_mcp_tools.py` – Verifies tool surfaces and end-to-end sync flows.
  - `test_authoritative_fixtures.py` – Asserts authoritative Markdown outputs stay stable.
  - `mcp_client.py` – Lightweight MCP client harness used by the tests.
  - `data/` – Fixture documents (`.docx`, `.pptx`, `.pdf`) used during tests.
- `image/` – Project artwork including the Escarabajo logo assets.
- `pyproject.toml` – Build metadata, dependencies, and CLI entry points for the package.
- `uv.lock` – Pinned dependency resolution produced by `uv` for reproducible installs.
- `AGENTS.md` – Co-generation brief describing MCP behaviour and tooling expectations.
- `FOSS_PLURALISM_MANIFESTO.md` – Community guidelines and participation principles.
- `LICENSE` – MIT license text governing project usage and distribution.

## MCP Tool Surface

- `scan_repo` — discover eligible DOCX/PPTX/PDF files via glob
- `sync_all` — synchronise every discovered binary, overwriting Markdown by default
- `sync_paths` — synchronise explicit paths (relative or absolute inside the repo)
- `get_text_path` — ensure a single Markdown artefact is fresh and return its path
- `list_kb` — enumerate generated Markdown files in the knowledge base
- `purge_outputs` — delete generated Markdown to force a clean rebuild
- `config_get` / `config_set` — inspect or amend `.Escarabajo/config.yaml`
- `list_prompts` / `get_prompt` — expose the built-in prompt pack
- `read_text` — optionally stream Markdown content when `expose_content` is enabled

## CLI Quick Start

```bash
# Initialise the workspace (current directory)
escarabajo init
# or target a specific path
escarabajo init --path ./docs/project

# Install in editable mode (optionals shown)
uv pip install -e ".[pdf,ocr]"

# Scan for documents
escarabajo scan
# or: python -m Escarabajo scan

# Synchronise everything with OCR enabled for PDFs
escarabajo sync --ocr

# Synchronise specific files
escarabajo sync-paths docs/spec.docx slides/brief.pptx

# Return the Markdown path for an individual document
escarabajo get-path --src docs/spec.docx
```

## Configuration

`escarabajo config-get` prints the current configuration, which defaults to:

```yaml
kb_dir: ".Escarabajo/kb"
globs: ["**/*.docx", "**/*.pptx", "**/*.pdf"]
exclude_globs: [".git/**", ".Escarabajo/**", "node_modules/**", "**/~$*", "**/*.tmp"]
ocr: false
expose_content: false
skip_unchanged: false
pdf:
  page_delimiter: "--- page {n} ---"
pptx:
  slide_delimiter: "--- slide {n} ---"
docx:
  keep_tables: true
```

Set `skip_unchanged=true` to avoid redundant work (Escarabajo still overwrites by default) and flip `expose_content=true` when you want to serve Markdown bodies through the `read_text` tool.

## Running the Server

- `python -m Escarabajo --mcp` starts the MCP server (FastMCP when available, otherwise a lightweight JSON-over-stdio loop)
- `python -m Escarabajo <command>` or `escarabajo <command>` runs the CLI helpers directly (running with no command prints the CLI help)

## Testing

Populate `.Escarabajo/kb/` by syncing the authoritative fixtures (for example, run `escarabajo sync-paths ...` or `escarabajo sync`). Once the cache contains the Markdown outputs referenced by `.Escarabajo/index.json`, execute the test suite:

```bash
uv run pytest -q
```

The suite covers extraction adapters, mapping logic, sync behaviours, and the CLI surface.


## Principles of Participation

Everyone is invited and welcome to contribute: open issues, propose pull requests, share ideas, or help improve documentation.  
Participation is open to all, regardless of background or viewpoint.  

This project follows the [FOSS Pluralism Manifesto](./FOSS_PLURALISM_MANIFESTO.md),  
which affirms respect for people, freedom to critique ideas, and space for diverse perspectives.  


## License and Copyright

Copyright (c) 2025, Iwan van der Kleijn

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

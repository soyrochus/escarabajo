# “Escarabajo MCP Server” — Co-generation Prompt (paste this into your code-gen assistant)

**Role / Objective**

You are generating an **MCP server** named **Escarabajo** (a.k.a. Scarab) that guarantees **synchronous, correct extraction** of local repository documents into Markdown for downstream search/analysis.
The server does **not** act as a general file store. Its primary job is to **ensure the text artifacts exist and are up-to-date**, and to **hand back correct file paths**.

**Core Behavior**

1. **Workspace & cache layout**

   * Repo root contains a hidden directory: **`.Escarabajo/`**

     * **`.Escarabajo/kb/`** – canonical text outputs (Markdown)
     * **`.Escarabajo/index.json`** – mapping & metadata (see schema below)
     * **`.Escarabajo/config.yaml`** – config (globs, excludes, OCR, flags)
   * Mapping rule (deterministic, idempotent):
     `(<repo-relative path of source>)  ->  .Escarabajo/kb/<same path>.md`
     Examples:

     * `docs/spec.docx` → `.Escarabajo/kb/docs/spec.docx.md`
     * `slides/brief.pptx` → `.Escarabajo/kb/slides/brief.pptx.md`
     * `contracts/agreement.pdf` → `.Escarabajo/kb/contracts/agreement.pdf.md`
   * If you prefer a suffix dir like `ebk/`, make it configurable (`kb_dir: "kb"`).

2. **Supported inputs (initial)**

   * **Word** (`.docx`)
   * **PowerPoint** (`.pptx`)
   * **PDF** (`.pdf`) with optional OCR for scanned docs (config flag: `ocr: false`).

3. **Extraction policy (synchronous & authoritative)**

   * **Default behavior:** *Always re-extract and overwrite* the Markdown output for any file targeted by a sync operation. (Matches user requirement “It always overrides the text file”.)
   * Provide a **config flag** `skip_unchanged: false` to allow teams to avoid re-work in big repos (when `true`, only update if `src_mtime > out_mtime` or hash mismatch).
   * On any tool call that requests a path, ensure the corresponding Markdown exists **before** returning (perform extraction if missing/outdated). **Block until finished**.

4. **Index & metadata**

   * Maintain `.Escarabajo/index.json` (pretty-printed, UTF-8) with entries:

     ```json
     {
       "version": 1,
       "generated_at": "ISO-8601",
       "kb_dir": ".Escarabajo/kb",
       "files": [
         {
           "src": "docs/spec.docx",
           "out": ".Escarabajo/kb/docs/spec.docx.md",
           "status": "ok|error|skipped",
           "reason": "string or null",
           "src_mtime": "ISO-8601",
           "out_mtime": "ISO-8601",
           "src_sha256": "hex",
           "out_sha256": "hex",
           "bytes_in": 12345,
           "bytes_out": 6789,
           "duration_ms": 321
         }
       ]
     }
     ```
   * Hashing can be skipped if `skip_unchanged=false` (always overwrite), but still store `src_sha256`/`out_sha256` for auditability.

5. **Security & scope**

   * Operate **only within the current repo** (no parent paths; reject path traversal).
   * Respect `.gitignore` by default and a local ignore list in config (`exclude_globs`).
   * No network. No uploading.

6. **Quality rules**

   * Markdown should be clean and stable: extract headings, paragraphs, lists, tables; preserve slide/page boundaries with clear markers (e.g., `--- slide 3 ---` / `--- page 5 ---`).
   * For PDFs, attempt layout-aware extraction; when OCR is on, clearly annotate the output (front-matter or header note).
   * Idempotent runs produce the same outputs for unchanged inputs.

---

**MCP Surface (tools & prompts)**

Implement the following **tools**:

1. `scan_repo`

   * **Purpose:** find candidate binaries by glob.
   * **Inputs:** `{ globs?: string[]; exclude_globs?: string[] }`
   * **Defaults:** `globs=["**/*.docx","**/*.pptx","**/*.pdf"]`, `exclude_globs=[".git/**",".Escarabajo/**","node_modules/**","**/~$*","**/*.tmp"]`
   * **Returns:** list of `{ src: string }`.

2. `sync_all`

   * **Purpose:** ensure *all* discovered binaries are extracted (overwrite per policy).
   * **Inputs:** `{ globs?: string[]; exclude_globs?: string[]; ocr?: boolean }`
   * **Returns:** summary `{ processed: number, ok: number, skipped: number, errors: number, out_paths: string[] }`.

3. `sync_paths`

   * **Purpose:** extract specific files (absolute/relative repo paths).
   * **Inputs:** `{ paths: string[]; ocr?: boolean }`
   * **Returns:** `{ results: Array<{ src:string, out:string, status:string, reason?:string }> }`.

4. `get_text_path`

   * **Purpose:** guarantee the Markdown exists for one source and return its **path**.
   * **Inputs:** `{ src: string }`
   * **Behavior:** performs extraction if needed (or always, per policy), then returns `{ out: string }`.

5. `list_kb`

   * **Purpose:** list all known Markdown outputs in `.Escarabajo/kb`.
   * **Inputs:** `{ }`
   * **Returns:** `{ items: Array<{ out:string, src?:string }> }`.

6. `purge_outputs`

   * **Purpose:** delete generated Markdown (or subtrees) to force a clean rebuild.
   * **Inputs:** `{ globs?: string[] }`
   * **Returns:** `{ deleted: string[] }`.

7. `config_get` / `config_set`

   * **Purpose:** read/update `.Escarabajo/config.yaml`.
   * **Schema (YAML):**

     ```yaml
     kb_dir: ".Escarabajo/kb"
     globs: ["**/*.docx","**/*.pptx","**/*.pdf"]
     exclude_globs: [".git/**",".Escarabajo/**","node_modules/**","**/~$*","**/*.tmp"]
     ocr: false
     expose_content: false
     skip_unchanged: false
     pdf:
       keep_figures_as_captions: true
       page_delimiter: "--- page {n} ---"
     pptx:
       slide_delimiter: "--- slide {n} ---"
     docx:
       keep_tables: true
     ```
   * `config_set` takes a partial update.

8. *(Optional, off by default)* `read_text`

   * **Purpose:** return the **contents** of a generated Markdown (size-capped).
   * **Inputs:** `{ out: string, max_bytes?: number }`
   * **Returns:** `{ content: string }` (truncate if `> max_bytes`, indicate truncation).
   * Only enabled when `expose_content=true`.

**Prompt Pack (served by MCP)**

Provide a `list_prompts` and `get_prompt` tool so clients can fetch standard prompts.

* `list_prompts` → returns `{ names: string[] }`.
* `get_prompt` → inputs `{ name: string, params?: object }`, returns `{ template: string }`.

Seed with these (parameterized with handlebars-style `{{ }}`):

* `doc.summarize`
  “You are extracting a precise summary of **{{path}}**. Produce: TL;DR (5 bullets), key sections with one-line takeaways, and a list of open questions. Quote sparingly; prefer paraphrase.”

* `doc.extract_requirements`
  “From **{{path}}**, list functional requirements, non-functional requirements, constraints, and explicit acceptance criteria. Output in Markdown tables.”

* `ppt.to_outline`
  “Turn **{{path}}** into a clean outline: per slide → heading + 1-3 bullets; capture any speaker notes as italicized sub-bullets.”

* `pdf.policy_risk`
  “Inspect **{{path}}** for policy or compliance risks. Return a table: section/page • risk • severity • rationale • suggested mitigation.”

* `kb.crosslink`
  “Given these paths:\n{{#each paths}}- {{this}}\n{{/each}}\nPropose cross-links (related sections) and a consolidated index.md with anchors.”

---

Got it—here’s a tight, implementation-ready **technical description** for your Python MCP server.

# Escarabajo (Escarabajo MCP Server) — Technical Specification

## Purpose

Escarabajo is an **MCP server (Python, FastMCP)** whose sole responsibility is to **synchronize binary documents** in the local repo (DOCX, PPTX, PDF) into canonical **Markdown** under a hidden workspace, and **return correct paths** to those text artifacts for agent consumption.
It **does not** stream binary payloads to clients; it guarantees that **the Markdown exists and is current**, then returns **paths**.

## Responsibilities

* Discover candidate source files (glob).
* Extract/normalize to Markdown (deterministic mapping) **synchronously**.
* Always overwrite the Markdown by default (configurable).
* Maintain an **index.json** with provenance and audit fields.
* Expose a compact MCP tool surface + a prompt pack.
* Provide a simple **console utility** (same module) for local usage and CI.

Out of scope: embeddings/RAG, network I/O, remote storage.

---

## On-disk layout (repo-relative)

```
.escarabajo/
  config.yaml           # user-editable configuration
  index.json            # provenance & audit
  kb/                   # canonical Markdown outputs
```

**Mapping rule (idempotent):**

```
<repo_rel_src_path> → .escarabajo/kb/<repo_rel_src_path>.md
# e.g.
docs/spec.docx       → .escarabajo/kb/docs/spec.docx.md
slides/brief.pptx    → .escarabajo/kb/slides/brief.pptx.md
contracts/agreement.pdf → .escarabajo/kb/contracts/agreement.pdf.md
```

---

## Synchronization policy

* **Default:** `always_overwrite = true` (extract every time a tool needs a path).
* Optional: `skip_unchanged = true` (extract only if `src_mtime > out_mtime` or hash diff).
* Extraction is **blocking/synchronous**—MCP reply only after output exists.
* Concurrency safety with per-file **advisory locks** (avoid racey double–extract).

---

## Configuration (`.escarabajo/config.yaml`)

```yaml
kb_dir: ".escarabajo/kb"
globs: ["**/*.docx","**/*.pptx","**/*.pdf"]
exclude_globs: [".git/**",".escarabajo/**","node_modules/**","**/~$*","**/*.tmp"]
ocr: false                 # enable Tesseract on scanned PDFs (optional)
always_overwrite: true     # default behavior
skip_unchanged: false      # ignored if always_overwrite=true
pdf:
  page_delimiter: "--- page {n} ---"
pptx:
  slide_delimiter: "--- slide {n} ---"
docx:
  keep_tables: true
expose_content: false      # when false, server returns PATHS only (recommended)
```

---

## Index schema (`.escarabajo/index.json`)

```json
{
  "version": 1,
  "generated_at": "ISO-8601",
  "kb_dir": ".escarabajo/kb",
  "files": [
    {
      "src": "docs/spec.docx",
      "out": ".escarabajo/kb/docs/spec.docx.md",
      "status": "ok|error|skipped",
      "reason": "string|null",
      "src_mtime": "ISO-8601",
      "out_mtime": "ISO-8601",
      "src_sha256": "hex",
      "out_sha256": "hex",
      "bytes_in": 12345,
      "bytes_out": 6789,
      "duration_ms": 321
    }
  ]
}
```

Write via **atomic temp-file + rename**.

---

## Extraction adapters (Python)

* **DOCX → Markdown**: `mammoth` (DOCX→HTML) → `markdownify` or `turndown-py` equivalent pass.
* **PPTX → Markdown**: `python-pptx` (collect text boxes/notes) → slide section with bullet points, using `slide_delimiter`.
* **PDF → Markdown**: prefer **PyMuPDF (fitz)** for speed/accuracy; fallback `pdfminer.six`.
  **OCR (optional)**: `pytesseract` + system `tesseract-ocr` when `ocr: true`. Annotate OCR in output header.
* Normalize whitespace, preserve headings/tables where feasible, mark slide/page boundaries.

---

## MCP Tool surface (Python FastMCP)

For FastMCP seeÑ https://gofastmcp.com/llms.txt . Interface below uses JSON-serializable payloads and simple validation.

1. **`scan_repo`**
   **Input**: `{ globs?: string[], exclude_globs?: string[] }`
   **Return**: `{ items: Array<{ src: string }> }`

2. **`sync_all`**
   **Input**: `{ globs?: string[], exclude_globs?: string[], ocr?: boolean }`
   **Return**: `{ processed: number, ok: number, skipped: number, errors: number, out_paths: string[] }`

3. **`sync_paths`**
   **Input**: `{ paths: string[], ocr?: boolean }`
   **Return**: `{ results: Array<{ src: string, out: string, status: string, reason?: string }> }`

4. **`get_text_path`**
   **Input**: `{ src: string }`
   **Behavior**: ensures extraction per policy.
   **Return**: `{ out: string }`

5. **`list_kb`**
   **Input**: `{}`
   **Return**: `{ items: Array<{ out: string, src?: string }> }`

6. **`purge_outputs`**
   **Input**: `{ globs?: string[] }` (defaults to `**/*.md`)
   **Return**: `{ deleted: string[] }`

7. **`config_get` / `config_set`**
   `config_get`→ returns resolved config.
   `config_set` (partial update) **Input**: any subset of config fields → returns new config.

8. **`list_prompts` / `get_prompt`**
   Prompt names: `doc.summarize`, `doc.extract_requirements`, `ppt.to_outline`, `pdf.policy_risk`, `kb.crosslink`.
   `get_prompt` returns `{ template: string }` with `{{param}}` placeholders.

9. *(Optional, off by default)* **`read_text`**
   Only if `expose_content=true`.
   **Input**: `{ out: string, max_bytes?: number }` → `{ content: string, truncated: boolean }`.

**Security**: reject path traversal; operate strictly repo-relative; respect `.gitignore` + `exclude_globs`.

---

## Package & runtime

### Module & entrypoints

* **Distribution name**: `Escarabajo`
* **Python module**: `Escarabajo/`
* **Console script**: `Escarabajo` (CLI wrapper)
* **`__main__.py`**: `python -m Escarabajo` starts the **MCP server** by default
  `Escarabajo` (console) exposes local ops: `scan`, `sync`, `get-path`, `list-kb`, `purge`, `config-get`, `config-set`, `prompts`.

### Suggested CLI (posix-friendly)

```
escarabajo scan --globs "**/*.docx" "**/*.pdf"
escarabajo sync --ocr
Escarabajo get-path --src docs/spec.docx
escarabajo list-kb
escarabajo purge --globs "**/legacy/*.md"
escarabajo config-get
escarabajo config-set --set always_overwrite=false --set skip_unchanged=true
escarabajo prompts --list
escarabajo prompts --get ppt.to_outline
```

### Logging & exit codes

* **stderr**: structured JSON lines (level, ts, event, fields).
* **stdout**: concise human messages for CLI.
* Exit codes: `0` success; `1` generic error; `2` bad args; `3` partial failures (some files error).

### Concurrency

* Per-output **file locks** (`filelock`) to serialize extraction for the same `src`.
* Global lock (`.escarabajo/.lock`) to serialize index writes.

---

## Dependency & build (uv)

> **Note:** `uv` and PEP 621 expect **`pyproject.toml`**, not YAML. If you truly need a YAML file for other tooling, keep it separate; dependency metadata for `uv` must live in TOML.

**`pyproject.toml` (essentials)**

```toml
[project]
name = "Escarabajo"
version = "0.1.0"
description = "Escarabajo MCP server: repo doc sync (DOCX/PPTX/PDF) to Markdown + path oracle."
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
  "mcp[server]",         # FastMCP / MCP server package (xxx)
  "pyyaml>=6",
  "pathspec>=0.12",
  "filelock>=3.14",
  "pymupdf>=1.24",       # PDF fast path
  "pdfminer.six>=20231228",  # fallback
  "mammoth>=1.6.0",      # DOCX -> HTML
  "markdownify>=0.12.1", # HTML -> Markdown
  "python-pptx>=0.6.23", # PPTX
  "rich>=13.7"           # nice CLI output (optional)
]

[project.optional-dependencies]
ocr = ["pytesseract>=0.3.10"]

[project.scripts]
Escarabajo = "Escarabajo.cli:main"

[tool.uv]  # uv-specific (lock, resolver behavior etc. if needed)
```

**Common uv flows**

```
uv venv
uv pip install -e ".[ocr]"     # with OCR extras (optional)
uv run Escarabajo --help
uv run python -m Escarabajo      # start MCP server (stdio)
```

---

## Code organization

```
Escarabajo/
  __init__.py
  __main__.py          # starts MCP server (stdio)
  server.py            # FastMCP wiring: tool defs, schemas, handlers
  cli.py               # argparse/typer CLI wrappers → call same handlers
  config.py            # load/save/validate .escarabajo/config.yaml
  fsutil.py            # atomic write, hashes, locks, path mapping
  indexdb.py           # load/save index.json, upsert entries
  extract/
    __init__.py
    docx.py            # mammoth + markdownify
    pptx.py            # python-pptx
    pdf.py             # PyMuPDF / pdfminer; optional OCR
  prompts.py           # prompt pack, list/get
  tools/               # thin adapters from MCP tool call → core ops
tests/
  conftest.py
  test_mapping.py
  test_extract_docx.py
  test_extract_pptx.py
  test_extract_pdf.py
  test_sync_paths.py
  test_cli.py
.escarabajo/
  config.yaml          # generated at first run
README.md
```

---

## Testing (PyTest)

* **Unit**

  * `test_mapping.py`: `src → kb/src.md` mapping; path normalization.
  * `test_extract_*`: golden Markdown for fixture docs; stable delimiters.
  * `test_sync_paths.py`: overwrite vs skip_unchanged; index.json content; locking.
  * `test_cli.py`: commands return expected JSON/exit codes.
* **Fixtures**: tiny `.docx/.pptx/.pdf` in `tests/data/`.
* **Run**: `uv run pytest -q`

**CI knobs** (generic runner):

* Install system `tesseract-ocr` if `ocr` tests enabled; otherwise skip with marker.
* Matrix Python `3.11`/`3.12`.

---

## MCP startup behaviors

* On boot, ensure `.escarabajo/config.yaml` exists (write defaults if missing).
* Tool calls resolve **repo root = CWD**; reject absolute paths and `..` traversal.
* For `get_text_path`, **perform extraction** (respecting policy) before returning the path.

---

## Prompt pack (initial)

* `doc.summarize`, `doc.extract_requirements`, `ppt.to_outline`, `pdf.policy_risk`, `kb.crosslink`
  Templates use `{{}}` placeholders; delivered via `list_prompts` / `get_prompt`.

---

## Security & compliance

* No network calls; strictly local FS.
* Path whitelisting and traversal guards.
* JSON & YAML parsing hardened (safe loaders).
* Deterministic, audit-friendly outputs + hashes.

---

## Performance notes

* Prefer PyMuPDF for PDFs; fallback to pdfminer if unavailable.
* Batch operations stream files; avoid loading huge files wholly where possible.
* Use file hashing only when `skip_unchanged=true` to avoid extra I/O by default.

---

## Example flows

**From an agent (MCP):**

1. `get_text_path { "src": "docs/spec.docx" }`
   → server extracts and returns `{ "out": ".escarabajo/kb/docs/spec.docx.md" }`.

**From terminal (developer):**

```
Escarabajo sync --globs "**/*.docx" "**/*.pptx" "**/*.pdf"
Escarabajo get-path --src slides/brief.pptx
```

---

If you want, I can also produce a **scaffolded repo layout** text (README, config, test skeletons, CLI help) directly from this spec for your co-gen agent to follow 1:1.


**Error Handling**

* Return clear `status` & `reason` per file; never partially update `index.json`—write to a temp file and atomic-move.
* If a tool call fails mid-batch, include per-file statuses and a top-level `errors` count.

---

**Acceptance Criteria**

* Calling `get_text_path {src:"docs/spec.docx"}`:

  * Creates `.Escarabajo/kb/docs/spec.docx.md` (overwriting by default),
  * Updates `index.json`,
  * Returns `{ out: ".Escarabajo/kb/docs/spec.docx.md" }`.

* `sync_all` on a repo with 10 mixed files returns correct counts and makes all `.md` files present.

* `list_kb` yields only paths under `.Escarabajo/kb` (never raw binary paths).

* When `expose_content=false`, trying `read_text` yields a clear “disabled by config” error.

---


## README

Write an elaborate README. Include the logo (image/escarabajo.png)

Add all content *above* the existing content in the README (above "## Principles of Participation")

**Non-Goals**

* No embedding/vectorization, no RAG, no network calls.
* No binary streaming by default; the server is a **synchronizer + path oracle**.

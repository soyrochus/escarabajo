# Document Generation Guide (Escarabajo)

## Purpose

This guide explains how to create project documentation with Escarabajo while keeping the workflow lightweight. Once the knowledge base is refreshed, you only need two inputs—`list-kb` results and the relevant source files—to produce trustworthy, human-readable docs.

## Keep the Knowledge Base Fresh

1. From the repository root, run the Escarabajo CLI sync command:

   ```bash
   uv run Escarabajo sync
   ```

   This forcibly re-extracts every supported DOCX, PPTX, and PDF file and refreshes `.Escarabajo/kb/` plus the index metadata. Because the CLI always overwrites stale outputs, you can rely on the Markdown snapshots without any extra scripting.

2. Escarabajo also exposes commands such as `scan`, `sync-paths`, `get-path`, and more. They exist for completeness—reach for them when you have a niche need—but a simple `sync` before writing keeps the knowledge base accurate in most situations.

## Discover Available Knowledge

After syncing, list the generated Markdown entries:

```bash
uv run Escarabajo list-kb --json
```

- The output enumerates every `.Escarabajo/kb/**` file.
- Open the returned Markdown paths directly in your editor; no custom utilities are required.
- When `expose_content=true`, you may also preview content via `uv run Escarabajo read-text --out <path>`, though direct file access is usually simpler for authoring.

At this point you have everything you need: canonical document extracts and the project’s source code. Avoid layering bespoke clients—the CLI already guarantees an up-to-date knowledge base.

## Build from Source Code and KB Markdown

1. Review the code that implements the behaviour you’re documenting (for example `tests/random_app.py`).
2. Cross-reference KB Markdown for requirements, philosophy, and user guidance. Common RNGenius files include:

   - `.Escarabajo/kb/tests/data/RNGenius_Functional_Spec.docx.md`
   - `.Escarabajo/kb/tests/data/RNGenius_Philosophy.pptx.md`
   - `.Escarabajo/kb/tests/data/RNGenius_User_Manual.pdf.md`

3. Capture any code or spec deltas introduced by your change so the write-up reflects reality.

## Recommended Document Layout

Follow the structure used in [`example_random_app_documentation.md`](tests/example_random_app_documentation.md), keeping the functional story first and the technical analysis second.

```markdown
# <Document Title>

## Functional Narrative
- Purpose and business context
- Requirements table (spec item → implementation cue)
- Rituals or workflows derived from philosophy docs
- Guardrails and user guidance
- Onboarding flow (numbered list)

## Technical Deep Dive
- Module snapshot (file, entry point, dependencies, numeric ranges)
- UI composition (ordered list describing key widgets/areas)
- Core engine notes (randomness, state, data flow)
- Supporting systems (clipboard, confetti, persistence)
- Accessibility & delight mechanics (bullet list)
- Integration hooks and extension tips
- Document provenance (list KB files consulted)
```

Keeping this template handy clarifies where to slot functional signals versus deeper engineering notes.

## Example Prompt for Co-Generation

When you need another documentation artifact, anchor the assistant with a prompt like:

> Create the documentation as `example_random_app_documentation.md` using only the `list_kb` tools. Access the returned files directly. Add the information from the files directly (access the files in the project directory). Incorporate the functional/philosophical message from the context into the documentation. Separate a functional part (first) from a more detailed technical part (second).

The wording reinforces the minimal-tool philosophy: rely on the KB output and the source code, not on custom scripts or broad Escarabajo calls.

## When to Reach for Other Tools (Optional)

Escarabajo’s full command set—`scan`, `sync-paths`, `get-path`, `prompts`, and friends—remains available for specialised tasks (partial rebuilds, prompt inspection, automation). Use them when necessary, but remember they’re optional once the CLI sync has run.

## Writing Tips

- **Stay human:** explain why decisions matter before describing how the code works.
- **Trace requirements:** for every functional requirement, point to the class or method that satisfies it.
- **Reuse headings:** consistent section names make future updates and reviews easier.
- **Cite sources:** list the KB Markdown files you referenced so reviewers can verify linkage quickly.
- **Refresh before you write:** make `uv run Escarabajo sync` part of your documentation routine to avoid stale content.

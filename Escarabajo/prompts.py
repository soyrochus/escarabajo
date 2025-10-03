"""Prompt pack exposed by the Escarabajo MCP server."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Match

import re

PROMPTS: Dict[str, str] = {
    "doc.summarize": (
        "You are extracting a precise summary of **{{path}}**. Produce: TL;DR (5 bullets), "
        "key sections with one-line takeaways, and a list of open questions. Quote sparingly; "
        "prefer paraphrase."
    ),
    "doc.extract_requirements": (
        "From **{{path}}**, list functional requirements, non-functional requirements, constraints, "
        "and explicit acceptance criteria. Output in Markdown tables."
    ),
    "ppt.to_outline": (
        "Turn **{{path}}** into a clean outline: per slide → heading + 1-3 bullets; capture any "
        "speaker notes as italicized sub-bullets."
    ),
    "pdf.policy_risk": (
        "Inspect **{{path}}** for policy or compliance risks. Return a table: section/page • risk • "
        "severity • rationale • suggested mitigation."
    ),
    "kb.crosslink": (
        "Given these paths:\n{{#each paths}}- {{this}}\n{{/each}}\nPropose cross-links (related sections) and a consolidated index.md with anchors."
    ),
}


def list_prompts() -> Dict[str, List[str]]:
    return {"names": sorted(PROMPTS)}


EACH_PATTERN = re.compile(r"{{#each (\w+)}}(.*?){{/each}}", re.DOTALL)


def _render_template(template: str, params: Dict[str, Any]) -> str:
    """Render a minimal subset of Handlebars-style templates."""

    def each_repl(match: Match[str]) -> str:
        key = match.group(1)
        body = match.group(2)
        items = params.get(key, [])
        if not isinstance(items, list):
            return ""
        rendered_items = []
        for item in items:
            item_str = str(item)
            rendered_body = body.replace("{{this}}", item_str)
            rendered_body = _render_template(rendered_body, params)
            rendered_items.append(rendered_body)
        return "".join(rendered_items)

    rendered = EACH_PATTERN.sub(each_repl, template)

    for key, value in params.items():
        placeholder = f"{{{{{key}}}}}"
        rendered = rendered.replace(placeholder, str(value))

    return rendered


def get_prompt(name: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, str]:
    if name not in PROMPTS:
        raise KeyError(f"Unknown prompt '{name}'")
    template = PROMPTS[name]
    if params:
        template = _render_template(template, params)
    return {"template": template}


__all__ = ["list_prompts", "get_prompt", "PROMPTS"]

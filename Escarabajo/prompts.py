"""Prompt pack exposed by the Escarabajo MCP server."""

from __future__ import annotations

from typing import Dict, List

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


def get_prompt(name: str) -> Dict[str, str]:
    if name not in PROMPTS:
        raise KeyError(f"Unknown prompt '{name}'")
    return {"template": PROMPTS[name]}


__all__ = ["list_prompts", "get_prompt", "PROMPTS"]

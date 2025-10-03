"""PPTX extraction utilities."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List
from zipfile import ZipFile


NAMESPACES = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
}


def _slide_text(xml: bytes) -> List[str]:
    root = ET.fromstring(xml)
    texts: List[str] = []
    for node in root.findall(".//a:t", NAMESPACES):
        if node.text and node.text.strip():
            texts.append(node.text.strip())
    return texts


def extract_pptx(path: Path, options: Dict[str, object] | None = None) -> str:
    options = options or {}
    delimiter_template = str(options.get("slide_delimiter", "--- slide {n} ---"))

    with ZipFile(path) as archive:
        slide_names = sorted(
            [name for name in archive.namelist() if name.startswith("ppt/slides/slide") and name.endswith(".xml")]
        )
        if not slide_names:
            return ""
        lines: List[str] = []
        for index, name in enumerate(slide_names, start=1):
            slide_text = _slide_text(archive.read(name))
            if not slide_text:
                continue
            lines.append(delimiter_template.format(n=index))
            for item in slide_text:
                lines.append(f"- {item}")
    if not lines:
        return ""
    return "\n".join(lines).strip() + "\n"


__all__ = ["extract_pptx"]

"""DOCX extraction utilities."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List
from zipfile import ZipFile


NAMESPACES = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
}


def _paragraph_text(paragraph: ET.Element) -> str:
    texts: List[str] = []
    for node in paragraph.findall(".//w:t", NAMESPACES):
        if node.text:
            texts.append(node.text)
    return "".join(texts).strip()


def _paragraph_style(paragraph: ET.Element) -> str | None:
    style = paragraph.find("w:pPr/w:pStyle", NAMESPACES)
    if style is not None:
        return style.get(f"{{{NAMESPACES['w']}}}val")
    return None


def _is_list_item(paragraph: ET.Element) -> bool:
    return paragraph.find("w:pPr/w:numPr", NAMESPACES) is not None


def _extract_table(table: ET.Element) -> str:
    rows: List[List[str]] = []
    for tr in table.findall("w:tr", NAMESPACES):
        row: List[str] = []
        for tc in tr.findall("w:tc", NAMESPACES):
            text_parts: List[str] = []
            for paragraph in tc.findall("w:p", NAMESPACES):
                text = _paragraph_text(paragraph)
                if text:
                    text_parts.append(text)
            row.append("<br/>".join(text_parts))
        rows.append(row)
    if not rows:
        return ""
    col_count = max(len(r) for r in rows)
    for row in rows:
        row.extend([""] * (col_count - len(row)))
    header = rows[0]
    align = ["---" for _ in header]
    lines = ["| " + " | ".join(header) + " |", "| " + " | ".join(align) + " |"]
    for row in rows[1:]:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def extract_docx(path: Path, options: Dict[str, object] | None = None) -> str:
    options = options or {}
    keep_tables = bool(options.get("keep_tables", True))

    with ZipFile(path) as archive:
        try:
            xml_data = archive.read("word/document.xml")
        except KeyError as exc:
            raise ValueError("DOCX is missing word/document.xml") from exc

    root = ET.fromstring(xml_data)
    body = root.find("w:body", NAMESPACES)
    if body is None:
        return ""

    lines: List[str] = []
    for element in body:
        tag = element.tag.split("}")[-1]
        if tag == "p":
            text = _paragraph_text(element)
            if not text:
                continue
            style = _paragraph_style(element) or ""
            if style.startswith("Heading"):
                suffix = style[len("Heading"):]
                try:
                    level = int(suffix or "1")
                except ValueError:
                    level = 1
                level = max(1, min(level, 6))
                lines.append(f"{'#' * level} {text}")
            elif _is_list_item(element):
                lines.append(f"- {text}")
            else:
                lines.append(text)
        elif tag == "tbl" and keep_tables:
            table_md = _extract_table(element)
            if table_md:
                lines.append(table_md)
        else:
            continue
    return "\n\n".join(lines).strip() + "\n"


__all__ = ["extract_docx"]

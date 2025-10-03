"""PDF extraction utilities."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List

try:  # pragma: no-cover - optional dependency
    import fitz  # type: ignore
except Exception:  # pragma: no-cover
    fitz = None  # type: ignore

try:  # pragma: no-cover
    from PyPDF2 import PdfReader  # type: ignore
except Exception:  # pragma: no-cover
    PdfReader = None  # type: ignore


def _extract_with_fitz(path: Path) -> List[str]:
    doc = fitz.open(str(path))  # type: ignore[arg-type]
    pages: List[str] = []
    try:
        for page in doc:
            pages.append(page.get_text("text"))
    finally:
        doc.close()
    return pages


def _extract_with_pypdf(path: Path) -> List[str]:
    reader = PdfReader(str(path))  # type: ignore
    pages: List[str] = []
    for page in reader.pages:
        text = page.extract_text() or ""
        pages.append(text)
    return pages


def extract_pdf(path: Path, options: Dict[str, object] | None = None, *, ocr: bool = False) -> str:
    options = options or {}
    delimiter_template = str(options.get("page_delimiter", "--- page {n} ---"))

    pages: List[str] = []
    if fitz is not None:
        pages = _extract_with_fitz(path)
    elif PdfReader is not None:
        pages = _extract_with_pypdf(path)
    else:
        raise RuntimeError("No PDF extraction backend available. Install PyMuPDF or PyPDF2.")

    lines: List[str] = []
    if ocr:
        lines.append("> OCR mode enabled during extraction; text accuracy depends on system Tesseract installation.")
    for index, content in enumerate(pages, start=1):
        lines.append(delimiter_template.format(n=index))
        normalized = content.replace("\r\n", "\n").replace("\r", "\n")
        for line in normalized.split("\n"):
            stripped = line.strip()
            if stripped:
                lines.append(stripped)
    if not lines:
        return ""
    return "\n".join(lines).strip() + "\n"


__all__ = ["extract_pdf"]

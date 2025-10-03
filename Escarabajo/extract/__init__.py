"""Extraction front-door for various document types."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from . import docx as docx_adapter
from . import pdf as pdf_adapter
from . import pptx as pptx_adapter


SUPPORTED_TYPES = {".docx", ".pptx", ".pdf"}


def extract_to_markdown(src: Path, config: Dict[str, Any], *, ocr: bool | None = None) -> str:
    """Dispatch extraction based on file extension."""

    ext = src.suffix.lower()
    if ext not in SUPPORTED_TYPES:
        raise ValueError(f"Unsupported file type: {ext}")
    effective_ocr = ocr if ocr is not None else bool(config.get("ocr", False))
    if ext == ".docx":
        return docx_adapter.extract_docx(src, config.get("docx", {}))
    if ext == ".pptx":
        return pptx_adapter.extract_pptx(src, config.get("pptx", {}))
    return pdf_adapter.extract_pdf(src, config.get("pdf", {}), ocr=effective_ocr)


__all__ = ["extract_to_markdown", "SUPPORTED_TYPES"]

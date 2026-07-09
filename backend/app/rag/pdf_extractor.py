"""PDF text extraction using PyMuPDF (fitz)."""

import logging
from pathlib import Path

import fitz  # PyMuPDF

logger = logging.getLogger(__name__)


def extract_text_by_page(pdf_path: str | Path) -> list[dict]:
    """Extract text from each page of a PDF.

    Returns:
        List of dicts: [{"page_number": int, "text": str}, ...]
    """
    pages = []
    try:
        doc = fitz.open(str(pdf_path))
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text = page.get_text("text").strip()
            if text:
                pages.append({"page_number": page_num + 1, "text": text})
        doc.close()
        logger.info("Extracted %d pages from %s", len(pages), pdf_path)
    except Exception as exc:
        logger.error("PDF extraction failed for %s: %s", pdf_path, exc)
        raise
    return pages


def get_page_count(pdf_path: str | Path) -> int:
    """Return the total number of pages in a PDF."""
    doc = fitz.open(str(pdf_path))
    count = len(doc)
    doc.close()
    return count

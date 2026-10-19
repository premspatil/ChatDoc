"""Step 1 of RAG: read a PDF and return its text page by page (page numbers preserved)."""
from dataclasses import dataclass

import pymupdf  # PyMuPDF


class PDFProcessingError(Exception):
    """Raised when a PDF cannot be opened or read. The message is safe to show to users."""


@dataclass(frozen=True)
class PageText:
    page_number: int  # 1-based, same as the page numbers a human sees
    text: str


def _open(source):
    try:
        if isinstance(source, (bytes, bytearray)):
            doc = pymupdf.open(stream=bytes(source), filetype="pdf")
        else:
            doc = pymupdf.open(str(source))
    except Exception as exc:  # noqa: BLE001 - PyMuPDF raises several error types
        raise PDFProcessingError("This file could not be read as a PDF.") from exc
    if doc.needs_pass:
        doc.close()
        raise PDFProcessingError("This PDF is password-protected. Remove the password and try again.")
    return doc


def get_page_count(source) -> int:
    """Open the PDF just to count pages. Also proves the file is a readable PDF."""
    doc = _open(source)
    try:
        return doc.page_count
    finally:
        doc.close()


def extract_pages(source) -> list[PageText]:
    """Return one PageText per page that contains text. `source` is a path or raw bytes."""
    doc = _open(source)
    try:
        pages = []
        for index in range(doc.page_count):
            text = doc.load_page(index).get_text("text").strip()
            if text:
                pages.append(PageText(page_number=index + 1, text=text))
        return pages
    finally:
        doc.close()

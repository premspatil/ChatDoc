"""Step 2 of RAG: cut page text into overlapping chunks that fit an embedding model."""
import re
from dataclasses import dataclass

from .pdf_processor import PageText


@dataclass(frozen=True)
class Chunk:
    page_number: int
    chunk_index: int  # position inside the whole document (0, 1, 2, ...)
    text: str


def chunk_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    """Split text into pieces of at most `chunk_size` characters.

    Neighbouring pieces share `overlap` characters so a sentence cut at the edge
    still appears whole in one of them. We try to cut at a space, not mid-word.
    """
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than 0")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must be >= 0 and smaller than chunk_size")

    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return []
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        if end < len(text):
            cut = text.rfind(" ", start + int(chunk_size * 0.6), end)
            if cut != -1:
                end = cut
        piece = text[start:end].strip()
        if piece:
            chunks.append(piece)
        if end >= len(text):
            break
        next_start = end - overlap
        start = next_start if next_start > start else end  # always move forward
    return chunks


def chunk_pages(pages: list[PageText], chunk_size: int, overlap: int) -> list[Chunk]:
    """Chunk every page separately so each chunk knows exactly which page it came from."""
    chunks: list[Chunk] = []
    for page in pages:
        for piece in chunk_text(page.text, chunk_size, overlap):
            chunks.append(Chunk(page_number=page.page_number, chunk_index=len(chunks), text=piece))
    return chunks

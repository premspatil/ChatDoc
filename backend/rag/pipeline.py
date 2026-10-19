"""The two public entry points of the RAG package.

index_document(...)  - used after upload
answer_question(...) - used by the chat API
"""
import logging

from django.conf import settings

from . import embeddings, llm_service, prompts, retriever, vector_store
from .chunking import chunk_pages
from .pdf_processor import extract_pages

logger = logging.getLogger(__name__)


class NoExtractableTextError(Exception):
    """The PDF opened fine but has no text (probably scanned images)."""


def index_document(document_id: int, owner_id: int, pdf_path) -> int:
    """Extract -> chunk -> embed -> store in ChromaDB. Returns the number of chunks."""
    pages = extract_pages(pdf_path)
    chunks = chunk_pages(pages, settings.CHUNK_SIZE, settings.CHUNK_OVERLAP)
    if not chunks:
        raise NoExtractableTextError()

    vectors = embeddings.embed_texts([c.text for c in chunks])
    vector_store.delete_document(document_id)  # makes re-indexing safe
    vector_store.add_chunks(document_id, owner_id, chunks, vectors)
    return len(chunks)


def answer_question(document_id: int, owner_id: int, question: str, history: list[dict]) -> dict:
    """Return {"answer": str, "sources": [{page, snippet, score, chunk_id}, ...]}."""
    hits = retriever.retrieve(document_id, owner_id, question, history)
    if not hits:
        return {"answer": prompts.NOT_FOUND_MESSAGE, "sources": []}

    messages = prompts.build_messages(question, hits, history)
    answer = llm_service.generate_answer(messages)

    if answer.strip().startswith(prompts.NOT_FOUND_MESSAGE):
        return {"answer": prompts.NOT_FOUND_MESSAGE, "sources": []}  # no misleading citations

    return {"answer": answer, "sources": format_sources(hits)}


def format_sources(hits: list[dict]) -> list[dict]:
    return [
        {
            "page": h["page_number"],
            "snippet": prompts.make_snippet(h["text"], settings.SNIPPET_CHARS),
            "score": h["score"],
            "chunk_id": h["chunk_id"],
        }
        for h in hits
    ]

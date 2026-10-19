import pytest

from rag import embeddings, prompts, vector_store
from rag.chunking import Chunk, chunk_pages, chunk_text
from rag.pdf_processor import PDFProcessingError, extract_pages, get_page_count
from rag.pipeline import format_sources
from rag.retriever import build_search_text
from tests.conftest import make_pdf_bytes


def test_extract_pages_keeps_page_numbers(pdf_bytes):
    pages = extract_pages(pdf_bytes)
    assert [p.page_number for p in pages] == [1, 2, 3]
    assert "Photosynthesis" in pages[0].text
    assert "mitochondria" in pages[1].text
    assert "French Revolution" in pages[2].text


def test_blank_pages_are_skipped_but_numbering_stays_correct():
    data = make_pdf_bytes(["First page text", "", "Third page text"])
    pages = extract_pages(data)
    assert [p.page_number for p in pages] == [1, 3]
    assert get_page_count(data) == 3


def test_invalid_pdf_raises_friendly_error():
    with pytest.raises(PDFProcessingError):
        extract_pages(b"this is not a pdf")


def test_chunk_text_respects_size_and_overlap():
    text = " ".join(f"word{i}" for i in range(400))
    chunks = chunk_text(text, chunk_size=200, overlap=40)
    assert len(chunks) > 3
    assert all(len(c) <= 200 for c in chunks)
    # neighbours share some text because of the overlap
    assert set(chunks[0].split()[-3:]) & set(chunks[1].split()[:10])
    # nothing is lost: the last word is in the last chunk
    assert chunks[-1].endswith("word399")


def test_chunk_text_short_and_invalid_inputs():
    assert chunk_text("short text", 100, 10) == ["short text"]
    assert chunk_text("   ", 100, 10) == []
    with pytest.raises(ValueError):
        chunk_text("abc", 100, 100)
    with pytest.raises(ValueError):
        chunk_text("abc", 0, 0)


def test_chunk_pages_keeps_page_number_and_running_index(pdf_bytes):
    chunks = chunk_pages(extract_pages(pdf_bytes), 60, 10)
    assert [c.chunk_index for c in chunks] == list(range(len(chunks)))
    assert {c.page_number for c in chunks} == {1, 2, 3}


def test_hash_embeddings_are_stable_and_normalised():
    a = embeddings.embed_query("plants and sunlight")
    b = embeddings.embed_query("plants and sunlight")
    assert a == b
    assert abs(sum(v * v for v in a) - 1.0) < 1e-6


def _index(doc_id, owner_id, texts_by_page):
    chunks = [Chunk(page, i, text) for i, (page, text) in enumerate(texts_by_page)]
    vectors = embeddings.embed_texts([c.text for c in chunks])
    vector_store.add_chunks(doc_id, owner_id, chunks, vectors)


def test_vector_store_returns_most_relevant_chunk_first():
    _index(1, 10, [(1, "plants use sunlight for photosynthesis"), (2, "the french revolution started in 1789")])
    hits = vector_store.query_chunks(1, 10, embeddings.embed_query("when did the french revolution start"), 2)
    assert hits[0]["page_number"] == 2
    assert hits[0]["score"] >= hits[1]["score"]


def test_vector_store_never_leaks_other_documents_or_users():
    _index(1, 10, [(1, "secret salary table for alice")])
    _index(2, 20, [(1, "secret salary table for bob")])
    query = embeddings.embed_query("secret salary table")

    mine = vector_store.query_chunks(1, 10, query, 5)
    assert len(mine) == 1 and "alice" in mine[0]["text"]
    # right document id but wrong owner -> nothing
    assert vector_store.query_chunks(1, 20, query, 5) == []


def test_vector_store_delete_document():
    _index(5, 10, [(1, "temporary text"), (2, "more temporary text")])
    assert vector_store.count_document_chunks(5) == 2
    vector_store.delete_document(5)
    assert vector_store.count_document_chunks(5) == 0


def test_build_messages_and_citation_formatting():
    hits = [{"chunk_id": "doc1-chunk0", "page_number": 4, "text": "x " * 400, "score": 0.91}]
    messages = prompts.build_messages("What is x?", hits, [{"role": "user", "content": "hi"}])
    assert messages[0]["role"] == "system" and "Never invent" in messages[0]["content"]
    assert messages[-1]["content"].count('<excerpt page="4">') == 1
    assert "untrusted" in messages[0]["content"].lower()

    sources = format_sources(hits)
    assert sources[0]["page"] == 4
    assert len(sources[0]["snippet"]) <= 300 and sources[0]["snippet"].endswith("…")


def test_short_followup_uses_previous_question_for_search():
    history = [{"role": "user", "content": "What is photosynthesis in plants?"}]
    assert "photosynthesis" in build_search_text("and why?", history)
    long_q = "Tell me everything about the French Revolution please"
    assert build_search_text(long_q, history) == long_q

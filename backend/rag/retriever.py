"""Semantic retrieval: question -> embedding -> closest chunks of ONE document."""
from django.conf import settings

from . import embeddings, vector_store


def build_search_text(question: str, history: list[dict]) -> str:
    """For very short follow-ups ("and the second one?") add the previous user question."""
    if len(question.split()) < 6:
        previous = [m["content"] for m in history if m["role"] == "user"]
        if previous:
            return f"{previous[-1]} {question}"
    return question


def retrieve(document_id: int, owner_id: int, question: str, history: list[dict]) -> list[dict]:
    text = build_search_text(question, history)
    query_vector = embeddings.embed_query(text)
    return vector_store.query_chunks(document_id, owner_id, query_vector, settings.RETRIEVAL_TOP_K)

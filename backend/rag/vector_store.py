"""ChromaDB operations. Vectors live here - never in MySQL."""
import logging
from functools import lru_cache

import chromadb
from chromadb.config import Settings as ChromaSettings
from django.conf import settings

from .chunking import Chunk

logger = logging.getLogger(__name__)
_BATCH = 100


@lru_cache(maxsize=4)
def _client(path: str):
    return chromadb.PersistentClient(path=path, settings=ChromaSettings(anonymized_telemetry=False))


def get_collection():
    client = _client(str(settings.CHROMA_DIR))
    # We always pass our own embeddings, so no Chroma embedding function is needed.
    return client.get_or_create_collection(
        name=settings.CHROMA_COLLECTION,
        metadata={"hnsw:space": "cosine"},
        embedding_function=None,
    )


def add_chunks(document_id: int, owner_id: int, chunks: list[Chunk], embeddings: list[list[float]]) -> None:
    collection = get_collection()
    for i in range(0, len(chunks), _BATCH):
        part = chunks[i : i + _BATCH]
        collection.add(
            ids=[f"doc{document_id}-chunk{c.chunk_index}" for c in part],
            embeddings=embeddings[i : i + _BATCH],
            documents=[c.text for c in part],
            metadatas=[
                {
                    "document_id": document_id,
                    "owner_id": owner_id,
                    "page_number": c.page_number,
                    "chunk_index": c.chunk_index,
                }
                for c in part
            ],
        )


def query_chunks(document_id: int, owner_id: int, query_embedding: list[float], top_k: int) -> list[dict]:
    """Return the closest chunks from ONE document that belongs to ONE user."""
    collection = get_collection()
    result = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        where={"$and": [{"document_id": {"$eq": document_id}}, {"owner_id": {"$eq": owner_id}}]},
        include=["documents", "metadatas", "distances"],
    )
    hits = []
    for chunk_id, text, meta, distance in zip(
        result["ids"][0], result["documents"][0], result["metadatas"][0], result["distances"][0]
    ):
        hits.append(
            {
                "chunk_id": chunk_id,
                "text": text,
                "page_number": meta["page_number"],
                "score": round(1.0 - float(distance), 4),  # cosine similarity
            }
        )
    return hits


def delete_document(document_id: int) -> None:
    get_collection().delete(where={"document_id": {"$eq": document_id}})


def count_document_chunks(document_id: int) -> int:
    got = get_collection().get(where={"document_id": {"$eq": document_id}}, include=[])
    return len(got["ids"])


def reset_collection() -> None:
    """Delete everything. Used by tests only."""
    client = _client(str(settings.CHROMA_DIR))
    try:
        client.delete_collection(settings.CHROMA_COLLECTION)
    except Exception:  # noqa: BLE001
        logger.debug("Collection did not exist yet")

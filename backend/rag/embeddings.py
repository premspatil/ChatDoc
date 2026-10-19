"""Step 3 of RAG: turn text into vectors (embeddings).

The SAME model must be used when indexing and when answering questions,
which is why the model name comes from one setting (EMBEDDING_MODEL).
"""
import hashlib
import math
import re
from functools import lru_cache

from django.conf import settings


@lru_cache(maxsize=1)
def _load_sentence_transformer(model_name: str):
    # Imported lazily: loading torch is slow and not needed for most requests.
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(model_name)


def _hash_embedding(text: str, dims: int = 256) -> list[float]:
    """Tiny offline stand-in used by the test-suite (bag-of-words hashing)."""
    vector = [0.0] * dims
    for word in re.findall(r"[a-z0-9]+", text.lower()):
        digest = hashlib.md5(word.encode()).digest()
        vector[int.from_bytes(digest[:4], "big") % dims] += 1.0
    norm = math.sqrt(sum(v * v for v in vector)) or 1.0
    return [v / norm for v in vector]


def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    if settings.EMBEDDING_BACKEND == "hash":
        return [_hash_embedding(t) for t in texts]
    model = _load_sentence_transformer(settings.EMBEDDING_MODEL)
    vectors = model.encode(texts, batch_size=32, normalize_embeddings=True, show_progress_bar=False)
    return [v.tolist() for v in vectors]


def embed_query(text: str) -> list[float]:
    return embed_texts([text])[0]

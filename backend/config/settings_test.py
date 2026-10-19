"""Settings used only by pytest: SQLite, temp folders, fake embeddings, no real LLM."""
import tempfile
from pathlib import Path

from .settings import *  # noqa: F401,F403

DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}

_TMP = Path(tempfile.mkdtemp(prefix="chatdoc_tests_"))
MEDIA_ROOT = _TMP / "media"
CHROMA_DIR = _TMP / "chroma"
CHROMA_COLLECTION = "chatdoc_test_chunks"

EMBEDDING_BACKEND = "hash"
LLM_API_KEY = "test-key"
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]  # fast tests only

REST_FRAMEWORK = {
    **REST_FRAMEWORK,  # noqa: F405
    "DEFAULT_THROTTLE_RATES": {"ask": "1000/min", "auth": "1000/min", "upload": "1000/min"},
}
CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}

import pymupdf
import pytest
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from rag import vector_store

User = get_user_model()


@pytest.fixture(autouse=True)
def clean_vector_store():
    """Every test starts and ends with an empty ChromaDB collection."""
    vector_store.reset_collection()
    yield
    vector_store.reset_collection()


@pytest.fixture(autouse=True)
def isolated_media(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path / "media"


def make_pdf_bytes(pages: list[str]) -> bytes:
    """Build a small real PDF where each string becomes one page of text."""
    doc = pymupdf.open()
    for text in pages:
        page = doc.new_page()
        if text:
            page.insert_textbox(pymupdf.Rect(40, 40, 555, 800), text, fontsize=11)
    data = doc.tobytes()
    doc.close()
    return data


@pytest.fixture
def pdf_bytes():
    return make_pdf_bytes(
        [
            "Photosynthesis is the process plants use to turn sunlight, water and carbon dioxide into sugar and oxygen.",
            "The mitochondria produce energy for the cell. This energy is stored as ATP molecules.",
            "The French Revolution began in 1789 and changed the political structure of France.",
        ]
    )


@pytest.fixture
def make_user(db):
    def _make(username="alice", password="Str0ng-Pass-123"):
        return User.objects.create_user(username=username, password=password, email=f"{username}@example.com")

    return _make


@pytest.fixture
def auth_client(make_user):
    def _client(user=None):
        user = user or make_user()
        token, _ = Token.objects.get_or_create(user=user)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
        client.user = user
        return client

    return _client


@pytest.fixture
def client_alice(auth_client, make_user):
    return auth_client(make_user("alice"))


@pytest.fixture
def client_bob(auth_client, make_user):
    return auth_client(make_user("bob"))


@pytest.fixture
def upload_pdf():
    from django.core.files.uploadedfile import SimpleUploadedFile

    def _upload(client, data, name="notes.pdf"):
        return client.post(
            "/api/documents/upload/",
            {"file": SimpleUploadedFile(name, data, content_type="application/pdf")},
            format="multipart",
        )

    return _upload

import os

import pytest

from documents.models import Document
from rag import vector_store
from tests.conftest import make_pdf_bytes

pytestmark = pytest.mark.django_db


def test_upload_requires_login(upload_pdf, pdf_bytes):
    from rest_framework.test import APIClient

    assert upload_pdf(APIClient(), pdf_bytes).status_code == 401


def test_upload_valid_pdf_is_processed(client_alice, upload_pdf, pdf_bytes):
    res = upload_pdf(client_alice, pdf_bytes, "biology.pdf")
    assert res.status_code == 201
    assert res.data["status"] == "ready"
    assert res.data["page_count"] == 3
    assert res.data["chunk_count"] >= 3
    assert res.data["original_filename"] == "biology.pdf"
    doc = Document.objects.get(pk=res.data["id"])
    assert vector_store.count_document_chunks(doc.pk) == doc.chunk_count
    # the stored file name is random - never the user's file name
    assert "biology" not in doc.file.name


@pytest.mark.parametrize(
    "name,data,fragment",
    [
        ("notes.txt", b"%PDF-1.4 fake", "Only .pdf"),
        ("empty.pdf", b"", "empty"),
        ("fake.pdf", b"just some text, not a pdf", "not a valid PDF"),
        ("broken.pdf", b"%PDF-1.4 this is broken", "could not be read"),
    ],
)
def test_upload_validation_errors(client_alice, upload_pdf, name, data, fragment):
    res = upload_pdf(client_alice, data, name)
    assert res.status_code == 400
    assert fragment in str(res.data)


def test_upload_too_large(client_alice, upload_pdf, pdf_bytes, settings):
    settings.MAX_UPLOAD_BYTES = 100
    settings.MAX_UPLOAD_MB = 0
    res = upload_pdf(client_alice, pdf_bytes)
    assert res.status_code == 400 and "too large" in str(res.data)


def test_path_traversal_filename_is_harmless(client_alice, upload_pdf, pdf_bytes):
    res = upload_pdf(client_alice, pdf_bytes, "../../evil.pdf")
    assert res.status_code == 201
    doc = Document.objects.get(pk=res.data["id"])
    assert ".." not in doc.file.name
    assert doc.file.name.startswith(f"documents/{doc.owner_id}/")


def test_scanned_pdf_gets_helpful_message(client_alice, upload_pdf):
    res = upload_pdf(client_alice, make_pdf_bytes(["", ""]))
    assert res.status_code == 201
    assert res.data["status"] == "failed"
    assert "scanned" in res.data["error_message"].lower()


def test_duplicate_upload_is_not_reprocessed(client_alice, upload_pdf, pdf_bytes):
    first = upload_pdf(client_alice, pdf_bytes)
    second = upload_pdf(client_alice, pdf_bytes, "renamed.pdf")
    assert second.status_code == 200 and second.data["duplicate"] is True
    assert second.data["id"] == first.data["id"]
    assert Document.objects.count() == 1


def test_same_pdf_can_be_uploaded_by_two_users(client_alice, client_bob, upload_pdf, pdf_bytes):
    a = upload_pdf(client_alice, pdf_bytes)
    b = upload_pdf(client_bob, pdf_bytes)
    assert a.status_code == b.status_code == 201
    assert a.data["id"] != b.data["id"]


def test_users_only_see_their_own_documents(client_alice, client_bob, upload_pdf, pdf_bytes):
    doc_id = upload_pdf(client_alice, pdf_bytes).data["id"]
    assert len(client_alice.get("/api/documents/").data["results"]) == 1
    assert client_bob.get("/api/documents/").data["results"] == []
    assert client_bob.get(f"/api/documents/{doc_id}/").status_code == 404
    assert client_bob.delete(f"/api/documents/{doc_id}/").status_code == 404
    assert Document.objects.filter(pk=doc_id).exists()


def test_delete_document_removes_file_vectors_and_chats(client_alice, upload_pdf, pdf_bytes):
    doc_id = upload_pdf(client_alice, pdf_bytes).data["id"]
    chat = client_alice.post("/api/chats/", {"document_id": doc_id}, format="json")
    assert chat.status_code == 201
    path = Document.objects.get(pk=doc_id).file.path
    assert os.path.exists(path)

    assert client_alice.delete(f"/api/documents/{doc_id}/").status_code == 204

    assert not Document.objects.filter(pk=doc_id).exists()
    assert not os.path.exists(path)
    assert vector_store.count_document_chunks(doc_id) == 0
    assert client_alice.get("/api/chats/").data["results"] == []

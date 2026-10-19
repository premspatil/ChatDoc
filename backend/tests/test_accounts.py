import pytest
from rest_framework.test import APIClient

pytestmark = pytest.mark.django_db


def test_register_returns_token_and_hashes_password():
    client = APIClient()
    res = client.post(
        "/api/auth/register/",
        {"username": "newuser", "email": "n@example.com", "password": "Str0ng-Pass-123"},
        format="json",
    )
    assert res.status_code == 201
    assert res.data["token"]
    assert "password" not in res.data["user"]

    from django.contrib.auth import get_user_model

    user = get_user_model().objects.get(username="newuser")
    assert user.password != "Str0ng-Pass-123"  # stored hashed


def test_register_rejects_weak_password_and_duplicate_username(make_user):
    make_user("taken")
    client = APIClient()
    weak = client.post("/api/auth/register/", {"username": "x1", "password": "123"}, format="json")
    assert weak.status_code == 400
    dup = client.post(
        "/api/auth/register/", {"username": "TAKEN", "password": "Str0ng-Pass-123"}, format="json"
    )
    assert dup.status_code == 400


def test_login_success_and_failure(make_user):
    make_user("alice", "Str0ng-Pass-123")
    client = APIClient()
    ok = client.post("/api/auth/login/", {"username": "alice", "password": "Str0ng-Pass-123"}, format="json")
    assert ok.status_code == 200 and ok.data["token"]
    bad = client.post("/api/auth/login/", {"username": "alice", "password": "wrong"}, format="json")
    assert bad.status_code == 400


def test_me_requires_authentication(client_alice):
    assert APIClient().get("/api/auth/me/").status_code == 401
    res = client_alice.get("/api/auth/me/")
    assert res.status_code == 200 and res.data["username"] == "alice"


def test_logout_invalidates_token(client_alice):
    assert client_alice.post("/api/auth/logout/").status_code == 204
    assert client_alice.get("/api/auth/me/").status_code == 401


def test_private_endpoints_are_protected():
    client = APIClient()
    for url in ["/api/documents/", "/api/chats/"]:
        assert client.get(url).status_code == 401


def test_health_is_public():
    res = APIClient().get("/api/health/")
    assert res.status_code == 200 and res.data["status"] == "ok"

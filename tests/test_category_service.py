import pytest
from fastapi.testclient import TestClient
import sys, os

sys.path.insert(0, os.path.abspath("category-service"))

from app.main import app
from app.config import settings

client = TestClient(app)

KEY = os.environ["INTERNAL_API_KEY"]


def gw(user_id, email="test@example.com"):
    return {"X-User-ID": str(user_id), "X-User-Email": email, "X-Internal-Key": KEY}


def test_category_health():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["service"] == "category"


def test_category_crud_flow():
    headers = gw(1)
    create_res = client.post("/categories/", json={"name": "Subscriptions", "type": "expense"}, headers=headers)
    assert create_res.status_code == 200
    category = create_res.json()
    assert category["name"] == "Subscriptions"
    assert category["user_id"] == 1
    cat_id = category["id"]

    assert any(c["id"] == cat_id for c in client.get("/categories/", headers=headers).json())

    del_res = client.delete(f"/categories/{cat_id}", headers=headers)
    assert del_res.status_code == 200
    assert del_res.json()["message"] == "Category deleted"
    assert not any(c["id"] == cat_id for c in client.get("/categories/", headers=headers).json())


def test_category_not_found_error():
    assert client.delete("/categories/99999", headers=gw(1)).status_code == 404


# ---------------------------------------------------------------- tenant isolation

def test_user_cannot_list_another_users_categories():
    cat_id = client.post("/categories/", json={"name": "Secret", "type": "expense"}, headers=gw(10)).json()["id"]
    assert not any(c["id"] == cat_id for c in client.get("/categories/", headers=gw(11)).json())


def test_user_cannot_delete_another_users_category():
    cat_id = client.post("/categories/", json={"name": "Mine", "type": "income"}, headers=gw(20)).json()["id"]

    assert client.delete(f"/categories/{cat_id}", headers=gw(21)).status_code == 404

    assert any(c["id"] == cat_id for c in client.get("/categories/", headers=gw(20)).json())


def test_body_cannot_set_owner():
    res = client.post("/categories/", json={"name": "Planted", "type": "expense", "user_id": 999}, headers=gw(30))
    assert res.status_code == 200
    assert res.json()["user_id"] == 30
    assert client.get("/categories/", headers=gw(999)).json() == []


# ------------------------------------------------- only the gateway may assert identity

def test_forged_identity_without_internal_key_is_rejected():
    assert client.get("/categories/", headers={"X-User-ID": "1"}).status_code == 401


def test_wrong_internal_key_is_rejected():
    assert client.get("/categories/", headers={"X-User-ID": "1", "X-Internal-Key": "guess"}).status_code == 401


def test_internal_key_without_identity_is_rejected():
    assert client.get("/categories/", headers={"X-Internal-Key": KEY}).status_code == 401


def test_service_fails_closed_when_no_key_configured(monkeypatch):
    monkeypatch.setattr(settings, "internal_api_key", "")
    assert client.get("/categories/", headers={"X-User-ID": "1", "X-Internal-Key": ""}).status_code == 401


def test_bearer_token_alone_is_not_accepted_and_auth_service_is_not_called(httpx_mock):
    res = client.get("/categories/", headers={"Authorization": "Bearer anything"})
    assert res.status_code == 401
    assert httpx_mock.get_requests() == []


def test_category_unauthorized():
    assert client.get("/categories/").status_code == 401

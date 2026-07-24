import pytest
from fastapi.testclient import TestClient
import sys, os

sys.path.insert(0, os.path.abspath("category-service"))

from app.main import app
from app.config import settings

client = TestClient(app)

def test_category_health():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["service"] == "category"

def test_category_crud_flow_header_auth():
    headers = {"X-User-ID": "1", "X-User-Email": "test@example.com"}

    # Create Category
    cat_payload = {
        "name": "Subscriptions",
        "type": "expense"
    }
    create_res = client.post("/categories/", json=cat_payload, headers=headers)
    assert create_res.status_code == 200
    category = create_res.json()
    assert category["name"] == "Subscriptions"
    assert category["user_id"] == 1
    cat_id = category["id"]

    # Get Categories for User 1
    get_res = client.get("/categories/", headers=headers)
    assert get_res.status_code == 200
    categories = get_res.json()
    assert len(categories) >= 1
    assert any(c["id"] == cat_id for c in categories)

    # Delete Category
    del_res = client.delete(f"/categories/{cat_id}", headers=headers)
    assert del_res.status_code == 200
    assert del_res.json()["message"] == "Category deleted"

def test_category_not_found_error():
    headers = {"X-User-ID": "1"}
    del_res = client.delete("/categories/99999", headers=headers)
    assert del_res.status_code == 404

def test_category_unauthorized():
    res = client.get("/categories/")
    assert res.status_code == 401

def test_category_auth_fallback(httpx_mock):
    httpx_mock.add_response(
        method="GET",
        url=f"{settings.auth_service_url}/auth/verify?token=valid_token",
        status_code=200,
        json={"valid": True, "user_id": 88, "email": "cat@example.com"}
    )
    res = client.get("/categories/", headers={"Authorization": "Bearer valid_token"})
    assert res.status_code == 200

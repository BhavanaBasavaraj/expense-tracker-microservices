import pytest
from fastapi.testclient import TestClient
import sys, os

sys.path.insert(0, os.path.abspath("expense-service"))

from app.main import app
from app.config import settings

client = TestClient(app)

def test_expense_health():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["service"] == "expense"

def test_expense_crud_flow_header_auth():
    headers = {"X-User-ID": "1", "X-User-Email": "test@example.com"}

    # Create Expense
    exp_payload = {
        "title": "Groceries",
        "amount": 150.75,
        "type": "expense",
        "date": "2026-07-24",
        "category_id": 1,
        "description": "Weekly grocery shopping"
    }
    create_res = client.post("/expenses/", json=exp_payload, headers=headers)
    assert create_res.status_code == 200
    expense = create_res.json()
    assert expense["title"] == "Groceries"
    assert expense["user_id"] == 1
    exp_id = expense["id"]

    # Get Expenses for User 1
    get_res = client.get("/expenses/", headers=headers)
    assert get_res.status_code == 200
    expenses = get_res.json()
    assert len(expenses) >= 1
    assert any(e["id"] == exp_id for e in expenses)

    # Get Expenses for User 2 (should be empty for user 2)
    user2_res = client.get("/expenses/", headers={"X-User-ID": "2"})
    assert user2_res.status_code == 200
    assert not any(e["id"] == exp_id for e in user2_res.json())

    # Update Expense
    update_payload = {
        "title": "Supermarket Groceries",
        "amount": 175.00,
        "type": "expense",
        "date": "2026-07-24",
        "category_id": 1,
        "description": "Updated grocery shopping"
    }
    update_res = client.put(f"/expenses/{exp_id}", json=update_payload, headers=headers)
    assert update_res.status_code == 200
    assert update_res.json()["title"] == "Supermarket Groceries"

    # Delete Expense
    del_res = client.delete(f"/expenses/{exp_id}", headers=headers)
    assert del_res.status_code == 200
    assert del_res.json()["message"] == "Expense deleted"

def test_expense_not_found_errors():
    headers = {"X-User-ID": "1"}
    payload = {
        "title": "Test",
        "amount": 10.0,
        "type": "expense",
        "date": "2026-07-24"
    }

    # Update non-existent expense
    put_res = client.put("/expenses/99999", json=payload, headers=headers)
    assert put_res.status_code == 404

    # Delete non-existent expense
    del_res = client.delete("/expenses/99999", headers=headers)
    assert del_res.status_code == 404

def test_expense_unauthorized():
    # Request without X-User-ID or Authorization header
    response = client.get("/expenses/")
    assert response.status_code == 401

def test_expense_auth_service_fallback(httpx_mock):
    # Test Bearer authorization header fallback when X-User-ID is not provided
    httpx_mock.add_response(
        method="GET",
        url=f"{settings.auth_service_url}/auth/verify?token=valid_token",
        status_code=200,
        json={"valid": True, "user_id": 99, "email": "fallback@example.com"}
    )

    headers = {"Authorization": "Bearer valid_token"}
    res = client.get("/expenses/", headers=headers)
    assert res.status_code == 200

def test_expense_auth_service_fallback_invalid(httpx_mock):
    httpx_mock.add_response(
        method="GET",
        url=f"{settings.auth_service_url}/auth/verify?token=invalid_token",
        status_code=401,
        json={"detail": "Invalid token"}
    )

    headers = {"Authorization": "Bearer invalid_token"}
    res = client.get("/expenses/", headers=headers)
    assert res.status_code == 401

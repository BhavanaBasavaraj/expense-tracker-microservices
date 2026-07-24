import pytest
from fastapi.testclient import TestClient
import sys, os
import httpx

sys.path.insert(0, os.path.abspath("analytics-service"))

from app.main import app
from app.config import settings

def test_analytics_health():
    with TestClient(app) as client:
        res = client.get("/health")
        assert res.status_code == 200
        assert res.json()["service"] == "analytics"

def test_analytics_dashboard_with_httpx_mock(httpx_mock):
    headers = {"X-User-ID": "1", "X-User-Email": "analytics@example.com"}

    httpx_mock.add_response(
        method="GET",
        url=f"{settings.expense_service_url}/expenses/",
        status_code=200,
        is_reusable=True,
        json=[
            {"id": 1, "user_id": 1, "title": "Salary", "amount": 5000.0, "type": "income", "date": "2026-07-01", "category_id": 1},
            {"id": 2, "user_id": 1, "title": "Rent", "amount": 1500.0, "type": "expense", "date": "2026-07-02", "category_id": 2},
            {"id": 3, "user_id": 1, "title": "Groceries", "amount": 300.0, "type": "expense", "date": "2026-07-15", "category_id": 2},
        ]
    )

    with TestClient(app) as client:
        r1 = client.get("/analytics/dashboard", headers=headers)
        assert r1.status_code == 200
        data1 = r1.json()
        assert data1["total_income"] == 5000.0
        assert data1["total_expenses"] == 1800.0
        assert data1["net_balance"] == 3200.0

        r2 = client.get("/analytics/by-category", headers=headers)
        assert r2.status_code == 200
        data2 = r2.json()
        assert "1" in data2
        assert "2" in data2
        assert data2["2"]["total"] == 1800.0

        r3 = client.get("/analytics/monthly", headers=headers)
        assert r3.status_code == 200
        data3 = r3.json()
        assert "2026-07" in data3
        assert data3["2026-07"]["income"] == 5000.0

def test_analytics_temp_client_fallback(httpx_mock):
    headers = {"X-User-ID": "1"}

    httpx_mock.add_response(
        method="GET",
        url=f"{settings.expense_service_url}/expenses/",
        status_code=200,
        json=[
            {"id": 1, "user_id": 1, "title": "Freelance", "amount": 800.0, "type": "income", "date": "2026-07-10", "category_id": 1}
        ]
    )

    if hasattr(app.state, "http_client"):
        delattr(app.state, "http_client")

    client = TestClient(app)
    res = client.get("/analytics/dashboard", headers=headers)
    assert res.status_code == 200
    assert res.json()["total_income"] == 800.0

def test_analytics_expense_service_error_handling(httpx_mock):
    headers = {"X-User-ID": "1"}

    # Case 1: Expense service returns 500 error
    httpx_mock.add_response(
        method="GET",
        url=f"{settings.expense_service_url}/expenses/",
        status_code=500,
        json={"detail": "Database error"}
    )
    with TestClient(app) as client:
        r1 = client.get("/analytics/dashboard", headers=headers)
        assert r1.status_code == 500

    # Case 2: Expense service returns non-list format
    httpx_mock.add_response(
        method="GET",
        url=f"{settings.expense_service_url}/expenses/",
        status_code=200,
        json={"error": "invalid format"}
    )
    with TestClient(app) as client:
        r2 = client.get("/analytics/dashboard", headers=headers)
        assert r2.status_code == 500

    # Case 3: Expense service connection failure (503)
    httpx_mock.add_exception(
        httpx.RequestError("Connection timeout"),
        url=f"{settings.expense_service_url}/expenses/"
    )
    with TestClient(app) as client:
        r3 = client.get("/analytics/dashboard", headers=headers)
        assert r3.status_code == 503

def test_analytics_auth_fallback(httpx_mock):
    httpx_mock.add_response(
        method="GET",
        url=f"{settings.auth_service_url}/auth/verify?token=valid_token",
        status_code=200,
        json={"valid": True, "user_id": 77, "email": "a@b.com"}
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{settings.expense_service_url}/expenses/",
        status_code=200,
        json=[]
    )

    with TestClient(app) as client:
        res = client.get("/analytics/dashboard", headers={"Authorization": "Bearer valid_token"})
        assert res.status_code == 200

def test_analytics_unauthorized():
    with TestClient(app) as client:
        res = client.get("/analytics/dashboard")
        assert res.status_code == 401

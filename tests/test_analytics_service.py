import pytest
from fastapi.testclient import TestClient
import sys, os
import httpx

sys.path.insert(0, os.path.abspath("analytics-service"))

from app.main import app
from app.config import settings

KEY = os.environ["INTERNAL_API_KEY"]
EXPENSES_URL = f"{settings.expense_service_url}/expenses/"

SAMPLE = [
    {"id": 1, "user_id": 1, "title": "Salary", "amount": 5000.0, "type": "income", "date": "2026-07-01", "category_id": 1},
    {"id": 2, "user_id": 1, "title": "Rent", "amount": 1500.0, "type": "expense", "date": "2026-07-02", "category_id": 2},
    {"id": 3, "user_id": 1, "title": "Groceries", "amount": 300.0, "type": "expense", "date": "2026-07-15", "category_id": 2},
]


def gw(user_id=1, email="analytics@example.com"):
    return {"X-User-ID": str(user_id), "X-User-Email": email, "X-Internal-Key": KEY}


def test_analytics_health():
    with TestClient(app) as client:
        res = client.get("/health")
        assert res.status_code == 200
        assert res.json()["service"] == "analytics"


def test_analytics_numbers_computed_from_expenses(httpx_mock):
    httpx_mock.add_response(method="GET", url=EXPENSES_URL, status_code=200, is_reusable=True, json=SAMPLE)

    with TestClient(app) as client:
        data1 = client.get("/analytics/dashboard", headers=gw()).json()
        assert data1["total_income"] == 5000.0
        assert data1["total_expenses"] == 1800.0
        assert data1["net_balance"] == 3200.0
        assert data1["total_transactions"] == 3

        data2 = client.get("/analytics/by-category", headers=gw()).json()
        assert data2["1"] == {"total": 5000.0, "count": 1}
        assert data2["2"] == {"total": 1800.0, "count": 2}

        data3 = client.get("/analytics/monthly", headers=gw()).json()
        assert data3["2026-07"] == {"income": 5000.0, "expenses": 1800.0}


def test_analytics_asks_expense_service_for_the_callers_data_only(httpx_mock):
    """Analytics must pass the caller's identity on, authenticated as the gateway-trusted
    internal caller, and must not leak the user's raw bearer token downstream."""
    httpx_mock.add_response(method="GET", url=EXPENSES_URL, status_code=200, json=[])

    with TestClient(app) as client:
        headers = gw(user_id=77)
        headers["Authorization"] = "Bearer should-not-be-forwarded"
        assert client.get("/analytics/dashboard", headers=headers).status_code == 200

    sent = httpx_mock.get_requests()[0]
    assert sent.headers["X-User-ID"] == "77"
    assert sent.headers["X-Internal-Key"] == KEY
    assert "authorization" not in sent.headers


def test_analytics_temp_client_fallback(httpx_mock):
    httpx_mock.add_response(
        method="GET", url=EXPENSES_URL, status_code=200,
        json=[{"id": 1, "user_id": 1, "title": "Freelance", "amount": 800.0, "type": "income", "date": "2026-07-10", "category_id": 1}],
    )
    if hasattr(app.state, "http_client"):
        delattr(app.state, "http_client")

    client = TestClient(app)
    res = client.get("/analytics/dashboard", headers=gw())
    assert res.status_code == 200
    assert res.json()["total_income"] == 800.0


def test_analytics_expense_service_error_handling(httpx_mock):
    httpx_mock.add_response(method="GET", url=EXPENSES_URL, status_code=500, json={"detail": "Database error"})
    with TestClient(app) as client:
        assert client.get("/analytics/dashboard", headers=gw()).status_code == 500

    httpx_mock.add_response(method="GET", url=EXPENSES_URL, status_code=200, json={"error": "invalid format"})
    with TestClient(app) as client:
        assert client.get("/analytics/dashboard", headers=gw()).status_code == 500

    httpx_mock.add_exception(httpx.RequestError("Connection timeout"), url=EXPENSES_URL)
    with TestClient(app) as client:
        assert client.get("/analytics/dashboard", headers=gw()).status_code == 503


# ------------------------------------------------- only the gateway may assert identity

def test_forged_identity_without_internal_key_is_rejected(httpx_mock):
    with TestClient(app) as client:
        res = client.get("/analytics/dashboard", headers={"X-User-ID": "1"})
    assert res.status_code == 401
    assert httpx_mock.get_requests() == []  # never reached the expense service


def test_wrong_internal_key_is_rejected():
    with TestClient(app) as client:
        res = client.get("/analytics/dashboard", headers={"X-User-ID": "1", "X-Internal-Key": "guess"})
    assert res.status_code == 401


def test_service_fails_closed_when_no_key_configured(monkeypatch):
    monkeypatch.setattr(settings, "internal_api_key", "")
    with TestClient(app) as client:
        res = client.get("/analytics/dashboard", headers={"X-User-ID": "1", "X-Internal-Key": ""})
    assert res.status_code == 401


def test_bearer_token_alone_is_not_accepted_and_auth_service_is_not_called(httpx_mock):
    with TestClient(app) as client:
        res = client.get("/analytics/dashboard", headers={"Authorization": "Bearer anything"})
    assert res.status_code == 401
    assert httpx_mock.get_requests() == []


def test_analytics_unauthorized():
    with TestClient(app) as client:
        assert client.get("/analytics/dashboard").status_code == 401

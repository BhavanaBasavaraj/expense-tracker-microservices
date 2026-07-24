import pytest
from fastapi.testclient import TestClient
import sys, os

sys.path.insert(0, os.path.abspath("analytics-service"))

from app.main import app
from app.routers.analytics import get_current_user
import app.routers.analytics as analytics_module

def override_get_current_user():
    return {"user_id": 1, "email": "analytics.user@example.com"}

async def mock_get_expenses(token: str, user_id: int):
    return [
        {"id": 1, "user_id": 1, "title": "Salary", "amount": 5000.0, "type": "income", "date": "2026-07-01", "category_id": 1},
        {"id": 2, "user_id": 1, "title": "Rent", "amount": 1500.0, "type": "expense", "date": "2026-07-02", "category_id": 2},
        {"id": 3, "user_id": 1, "title": "Groceries", "amount": 300.0, "type": "expense", "date": "2026-07-15", "category_id": 2},
    ]

app.dependency_overrides[get_current_user] = override_get_current_user

client = TestClient(app)

def test_analytics_dashboard(monkeypatch):
    monkeypatch.setattr(analytics_module, "get_expenses", mock_get_expenses)
    response = client.get("/analytics/dashboard", headers={"Authorization": "Bearer fake-token"})
    assert response.status_code == 200
    data = response.json()
    assert data["total_income"] == 5000.0
    assert data["total_expenses"] == 1800.0
    assert data["net_balance"] == 3200.0
    assert data["total_transactions"] == 3

def test_analytics_by_category(monkeypatch):
    monkeypatch.setattr(analytics_module, "get_expenses", mock_get_expenses)
    response = client.get("/analytics/by-category", headers={"Authorization": "Bearer fake-token"})
    assert response.status_code == 200
    data = response.json()
    assert "1" in data
    assert data["1"]["total"] == 5000.0
    assert "2" in data
    assert data["2"]["total"] == 1800.0
    assert data["2"]["count"] == 2

def test_analytics_monthly(monkeypatch):
    monkeypatch.setattr(analytics_module, "get_expenses", mock_get_expenses)
    response = client.get("/analytics/monthly", headers={"Authorization": "Bearer fake-token"})
    assert response.status_code == 200
    data = response.json()
    assert "2026-07" in data
    assert data["2026-07"]["income"] == 5000.0
    assert data["2026-07"]["expenses"] == 1800.0

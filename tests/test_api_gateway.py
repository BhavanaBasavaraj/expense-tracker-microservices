import pytest
from fastapi.testclient import TestClient
import sys, os

sys.path.insert(0, os.path.abspath("api-gateway"))

from app.main import app
import app.main as gateway_module

client = TestClient(app)

def test_gateway_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["gateway"] == "healthy"

def test_gateway_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["message"] == "Expense Tracker API Gateway"

def test_gateway_service_unavailable_error():
    # Calling auth proxy when downstream auth-service is unreachable
    response = client.get("/auth/me?token=test")
    assert response.status_code == 503
    assert "Service unavailable" in response.json()["detail"]

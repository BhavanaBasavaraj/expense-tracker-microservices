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

def test_gateway_protected_route_unauthorized():
    response = client.get("/expenses/")
    assert response.status_code == 401
    assert "Invalid or missing authentication token" in response.json()["detail"]

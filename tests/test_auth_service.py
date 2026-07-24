import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import sys, os
sys.path.insert(0, os.path.abspath("auth-service"))

from app.database import Base, get_db
from app.main import app

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

Base.metadata.create_all(bind=engine)
app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_register_user_success():
    response = client.post(
        "/auth/register",
        json={
            "email": "john.doe@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "password": "securepassword123"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "john.doe@example.com"
    assert "id" in data

def test_register_user_invalid_email():
    response = client.post(
        "/auth/register",
        json={
            "email": "not-an-email",
            "first_name": "John",
            "last_name": "Doe",
            "password": "securepassword123"
        }
    )
    assert response.status_code == 422

def test_register_user_duplicate_email():
    payload = {
        "email": "duplicate@example.com",
        "first_name": "Jane",
        "last_name": "Doe",
        "password": "securepassword123"
    }
    res1 = client.post("/auth/register", json=payload)
    assert res1.status_code == 200

    res2 = client.post("/auth/register", json=payload)
    assert res2.status_code == 400
    assert res2.json()["detail"] == "Email already registered"

def test_login_and_verify_token():
    client.post(
        "/auth/register",
        json={
            "email": "auth.user@example.com",
            "first_name": "Auth",
            "last_name": "User",
            "password": "mypassword"
        }
    )

    login_res = client.post(
        "/auth/login",
        data={"username": "auth.user@example.com", "password": "mypassword"}
    )
    assert login_res.status_code == 200
    token_data = login_res.json()
    assert "access_token" in token_data
    token = token_data["access_token"]

    verify_res = client.get(f"/auth/verify?token={token}")
    assert verify_res.status_code == 200
    assert verify_res.json()["valid"] is True
    assert verify_res.json()["email"] == "auth.user@example.com"

def test_verify_invalid_token():
    res = client.get("/auth/verify?token=invalid_token")
    assert res.status_code == 401
    assert res.json()["detail"] == "Invalid token"

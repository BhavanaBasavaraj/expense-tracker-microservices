import pytest
from fastapi.testclient import TestClient
import sys, os
from jose import jwt

sys.path.insert(0, os.path.abspath("auth-service"))

from app.main import app
from app.config import settings
from app.routers.auth import hash_password, verify_password, create_token

client = TestClient(app)

def test_auth_health_and_root():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["service"] == "auth"

def test_hash_password_truncation():
    long_pass = "a" * 100
    hashed = hash_password(long_pass)
    assert verify_password(long_pass, hashed) is True

def test_register_user_success():
    payload = {
        "email": "john@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "password": "secretpassword"
    }
    response = client.post("/auth/register", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "john@example.com"
    assert "id" in data

def test_register_user_invalid_email():
    payload = {
        "email": "not-an-email",
        "first_name": "John",
        "last_name": "Doe",
        "password": "secretpassword"
    }
    response = client.post("/auth/register", json=payload)
    assert response.status_code == 422

def test_register_user_duplicate_email():
    payload = {
        "email": "duplicate@example.com",
        "first_name": "Dup",
        "last_name": "User",
        "password": "password123"
    }
    client.post("/auth/register", json=payload)
    response = client.post("/auth/register", json=payload)
    assert response.status_code == 400
    assert response.json()["detail"] == "Email already registered"

def test_login_success_and_invalid():
    # Register user
    reg_data = {
        "email": "login@example.com",
        "first_name": "Login",
        "last_name": "User",
        "password": "correctpassword"
    }
    client.post("/auth/register", json=reg_data)

    # Wrong password
    res_wrong = client.post("/auth/login", data={"username": "login@example.com", "password": "wrong"})
    assert res_wrong.status_code == 401

    # Wrong username
    res_nouser = client.post("/auth/login", data={"username": "nobody@example.com", "password": "correctpassword"})
    assert res_nouser.status_code == 401

    # Correct login
    res_ok = client.post("/auth/login", data={"username": "login@example.com", "password": "correctpassword"})
    assert res_ok.status_code == 200
    token = res_ok.json()["access_token"]

    # Verify token
    ver_res = client.get(f"/auth/verify?token={token}")
    assert ver_res.status_code == 200
    assert ver_res.json()["email"] == "login@example.com"

    # GET /auth/me
    me_res = client.get(f"/auth/me?token={token}")
    assert me_res.status_code == 200
    assert me_res.json()["email"] == "login@example.com"

def test_verify_and_me_invalid_tokens():
    # Invalid token string
    assert client.get("/auth/verify?token=invalid").status_code == 401
    assert client.get("/auth/me?token=invalid").status_code == 401

    # Token with missing 'sub'
    token_nosub = jwt.encode({"email": "test@example.com"}, settings.secret_key, algorithm=settings.algorithm)
    assert client.get(f"/auth/verify?token={token_nosub}").status_code == 401
    assert client.get(f"/auth/me?token={token_nosub}").status_code == 401

    # Token for non-existent user ID
    token_nouser = jwt.encode({"sub": "99999", "email": "ghost@example.com"}, settings.secret_key, algorithm=settings.algorithm)
    assert client.get(f"/auth/me?token={token_nouser}").status_code == 404

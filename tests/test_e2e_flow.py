import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import sys, os

# Setup sys.path for microservices imports
sys.path.insert(0, os.path.abspath("auth-service"))
sys.path.insert(0, os.path.abspath("expense-service"))
sys.path.insert(0, os.path.abspath("category-service"))
sys.path.insert(0, os.path.abspath("analytics-service"))
sys.path.insert(0, os.path.abspath("api-gateway"))

from app.database import Base as AuthBase, get_db as auth_get_db
from app.main import app as auth_app

# Set up test DB for Auth Service
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_auth_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

AuthBase.metadata.create_all(bind=engine)
auth_app.dependency_overrides[auth_get_db] = override_auth_db

auth_client = TestClient(auth_app)

def test_full_auth_end_to_end():
    # 1. Register new user
    reg_res = auth_client.post(
        "/auth/register",
        json={
            "email": "e2e.user@example.com",
            "first_name": "E2E",
            "last_name": "Tester",
            "password": "SecurePassword123!"
        }
    )
    assert reg_res.status_code == 200
    reg_data = reg_res.json()
    assert reg_data["email"] == "e2e.user@example.com"
    user_id = reg_data["id"]

    # 2. Test Invalid Email Format Validation
    invalid_email_res = auth_client.post(
        "/auth/register",
        json={
            "email": "invalid-email-string",
            "first_name": "E2E",
            "last_name": "Tester",
            "password": "SecurePassword123!"
        }
    )
    assert invalid_email_res.status_code == 422

    # 3. Test Duplicate Email Registration
    dup_res = auth_client.post(
        "/auth/register",
        json={
            "email": "e2e.user@example.com",
            "first_name": "E2E",
            "last_name": "Tester",
            "password": "SecurePassword123!"
        }
    )
    assert dup_res.status_code == 400
    assert dup_res.json()["detail"] == "Email already registered"

    # 4. Login to obtain JWT Token
    login_res = auth_client.post(
        "/auth/login",
        data={"username": "e2e.user@example.com", "password": "SecurePassword123!"}
    )
    assert login_res.status_code == 200
    token_data = login_res.json()
    assert "access_token" in token_data
    token = token_data["access_token"]

    # 5. Fetch User Profile (/auth/me)
    me_res = auth_client.get(f"/auth/me?token={token}")
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert me_data["id"] == user_id
    assert me_data["email"] == "e2e.user@example.com"

    # 6. Verify Token (/auth/verify)
    verify_res = auth_client.get(f"/auth/verify?token={token}")
    assert verify_res.status_code == 200
    assert verify_res.json()["valid"] is True
    assert verify_res.json()["user_id"] == user_id

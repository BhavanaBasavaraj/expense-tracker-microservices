import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import sys, os
sys.path.insert(0, os.path.abspath("category-service"))

from app.database import Base, get_db
from app.main import app
from app.routers.categories import get_current_user

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

def override_get_current_user():
    return {"user_id": 1, "email": "test.user@example.com"}

Base.metadata.create_all(bind=engine)
app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_user] = override_get_current_user

client = TestClient(app)

def test_category_crud_flow():
    # 1. Create category
    create_res = client.post(
        "/categories/",
        json={"name": "Food & Dining", "type": "expense"},
        headers={"Authorization": "Bearer fake-token"}
    )
    assert create_res.status_code == 200
    cat = create_res.json()
    assert cat["name"] == "Food & Dining"
    assert cat["type"] == "expense"
    cat_id = cat["id"]

    # 2. Get list of categories
    list_res = client.get("/categories/", headers={"Authorization": "Bearer fake-token"})
    assert list_res.status_code == 200
    categories = list_res.json()
    assert len(categories) == 1
    assert categories[0]["id"] == cat_id

    # 3. Delete category
    del_res = client.delete(f"/categories/{cat_id}", headers={"Authorization": "Bearer fake-token"})
    assert del_res.status_code == 200
    assert del_res.json()["message"] == "Category deleted"

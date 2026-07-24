import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import sys, os
sys.path.insert(0, os.path.abspath("expense-service"))

from app.database import Base, get_db
from app.main import app
from app.routers.expenses import get_current_user

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

def test_expense_crud_flow():
    # 1. Create expense
    create_res = client.post(
        "/expenses/",
        json={
            "title": "Groceries",
            "amount": 150.50,
            "type": "expense",
            "date": "2026-07-24",
            "description": "Weekly supermarket shopping"
        },
        headers={"Authorization": "Bearer fake-token"}
    )
    assert create_res.status_code == 200
    created = create_res.json()
    assert created["id"] is not None
    assert created["title"] == "Groceries"
    assert created["amount"] == 150.50
    expense_id = created["id"]

    # 2. Get list of expenses
    list_res = client.get("/expenses/", headers={"Authorization": "Bearer fake-token"})
    assert list_res.status_code == 200
    expenses = list_res.json()
    assert len(expenses) == 1
    assert expenses[0]["id"] == expense_id

    # 3. Update expense
    update_res = client.put(
        f"/expenses/{expense_id}",
        json={
            "title": "Supermarket Groceries",
            "amount": 175.00,
            "type": "expense",
            "date": "2026-07-24",
            "description": "Updated supermarket shopping"
        },
        headers={"Authorization": "Bearer fake-token"}
    )
    assert update_res.status_code == 200
    updated = update_res.json()
    assert updated["title"] == "Supermarket Groceries"
    assert updated["amount"] == 175.00

    # 4. Delete expense
    del_res = client.delete(f"/expenses/{expense_id}", headers={"Authorization": "Bearer fake-token"})
    assert del_res.status_code == 200
    assert del_res.json()["message"] == "Expense deleted"

    # 5. Verify empty list after deletion
    list_res_after = client.get("/expenses/", headers={"Authorization": "Bearer fake-token"})
    assert list_res_after.status_code == 200
    assert len(list_res_after.json()) == 0

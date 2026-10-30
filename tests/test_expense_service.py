import pytest
from fastapi.testclient import TestClient
import sys, os

sys.path.insert(0, os.path.abspath("expense-service"))

from app.main import app
from app.config import settings

client = TestClient(app)

KEY = os.environ["INTERNAL_API_KEY"]


def gw(user_id, email="test@example.com"):
    """Headers exactly as the API gateway would send them."""
    return {"X-User-ID": str(user_id), "X-User-Email": email, "X-Internal-Key": KEY}


def payload(title="Groceries", amount=150.75):
    return {
        "title": title,
        "amount": amount,
        "type": "expense",
        "date": "2026-07-24",
        "category_id": 1,
        "description": "Weekly grocery shopping",
    }


def test_expense_health():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["service"] == "expense"


def test_expense_crud_flow():
    headers = gw(1)

    create_res = client.post("/expenses/", json=payload(), headers=headers)
    assert create_res.status_code == 200
    expense = create_res.json()
    assert expense["title"] == "Groceries"
    assert expense["user_id"] == 1
    exp_id = expense["id"]

    get_res = client.get("/expenses/", headers=headers)
    assert get_res.status_code == 200
    assert any(e["id"] == exp_id for e in get_res.json())

    update_res = client.put(
        f"/expenses/{exp_id}", json=payload("Supermarket Groceries", 175.00), headers=headers
    )
    assert update_res.status_code == 200
    assert update_res.json()["title"] == "Supermarket Groceries"

    del_res = client.delete(f"/expenses/{exp_id}", headers=headers)
    assert del_res.status_code == 200
    assert del_res.json()["message"] == "Expense deleted"
    assert not any(e["id"] == exp_id for e in client.get("/expenses/", headers=headers).json())


def test_expense_not_found_errors():
    assert client.put("/expenses/99999", json=payload("Test", 10.0), headers=gw(1)).status_code == 404
    assert client.delete("/expenses/99999", headers=gw(1)).status_code == 404


# ---------------------------------------------------------------- tenant isolation

def test_user_cannot_list_another_users_expenses():
    exp_id = client.post("/expenses/", json=payload("Private rent"), headers=gw(10)).json()["id"]
    other = client.get("/expenses/", headers=gw(11)).json()
    assert not any(e["id"] == exp_id for e in other)


def test_user_cannot_update_another_users_expense():
    exp_id = client.post("/expenses/", json=payload("Original", 10.0), headers=gw(20)).json()["id"]

    res = client.put(f"/expenses/{exp_id}", json=payload("Hijacked", 999.0), headers=gw(21))
    assert res.status_code == 404  # indistinguishable from "does not exist"

    # The owner's row is untouched.
    mine = [e for e in client.get("/expenses/", headers=gw(20)).json() if e["id"] == exp_id][0]
    assert mine["title"] == "Original"
    assert mine["amount"] == 10.0


def test_user_cannot_delete_another_users_expense():
    exp_id = client.post("/expenses/", json=payload("Keep me"), headers=gw(30)).json()["id"]

    assert client.delete(f"/expenses/{exp_id}", headers=gw(31)).status_code == 404

    assert any(e["id"] == exp_id for e in client.get("/expenses/", headers=gw(30)).json())


def test_body_cannot_set_owner():
    body = payload("Mass assignment")
    body["user_id"] = 999  # attacker tries to plant a row under someone else
    res = client.post("/expenses/", json=body, headers=gw(40))
    assert res.status_code == 200
    assert res.json()["user_id"] == 40
    assert client.get("/expenses/", headers=gw(999)).json() == []


# ------------------------------------------------- only the gateway may assert identity

def test_forged_identity_without_internal_key_is_rejected():
    # What an attacker who can reach the service directly would send.
    res = client.get("/expenses/", headers={"X-User-ID": "1"})
    assert res.status_code == 401


def test_wrong_internal_key_is_rejected():
    res = client.get("/expenses/", headers={"X-User-ID": "1", "X-Internal-Key": "guess"})
    assert res.status_code == 401


def test_internal_key_without_identity_is_rejected():
    assert client.get("/expenses/", headers={"X-Internal-Key": KEY}).status_code == 401


def test_service_fails_closed_when_no_key_configured(monkeypatch):
    monkeypatch.setattr(settings, "internal_api_key", "")
    res = client.get("/expenses/", headers={"X-User-ID": "1", "X-Internal-Key": ""})
    assert res.status_code == 401


def test_bearer_token_alone_is_not_accepted_and_auth_service_is_not_called(httpx_mock):
    # The old fallback called the auth service. It must be gone: no outbound request at all.
    res = client.get("/expenses/", headers={"Authorization": "Bearer anything"})
    assert res.status_code == 401
    assert httpx_mock.get_requests() == []


def test_expense_unauthorized():
    assert client.get("/expenses/").status_code == 401


# ------------------------------------------------------------------ input validation

@pytest.mark.parametrize("field,value", [
    ("type", "transfer"),          # only income / expense exist
    ("type", ""),
    ("date", "yesterday"),
    ("date", "2026-13-45"),        # not a calendar date
    ("date", "2026-02-30"),
    ("amount", 0),
    ("amount", -5.0),
    ("title", ""),
    ("title", "   "),              # whitespace only
    ("title", "x" * 201),
])
def test_invalid_expense_is_rejected_on_create_and_update(field, value):
    bad = payload()
    bad[field] = value
    assert client.post("/expenses/", json=bad, headers=gw(50)).status_code == 422

    good_id = client.post("/expenses/", json=payload("valid"), headers=gw(50)).json()["id"]
    assert client.put(f"/expenses/{good_id}", json=bad, headers=gw(50)).status_code == 422
    # and the rejected update changed nothing
    stored = [e for e in client.get("/expenses/", headers=gw(50)).json() if e["id"] == good_id][0]
    assert stored["title"] == "valid"


def test_non_finite_amounts_are_rejected():
    from app.schemas import ExpenseCreate
    from pydantic import ValidationError
    for bad in (float("nan"), float("inf"), float("-inf")):
        with pytest.raises(ValidationError):
            ExpenseCreate(title="t", amount=bad, type="expense", date="2026-01-01")


def test_valid_dates_are_normalised_and_income_accepted():
    body = payload("Paycheck", 3000.0)
    body["type"] = "income"
    body["date"] = "2026-07-04"
    res = client.post("/expenses/", json=body, headers=gw(51))
    assert res.status_code == 200
    assert res.json()["date"] == "2026-07-04" and res.json()["type"] == "income"


def test_internal_service_sends_no_cors_headers():
    # Only the gateway talks to browsers; this service must not invite cross-origin calls.
    res = client.options("/expenses/", headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "GET"})
    assert "access-control-allow-origin" not in res.headers

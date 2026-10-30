from fastapi import APIRouter, Depends, HTTPException, Header, Request
from typing import Optional
import hmac
import httpx
from app.config import settings

router = APIRouter(prefix="/analytics", tags=["analytics"])

def _is_trusted_gateway(provided_key: Optional[str]) -> bool:
    """True only if the caller presented the shared internal key (set by the gateway).

    Fails closed: if no key is configured, nothing is trusted.
    """
    expected = settings.internal_api_key
    if not expected or not provided_key:
        return False
    return hmac.compare_digest(provided_key.encode(), expected.encode())


async def get_current_user(
    x_user_id: Optional[int] = Header(None, alias="X-User-ID"),
    x_user_email: Optional[str] = Header(None, alias="X-User-Email"),
    x_internal_key: Optional[str] = Header(None, alias="X-Internal-Key"),
):
    # Identity is established ONCE, at the API gateway. This service only trusts
    # the gateway-supplied identity headers, and only when they arrive together
    # with the shared internal key. It never calls the auth service.
    if not _is_trusted_gateway(x_internal_key) or x_user_id is None:
        raise HTTPException(status_code=401, detail="Invalid or missing authentication credentials")
    return {"user_id": x_user_id, "email": x_user_email or ""}

async def get_expenses(request: Request, user_id: int):
    headers = {"X-User-ID": str(user_id), "X-Internal-Key": settings.internal_api_key}

    client: httpx.AsyncClient = getattr(request.app.state, "http_client", None)
    try:
        if client:
            response = await client.get(
                f"{settings.expense_service_url}/expenses/",
                headers=headers
            )
        else:
            async with httpx.AsyncClient() as temp_client:
                response = await temp_client.get(
                    f"{settings.expense_service_url}/expenses/",
                    headers=headers,
                    timeout=10.0
                )
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Failed to fetch expenses")
        data = response.json()
        if not isinstance(data, list):
            raise HTTPException(status_code=500, detail="Invalid response format from expense service")
        return data
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="Expense service unavailable")

@router.get("/dashboard")
async def dashboard(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    expenses = await get_expenses(request, current_user["user_id"])

    total_income = sum(e["amount"] for e in expenses if e["type"] == "income")
    total_expenses = sum(e["amount"] for e in expenses if e["type"] == "expense")

    return {
        "total_income": total_income,
        "total_expenses": total_expenses,
        "net_balance": total_income - total_expenses,
        "total_transactions": len(expenses)
    }

@router.get("/by-category")
async def by_category(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    expenses = await get_expenses(request, current_user["user_id"])

    breakdown = {}
    for e in expenses:
        cat_id = str(e.get("category_id", "uncategorized"))
        if cat_id not in breakdown:
            breakdown[cat_id] = {"total": 0, "count": 0}
        breakdown[cat_id]["total"] += e["amount"]
        breakdown[cat_id]["count"] += 1

    return breakdown

@router.get("/monthly")
async def monthly(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    expenses = await get_expenses(request, current_user["user_id"])

    monthly = {}
    for e in expenses:
        month = e["date"][:7]  # YYYY-MM
        if month not in monthly:
            monthly[month] = {"income": 0, "expenses": 0}
        if e["type"] == "income":
            monthly[month]["income"] += e["amount"]
        else:
            monthly[month]["expenses"] += e["amount"]

    return monthly

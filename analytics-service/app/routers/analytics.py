from fastapi import APIRouter, Depends, HTTPException, Header
import httpx
from app.config import settings

router = APIRouter(prefix="/analytics", tags=["analytics"])

async def get_current_user(authorization: str = Header(...)):
    token = authorization.replace("Bearer ", "")
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{settings.auth_service_url}/auth/verify",
            params={"token": token}
        )
        if response.status_code != 200:
            raise HTTPException(status_code=401, detail="Invalid token")
        return response.json()

async def get_expenses(token: str, user_id: int):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{settings.expense_service_url}/expenses/",
            headers={"Authorization": f"Bearer {token}"}
        )
        return response.json()

@router.get("/dashboard")
async def dashboard(
    authorization: str = Header(...),
    current_user: dict = Depends(get_current_user)
):
    token = authorization.replace("Bearer ", "")
    expenses = await get_expenses(token, current_user["user_id"])

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
    authorization: str = Header(...),
    current_user: dict = Depends(get_current_user)
):
    token = authorization.replace("Bearer ", "")
    expenses = await get_expenses(token, current_user["user_id"])

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
    authorization: str = Header(...),
    current_user: dict = Depends(get_current_user)
):
    token = authorization.replace("Bearer ", "")
    expenses = await get_expenses(token, current_user["user_id"])

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

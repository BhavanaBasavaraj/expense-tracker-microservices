from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import List, Optional
import httpx
from app.database import get_db
from app.models import Expense
from app.schemas import ExpenseCreate, ExpenseResponse
from app.config import settings

router = APIRouter(prefix="/expenses", tags=["expenses"])

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

@router.get("/", response_model=List[ExpenseResponse])
async def get_expenses(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    return db.query(Expense).filter(
        Expense.user_id == current_user["user_id"]
    ).all()

@router.post("/", response_model=ExpenseResponse)
async def create_expense(
    expense: ExpenseCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    new_expense = Expense(**expense.dict(), user_id=current_user["user_id"])
    db.add(new_expense)
    db.commit()
    db.refresh(new_expense)
    return new_expense

@router.put("/{expense_id}", response_model=ExpenseResponse)
async def update_expense(
    expense_id: int,
    expense: ExpenseCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    db_expense = db.query(Expense).filter(
        Expense.id == expense_id,
        Expense.user_id == current_user["user_id"]
    ).first()
    if not db_expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    for key, value in expense.dict().items():
        setattr(db_expense, key, value)
    db.commit()
    db.refresh(db_expense)
    return db_expense

@router.delete("/{expense_id}")
async def delete_expense(
    expense_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    db_expense = db.query(Expense).filter(
        Expense.id == expense_id,
        Expense.user_id == current_user["user_id"]
    ).first()
    if not db_expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    db.delete(db_expense)
    db.commit()
    return {"message": "Expense deleted"}

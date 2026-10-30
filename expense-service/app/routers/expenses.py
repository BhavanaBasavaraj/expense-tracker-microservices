from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import List, Optional
import hmac
from app.database import get_db
from app.models import Expense
from app.schemas import ExpenseCreate, ExpenseResponse
from app.config import settings

router = APIRouter(prefix="/expenses", tags=["expenses"])

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
    data = expense.model_dump() if hasattr(expense, "model_dump") else expense.dict()
    new_expense = Expense(**data, user_id=current_user["user_id"])
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
    data = expense.model_dump() if hasattr(expense, "model_dump") else expense.dict()
    for key, value in data.items():
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

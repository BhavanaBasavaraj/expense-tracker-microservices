from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import List, Optional
import hmac
from app.database import get_db
from app.models import Category
from app.schemas import CategoryCreate, CategoryResponse
from app.config import settings

router = APIRouter(prefix="/categories", tags=["categories"])

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

@router.get("/", response_model=List[CategoryResponse])
async def get_categories(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    return db.query(Category).filter(
        Category.user_id == current_user["user_id"]
    ).all()

@router.post("/", response_model=CategoryResponse)
async def create_category(
    category: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    data = category.model_dump() if hasattr(category, "model_dump") else category.dict()
    new_category = Category(**data, user_id=current_user["user_id"])
    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    return new_category

@router.delete("/{category_id}")
async def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    category = db.query(Category).filter(
        Category.id == category_id,
        Category.user_id == current_user["user_id"]
    ).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    db.delete(category)
    db.commit()
    return {"message": "Category deleted"}

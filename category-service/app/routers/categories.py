from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import List, Optional
import httpx
from app.database import get_db
from app.models import Category
from app.schemas import CategoryCreate, CategoryResponse
from app.config import settings

router = APIRouter(prefix="/categories", tags=["categories"])

async def get_current_user(
    x_user_id: Optional[int] = Header(None, alias="X-User-ID"),
    x_user_email: Optional[str] = Header(None, alias="X-User-Email"),
    authorization: Optional[str] = Header(None)
):
    if x_user_id is not None:
        return {"user_id": x_user_id, "email": x_user_email or ""}
    
    if authorization:
        token = authorization.replace("Bearer ", "").strip()
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{settings.auth_service_url}/auth/verify",
                    params={"token": token},
                    timeout=10.0
                )
                if response.status_code == 200:
                    return response.json()
        except httpx.RequestError:
            pass
    raise HTTPException(status_code=401, detail="Invalid or missing authentication credentials")

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

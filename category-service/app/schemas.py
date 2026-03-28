from pydantic import BaseModel
from datetime import datetime

class CategoryCreate(BaseModel):
    name: str
    type: str

class CategoryResponse(BaseModel):
    id: int
    user_id: int
    name: str
    type: str
    created_at: datetime

    class Config:
        from_attributes = True

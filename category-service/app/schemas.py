from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import Literal

class CategoryCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=100)
    type: Literal["income", "expense"]

class CategoryResponse(BaseModel):
    id: int
    user_id: int
    name: str
    type: str
    created_at: datetime

    class Config:
        from_attributes = True

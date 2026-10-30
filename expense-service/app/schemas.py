from pydantic import BaseModel, ConfigDict, Field, field_validator
from datetime import datetime, date as _date
from typing import Literal, Optional

class ExpenseCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    title: str = Field(min_length=1, max_length=200)
    amount: float = Field(gt=0, allow_inf_nan=False)
    type: Literal["income", "expense"]
    date: str
    category_id: Optional[int] = None
    description: Optional[str] = Field(default=None, max_length=1000)

    @field_validator("date")
    @classmethod
    def _valid_iso_date(cls, v: str) -> str:
        try:
            return _date.fromisoformat(v).isoformat()
        except ValueError:
            raise ValueError("date must be a valid calendar date in YYYY-MM-DD format")

class ExpenseResponse(BaseModel):
    id: int
    user_id: int
    title: str
    amount: float
    type: str
    date: str
    category_id: Optional[int]
    description: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

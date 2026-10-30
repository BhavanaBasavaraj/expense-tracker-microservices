from pydantic import BaseModel, EmailStr, Field
from datetime import datetime

class UserCreate(BaseModel):
    email: EmailStr
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    # bcrypt only uses the first 72 bytes, so longer passwords would be silently truncated.
    password: str = Field(min_length=8, max_length=72)

class UserResponse(BaseModel):
    id: int
    email: str
    first_name: str
    last_name: str
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    user_id: int
    email: str

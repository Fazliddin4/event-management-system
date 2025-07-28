from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str = Field(min_length=8, max_length=16)

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "username": "book_admin",
                "email": "admin@bookla.com",
                "password": "password123"
            }
        },
    }

class UserRegisterOut(BaseModel):
    id: int
    username: str | None = None
    email: EmailStr 
    is_active: bool
    is_verified: bool    
    created_at: datetime

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": 2,
                "username": "username",
                "email": "user@gmail.com",
                "is_active": True,
                "is_verified": True,
                "created_at": "2025-01-01 13:00:00.000",
            }
        },
    }





class UserJWTLogin(BaseModel): 
    email: EmailStr
    password: str



class JWTRefreshIn(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    email: EmailStr
    access_token: str
    refresh_token: str
    token_type: str




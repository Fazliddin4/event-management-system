from pydantic import BaseModel, EmailStr
from datetime import datetime


class UserRegisterIn(BaseModel):
    username: str
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    email: EmailStr
    username: str | None = None
    is_active: bool
    created_at: datetime


class TokenIn(BaseModel):
    refresh_token: str


class TokenOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class EventCreateIn(BaseModel):
    title: str
    description: str | None = None
    start_datetime: datetime
    end_datetime: datetime
    location: str | None = None
    max_participants: int | None = 100

class EventUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    start_datetime: datetime | None = None
    end_datetime: datetime | None = None
    location: str | None = None
    max_participants: int | None = None
    is_active: bool | None = True

class EventOut(BaseModel):
    id: int
    title: str
    description: str | None = None
    start_datetime: datetime
    end_datetime: datetime
    location: str | None = None
    max_participants: int | None = 100
    is_active: bool
    created_at: datetime

class EventRegistrationCreateIn(BaseModel):
    user_id: int
    event_id: int
    status: str | None = "waitlist"

class EventRegistrationOut(BaseModel):
    id: int
    user_id: int
    event_id: int
    registered_at: datetime
    status: str


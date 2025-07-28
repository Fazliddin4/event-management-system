import os

from datetime import UTC, datetime, timedelta
from app.models import User
from jose import jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from app.models import Event
from app.schemas.event import EventCreate, EventUpdate

ACCESS_TOKEN_EXPIRE_MINUTES=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))
ALGORITHM=os.getenv("ALGORITHM")
SECRET_KEY=os.getenv("SECRET_KEY")

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def hash_password(password: str):
    return pwd_context.hash(password)


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def create_jwt_token(data: dict, expires_delta: float | None = None):
    delta = (
        timedelta(minutes=expires_delta)
        if expires_delta
        else timedelta(days=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    expire_time = datetime.now(UTC) + delta
    data.update({"exp": expire_time})

    jwt_token = jwt.encode(data, SECRET_KEY, ALGORITHM)

    return jwt_token


def generate_confirmation_token(email):
    """Generate JWT token"""
    payload = {
        "email": email,
        "exp": datetime.now(UTC) + timedelta(hours=1),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def get_event(db: Session, event_id: int):
    return db.query(Event).filter(Event.id == event_id).first()

def get_events(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Event).offset(skip).limit(limit).all()

def create_event(db: Session, event: EventCreate, user: User):
    db_event = Event(**event.dict(), organizer_id=user.id)
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event

def update_event(db: Session, db_event: Event, updates: EventUpdate):
    for key, value in updates.dict().items():
        setattr(db_event, key, value)
    db.commit()
    db.refresh(db_event)
    return db_event

def delete_event(db: Session, db_event: Event):
    db.delete(db_event)
    db.commit()

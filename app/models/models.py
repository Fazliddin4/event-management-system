

from datetime import datetime, UTC
from enum import Enum as PyEnum

from sqlalchemy import (
    String, Integer, DateTime, Boolean, ForeignKey, Enum
)
from sqlalchemy.orm import (
    relationship, Mapped, mapped_column, declarative_base
)

from app.database import Base


class RegistrationStatus(PyEnum):
    confirmed = "confirmed"
    cancelled = "cancelled"
    waitlist = "waitlist"


class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True)
    email: Mapped[str] = mapped_column(String(100), unique=True)
    hashed_password: Mapped[str] = mapped_column(String(128))
    is_active: Mapped[bool] = mapped_column(default=True)
    is_verified: Mapped[bool] = mapped_column(default=False)
    is_admin: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now(UTC))

    events: Mapped[list["Event"]] = relationship(
        back_populates="organizer"
    )

    registrations: Mapped[list["EventRegistration"]] = relationship(
        back_populates="user"
    )



class Event(Base):
    __tablename__ = 'events'

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(String(500), nullable=True)
    start_datetime: Mapped[datetime] = mapped_column(default=datetime.now(UTC))
    end_datetime: Mapped[datetime] = mapped_column(default=datetime.now(UTC))
    location: Mapped[str] = mapped_column(String(200), nullable=True)
    max_participants: Mapped[int] = mapped_column(default=100)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now(UTC))

    organizer_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    organizer: Mapped["User"] = relationship(back_populates="events")

    registrations: Mapped[list["EventRegistration"]] = relationship(
        back_populates="event"
    )



class EventRegistration(Base):
    __tablename__ = 'event_registrations'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id"))
    registered_at: Mapped[datetime] = mapped_column(default=datetime.now(UTC))
    status: Mapped[RegistrationStatus] = mapped_column(
        Enum(RegistrationStatus), default=RegistrationStatus.waitlist
    )

    user: Mapped["User"] = relationship(back_populates="registrations")
    event: Mapped["Event"] = relationship(back_populates="registrations")

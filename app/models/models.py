from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey, Enum
from datetime import datetime, UTC
from app.database import Base
import enum


class RegistrationStatus(str, enum.Enum):
    confirmed = "confirmed"
    cancelled = "cancelled"
    waitlist = "waitlist"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str]=mapped_column(String, unique=True)
    email: Mapped[str] = mapped_column(String, nullable=False)
    password_hash: Mapped[str] = mapped_column(String)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(UTC))

    events: Mapped[list["Event"]] = relationship(back_populates="organizer")
    registrations: Mapped[list["EventRegistration"]] = relationship(back_populates="user")


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=True)
    start_datetime: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_datetime: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    location: Mapped[str] = mapped_column(String, nullable=False)
    max_participants: Mapped[int] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(UTC))

    organizer_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    organizer: Mapped["User"] = relationship(back_populates="events")

    registrations: Mapped[list["EventRegistration"]] = relationship(back_populates="event")


class EventRegistration(Base):
    __tablename__ = "event_registrations"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id"), nullable=False)
    registered_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(UTC))
    status: Mapped[RegistrationStatus] = mapped_column(Enum(RegistrationStatus), default=RegistrationStatus.confirmed)

    user: Mapped["User"] = relationship(back_populates="registrations")
    event: Mapped["Event"] = relationship(back_populates="registrations")

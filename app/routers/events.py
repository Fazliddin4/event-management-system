from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List
from app.models.models import RegistrationStatus as Status
from sqlalchemy import func
from typing import Optional


from app.dependencies import db_dep, current_user_dep
from app.models import Event, User, EventRegistration
from app.schemas.schemas import EventCreateIn, EventOut, EventUpdate, EventRegistrationOut, EventRegistrationCreateIn

router = APIRouter(prefix="/events", tags=["events"])

@router.get("/", response_model=List[EventOut])
async def get_events(
    db: db_dep,
    current_user: current_user_dep
):
    events = db.query(Event).all()
    return events


@router.post("/", response_model=EventOut, status_code=status.HTTP_201_CREATED)
async def create_event(
    event: EventCreateIn,
    db: db_dep,
    current_user: current_user_dep
):
    db_event = Event(**event.model_dump(), organizer_id=current_user.id)
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event


@router.get("/{event_id}", response_model=EventOut)
async def get_event(
    event_id: int,
    db: db_dep,
    current_user: current_user_dep
):
    db_event = db.query(Event).filter(Event.id == event_id).first()
    if not db_event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    return db_event


@router.put("/{event_id}", response_model=EventOut)
async def update_event(
    event_id: int,
    event_update: EventUpdate,
    db: db_dep,
    current_user: current_user_dep
):
    db_event = db.query(Event).filter(Event.id == event_id).first()
    if not db_event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    if db_event.organizer_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to update this event"
        )
    
    update_data = event_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_event, field, value)
    
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    
    return db_event


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(
    event_id: int,
    db: db_dep,
    current_user: current_user_dep
):
    db_event = db.query(Event).filter(Event.id == event_id).first()
    if not db_event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    if db_event.organizer_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to delete this event"
        )
    
    db.delete(db_event)
    db.commit()
    
    return None

@router.post("/{event_id}/register", status_code=status.HTTP_201_CREATED)
async def register_for_event(
    event_id: int,
    db: db_dep,
    current_user: current_user_dep
):
    event = db.query(Event).filter(
        Event.id == event_id,
        Event.is_active == True
    ).first()
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found or inactive"
        )
    
    existing_registration = db.query(EventRegistration).filter(
        EventRegistration.event_id == event_id,
        EventRegistration.user_id == current_user.id,
        EventRegistration.status != Status.cancelled
    ).first()
    
    if existing_registration:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You are already registered for this event"
        )
    
    confirmed_count = db.query(func.count(EventRegistration.id)).filter(
        EventRegistration.event_id == event_id,
        EventRegistration.status == Status.confirmed
    ).scalar()


    status_value = Status.confirmed if confirmed_count < event.max_participants else Status.waitlist

    registration = EventRegistration(
        user_id=current_user.id,
        event_id=event_id,
        status=status_value
    )
    
    db.add(registration)
    db.commit()
    db.refresh(registration)
    
    return {
        "message": f"Successfully registered for event. Status: {status_value.value}",
        "status": status_value.value,
        "registration_id": registration.id
    }


@router.delete("/{event_id}/register", status_code=status.HTTP_200_OK)
async def cancel_registration(
    event_id: int,
    db: db_dep,
    current_user: current_user_dep
):
    registration = db.query(EventRegistration).filter(
        EventRegistration.event_id == event_id,
        EventRegistration.user_id == current_user.id,
        EventRegistration.status != Status.cancelled
    ).first()
    
    if not registration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active registration found for this event"
        )
    
    previous_status = registration.status

    registration.status = Status.cancelled
    db.commit()

    if previous_status == Status.confirmed:
        waitlisted = db.query(EventRegistration).filter(
            EventRegistration.event_id == event_id,
            EventRegistration.status == Status.waitlist
        ).order_by(EventRegistration.registered_at.asc()).first()
        
        if waitlisted:
            waitlisted.status = Status.confirmed
            db.commit()
            
    
    return {"message": "Registration cancelled successfully"}


@router.get("/{event_id}/participants", response_model=List[dict])
async def get_event_participants(
    event_id: int,
    db: db_dep,
    current_user: current_user_dep,
    status: Optional[Status] = Query(None, description="Filter participants by status")
):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    if event.organizer_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view participant list"
        )
    
    query = db.query(
        User.username,
        User.email,
        EventRegistration.status,
        EventRegistration.registered_at
    ).join(
        EventRegistration,
        User.id == EventRegistration.user_id
    ).filter(
        EventRegistration.event_id == event_id,
        EventRegistration.status != Status.cancelled
    )
    

    if status:
        query = query.filter(EventRegistration.status == status)
    
    return query or []

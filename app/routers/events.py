from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.dependencies import get_current_user
from app.models import User
from app.dependencies import get_db
from app.schemas.event import EventCreate, EventUpdate, EventOut
from app.utils import (
    get_event as get_event_from_db,
    get_events as get_events_from_db,
    create_event as create_event_in_db,
    update_event as update_event_in_db,
    delete_event as delete_event_in_db,
)

router = APIRouter(prefix="/events", tags=["Events"])


@router.get("/", response_model=list[EventOut])
def list_events(
    skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
):
    return get_events_from_db(db=db, skip=skip, limit=limit)


@router.get("/{event_id}", response_model=EventOut)
def retrieve_event(event_id: int, db: Session = Depends(get_db)):
    event = get_event_from_db(db=db, event_id=event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


@router.post("/", response_model=EventOut, status_code=status.HTTP_201_CREATED)
def create_event(
    event: EventCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return create_event_in_db(db=db, event=event, user=current_user)


@router.put("/{event_id}", response_model=EventOut)
def update_event(event_id: int, event_data: EventUpdate, db: Session = Depends(get_db)):
    db_event = get_event_from_db(db=db, event_id=event_id)
    if not db_event:
        raise HTTPException(status_code=404, detail="Event not found")
    return update_event_in_db(db=db, db_event=db_event, updates=event_data)


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_event(event_id: int, db: Session = Depends(get_db)):
    db_event = get_event_from_db(db=db, event_id=event_id)
    if not db_event:
        raise HTTPException(status_code=404, detail="Event not found")
    delete_event_in_db(db=db, db_event=db_event)

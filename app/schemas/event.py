from pydantic import BaseModel
from datetime import datetime

class EventBase(BaseModel):
    title: str
    description: str | None = None
    location: str | None = None
    start_datetime: datetime
    end_datetime: datetime

class EventCreate(EventBase):
    pass

class EventUpdate(EventBase):
    pass

class EventOut(EventBase):
    id: int
    created_at: datetime

    model_config = {
        "from_attributes": True  
    }
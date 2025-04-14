from pydantic import BaseModel
from typing import List
from uuid import UUID
from datetime import datetime


const_events = {'journey.booked': "journey.booked.v1", 'journey.canceled': 'journey.canceled.v1',
                'journey.approved': 'journey.approved.v1', 'journey.rejected': 'journey.rejected.v1'}


class JourneyBookedEvent(BaseModel):
    event_type: str = const_events['journey.booked']
    journey_id: UUID
    user_id: str
    route: List[str]
    origin_lat: float
    origin_lon: float
    destination_lat: float
    destination_lon: float
    scheduled_time: datetime
    timestamp: datetime


class JourneyCanceledEvent(BaseModel):
    event_type: str = const_events['journey.canceled']
    journey_id: UUID
    user_id: str
    scheduled_time: datetime
    timestamp: datetime


class JourneyApprovedEvent(BaseModel):
    event_type: str = const_events['journey.approved']
    journey_id: UUID
    user_id: str
    route: List[str]
    scheduled_time: datetime
    timestamp: datetime


class JourneyRejectedEvent(BaseModel):
    event_type: str = const_events['journey.rejected']
    journey_id: UUID
    user_id: str
    scheduled_time: datetime
    timestamp: datetime

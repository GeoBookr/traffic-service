# ./journey-booking-service/models/events.py

from pydantic import BaseModel
from typing import List
from uuid import UUID
from datetime import datetime


class JourneyBookedEvent(BaseModel):
    event_type: str = "journey.booked.v1"
    journey_id: UUID
    user_id: str
    route: List[str]
    origin_lat: float
    origin_lon: float
    destination_lat: float
    destination_lon: float
    timestamp: datetime


class JourneyCanceledEvent(BaseModel):
    event_type: str = "journey.canceled.v1"
    journey_id: UUID
    user_id: str
    timestamp: datetime


class JourneyApprovedEvent(BaseModel):
    event_type: str = "journey.approved.v1"
    journey_id: UUID
    user_id: str
    route: List[str]
    timestamp: datetime


class JourneyRejectedEvent(BaseModel):
    event_type: str = "journey.rejected.v1"
    journey_id: UUID
    user_id: str
    timestamp: datetime

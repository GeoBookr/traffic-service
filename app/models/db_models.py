from sqlalchemy import Column, String, DateTime, Enum, Float, Integer, ForeignKey, JSON, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
import uuid
import enum
from datetime import datetime, timezone

Base = declarative_base()


class JourneyStatus(str, enum.Enum):
    pending = "pending"
    confirmed = "confirmed"
    rejected = "rejected"
    canceled = "canceled"


class Journey(Base):
    __tablename__ = "journeys"

    journey_id = Column(UUID(as_uuid=True),
                        primary_key=True, default=uuid.uuid4)
    user_id = Column(String, nullable=False)
    origin_lat = Column(Float, nullable=False)
    origin_lon = Column(Float, nullable=False)
    destination_lat = Column(Float, nullable=False)
    destination_lon = Column(Float, nullable=False)
    vehicle_type = Column(String, nullable=False)
    scheduled_time = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    status = Column(Enum(JourneyStatus), default=JourneyStatus.pending)


class RegionType(enum.Enum):
    city = "city"
    country = "country"


class Slot(Base):
    __tablename__ = "slots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    region_type = Column(Enum(RegionType), nullable=False)
    region_identifier = Column(String, nullable=False)
    slot_time = Column(DateTime, nullable=False)
    slots = Column(Integer, nullable=False)
    reserved = Column(Integer, nullable=False, default=0)
    continent = Column(String, nullable=True)
    __table_args__ = (UniqueConstraint('region_identifier',
                      'slot_time', name='uix_region_time'),)


class Route(Base):
    __tablename__ = "routes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    journey_id = Column(UUID(as_uuid=True), ForeignKey(
        "journeys.journey_id"), nullable=False)
    route = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

from sqlalchemy.orm import Session
from app.models.db_models import Journey, Slot, RegionType
from app.services.slot_service import get_or_create_slot, get_continent_for_city
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def monitor_reservation_failure(region_identifier: str, error: Exception):
    logger.warning(f"Reservation failure for {region_identifier}: {error}")


def reserve_slot_for_region(db: Session, region_type: RegionType, region_identifier: str, slot_time: datetime,  continent: str = None) -> None:
    try:
        slot = get_or_create_slot(
            db, region_type, region_identifier, slot_time, continent)
        available = slot.slots - slot.reserved
        if available < 1:
            raise Exception(f"Insufficient capacity for {region_identifier}")
        slot.reserved += 1
        db.add(slot)
    except Exception as e:
        monitor_reservation_failure(region_identifier, e)
        raise


def confirm_journey_and_reserve_slots(db: Session, journey_id: str, route: list[str], region_type: RegionType) -> bool:
    """
    Tries to reserve 1 slot on each region in the given route. All operations
    are executed within one transaction. If any reservation fails, the transaction
    is aborted and the journey status is updated to "rejected".
    """
    try:
        with db.begin():
            for region in route:
                continent_value = None
                if region_type == RegionType.city:
                    continent_value = get_continent_for_city(region)
                reserve_slot_for_region(
                    db, region_type, region, continent_value)
            journey = db.query(Journey).filter(
                Journey.journey_id == journey_id).first()
            if journey is None:
                raise Exception("Journey not found")
            journey.status = "confirmed"
            db.add(journey)
        return True
    except Exception as e:
        logger.error(f"Reservation error for journey {journey_id}: {e}")
        try:
            with db.begin():
                journey = db.query(Journey).filter(
                    Journey.journey_id == journey_id).first()
                if journey:
                    journey.status = "rejected"
                    db.add(journey)
        except Exception as e2:
            db.rollback()
            logger.error(f"Rollback error for journey {journey_id}: {e2}")
        return False

import logging
from sqlalchemy.orm import Session
from datetime import datetime
from app.models.db_models import Journey, Slot, RegionType, Route
from app.services.reservation_service import reserve_slot_for_region
from app.services.slot_service import get_continent_for_city

logger = logging.getLogger(__name__)


def release_slot_for_region(db: Session, region_type: RegionType, region_identifier: str, slot_time: datetime) -> None:
    """
    Compensation function to undo a reservation for a specific time slot.
    """
    try:
        slot = db.query(Slot).with_for_update().filter(
            Slot.region_identifier == region_identifier,
            Slot.region_type == region_type,
            Slot.slot_time == slot_time
        ).first()
        if not slot:
            logger.info(
                f"No slot found for region {region_identifier} at {slot_time} in compensation.")
            return
        if slot.reserved > 0:
            slot.reserved -= 1
            db.add(slot)
            db.flush()
            logger.info(
                f"Compensation: Released reservation for region '{region_identifier}' at {slot_time}")
    except Exception as comp_err:
        logger.error(
            f"Error during compensation for region '{region_identifier}' at {slot_time}: {comp_err}")
        raise


def saga_reservation(db: Session, journey_id: str, steps: list[dict], region_type: RegionType, route: list[str], slot_time: datetime) -> bool:
    """
    Orchestrates a saga that reserves a slot on each region along the journey.
    'steps' should be a list of dictionaries for each reservation step. For example:
        steps = [
            {"region": "EU-Cluster", "continent": "Europe"},
            {"region": "Asia-Cluster", "continent": "Asia"},
            {"region": "CityX", "continent": "Asia"}
        ]
    If all steps succeed, the journey status is updated to "confirmed".
    If any step fails, the previously reserved steps are undone (compensated) and
    the journey is marked as "rejected".
    """
    reserved_steps = []
    try:
        with db.begin():
            for step in steps:
                region = step["region"]
                continent_value = step.get("continent")
                if region_type == RegionType.city and not continent_value:
                    continent_value = get_continent_for_city(region)
                reserve_slot_for_region(
                    db, region_type, region,  slot_time, continent_value,)
                reserved_steps.append(step)

            journey = db.query(Journey).filter(
                Journey.journey_id == journey_id).first()
            if not journey:
                raise Exception("Journey not found during saga reservation.")
            journey.status = "confirmed"
            db.add(journey)

            route_entry = Route(
                journey_id=journey_id,
                route=route,
            )
            db.add(route_entry)
        logger.info(f"Saga reservation succeeded for journey {journey_id}")
        return True

    except Exception as saga_err:
        logger.error(
            f"Saga reservation error for journey {journey_id}: {saga_err}")
        try:
            with db.begin():
                for step in reserved_steps:
                    release_slot_for_region(
                        db, region_type, step["region"], slot_time)
                journey = db.query(Journey).filter(
                    Journey.journey_id == journey_id).first()
                if journey:
                    journey.status = "rejected"
                    db.add(journey)
            logger.info(f"Compensation completed for journey {journey_id}")
        except Exception as comp_err:
            logger.error(
                f"Compensation error for journey {journey_id}: {comp_err}")
        return False


def saga_release_slots(db: Session, journey_id: str, steps: list[dict], region_type: RegionType, slot_time: datetime) -> bool:
    """
    Orchestrates a compensation saga for releasing reserved slots when a journey is canceled.
    Uses the specific slot_time to uniquely identify the records.
    """
    try:
        txn = db.begin_nested() if db.in_transaction() else db.begin()
        with txn:
            for step in steps:
                region = step.get("region")
                release_slot_for_region(db, region_type, region, slot_time)
            journey = db.query(Journey).filter(
                Journey.journey_id == journey_id).first()
            if journey:
                journey.status = "canceled"
                db.add(journey)
        db.commit()
        logger.info(f"Saga slot release succeeded for journey {journey_id}")
        return True
    except Exception as saga_err:
        logger.error(
            f"Saga slot release error for journey {journey_id}: {saga_err}")
        return False

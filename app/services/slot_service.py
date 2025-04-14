import random
from sqlalchemy.orm import Session
from app.models.db_models import Slot, RegionType
from geopy.geocoders import Nominatim
import pycountry_convert as pc
import logging
from datetime import datetime
from psycopg.errors import LockNotAvailable
from tenacity import retry, stop_after_attempt, retry_if_exception_type, wait_random_exponential
logger = logging.getLogger(__name__)


def get_continent_for_city(city: str) -> str:
    try:
        geolocator = Nominatim(user_agent="traffic-service-get-city")
        location = geolocator.geocode(city)
        if location and location.raw.get("address"):
            address = location.raw["address"]
            country_code = address.get("country_code", None)
            if country_code:
                try:
                    continent_code = pc.country_alpha2_to_continent_code(
                        country_code.upper())
                    continent = pc.convert_continent_code_to_continent_name(
                        continent_code)
                    return continent
                except Exception as conv_e:
                    logger.error(
                        f"Error converting country code for city {city}: {conv_e}")
                    return "Unknown"
        return "Unknown"
    except Exception as e:
        print(f"Error getting continent for city {city}: {e}")
        return "Unknown"


@retry(
    wait=wait_random_exponential(multiplier=0.5, min=0.5, max=3),
    stop=stop_after_attempt(15),
    retry=retry_if_exception_type(LockNotAvailable)
)
def get_or_create_slot(db: Session, region_type: RegionType, region_identifier: str, slot_time: datetime, continent: str = None) -> Slot:
    try:
        slot = db.query(Slot).with_for_update(nowait=True).filter(
            Slot.region_identifier == region_identifier,
            Slot.region_type == region_type,
            Slot.slot_time == slot_time
        ).first()
    except Exception as lock_error:
        raise LockNotAvailable(
            f"Could not lock slot for {region_identifier}: {lock_error}")

    if slot is None:
        if region_type == RegionType.city and not continent:
            continent = get_continent_for_city(region_identifier)
        new_slots = random.randint(
            3, 10) if region_type == RegionType.city else random.randint(30, 100)
        slot = Slot(
            region_type=region_type,
            region_identifier=region_identifier,
            slot_time=slot_time,
            slots=new_slots,
            reserved=0,
            continent=continent or "Unknown"
        )
        db.add(slot)
        db.flush()
        db.refresh(slot)
    else:
        if region_type == RegionType.city and not slot.continent and continent:
            slot.continent = continent
            db.flush()
    return slot


def replicate_geo(db: Session, route_country_identifiers: list[str], route_continents: list[str]):
    logger.info(
        f"[slot_service] Simulating geo-replication for route spanning continents: {route_continents}")
    for country in route_country_identifiers:
        slot = db.query(Slot).filter(
            Slot.region_identifier == country,
            Slot.region_type == RegionType.country
        ).first()
        if slot:
            current = slot.continent or ""
            for continent in route_continents:
                if continent not in current:
                    current = (current + "," + continent).strip(",")
            slot.continent = current
            db.commit()
    return

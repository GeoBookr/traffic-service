import json
import logging
from app.domain.route_generator import generate_route, generate_city_route
from app.domain.country_mapper import coordinates_to_country_info
from app.messaging.publisher import publisher
from app.models.db_models import RegionType
from app.services.slot_service import replicate_geo
from app.services.saga_orchestrator import saga_reservation
from app.db.database import SessionLocal

logger = logging.getLogger(__name__)


async def handle_journey_event(event: dict):
    try:
        journey_id = event.get("journey_id")
        origin_lat = event.get("origin_lat")
        origin_lon = event.get("origin_lon")
        destination_lat = event.get("destination_lat")
        destination_lon = event.get("destination_lon")

        if None in (origin_lat, origin_lon, destination_lat, destination_lon):
            logger.error(f"Missing coordinate(s) in journey event: {event}")
            return

        origin_info = coordinates_to_country_info(origin_lat, origin_lon)
        destination_info = coordinates_to_country_info(
            destination_lat, destination_lon)

        if origin_info is None or destination_info is None:
            logger.error(
                f"Could not determine location info for journey event: {event}")
            return

        origin_country = origin_info[1]
        destination_country = destination_info[1]
        origin_city = origin_info[3]
        destination_city = destination_info[3]
        origin_continent = origin_info[2]
        destination_continent = destination_info[2]

        db = SessionLocal()

        if origin_country == destination_country:
            logger.info(
                f"Both locations in {origin_country} – using city-to-city routing.")
            route = generate_city_route(origin_city, destination_city)
            region_type = RegionType.city
        else:
            logger.info(
                f"Different countries ({origin_country} vs {destination_country}) – using country-to-country routing.")
            route = generate_route(origin_country, destination_country)
            region_type = RegionType.country
            continents_in_route = {origin_continent, destination_continent}
            if len(continents_in_route) > 1:
                replicate_geo(db, route, list(continents_in_route))

        logger.info(f"Route approved for journey {journey_id}: {route}")

        saga_steps = []
        for region in route:
            step = {"region": region}
            if region_type == RegionType.city:
                step["continent"] = origin_continent
            saga_steps.append(step)

        confirmed = saga_reservation(db, journey_id, saga_steps, region_type)
        if confirmed:
            logger.info(f"Journey {journey_id} confirmed and slots reserved.")
            await publisher.publish_event({
                "type": "journey.confirmed",
                "journey_id": journey_id,
                "route": route,
            })
        else:
            logger.error(
                f"Journey {journey_id} reservation failed. Marked as rejected.")
            await publisher.publish_event({
                "type": "journey.rejected",
                "journey_id": journey_id,
                "route": route,
            })
        db.close()
    except Exception as e:
        logger.exception(f"Error handling journey event: {e}")

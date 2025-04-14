import json
import logging
from datetime import datetime, timezone
from app.domain.route_generator import generate_route, generate_city_route
from app.domain.country_mapper import coordinates_to_country_info
from app.messaging.publisher import publisher
from app.models.db_models import RegionType
from app.models.db_models import Route, Slot
from fastapi.concurrency import run_in_threadpool
from app.services.slot_service import replicate_geo
from app.services.saga_orchestrator import saga_reservation, saga_release_slots
from app.db.database import SessionLocal
from sqlalchemy.future import select
from app.models.events import const_events, JourneyApprovedEvent, JourneyRejectedEvent, JourneyBookedEvent, JourneyCanceledEvent


logger = logging.getLogger(__name__)


async def handle_journey_event(event: dict):
    try:
        if event['event_type'] == const_events['journey.booked']:
            await handle_booking_event(event)
        elif event['event_type'] == const_events['journey.canceled']:
            await handle_canceling_event(event)
    except Exception as e:
        logger.exception(f"Error handling journey event: {e}")


async def handle_canceling_event(event: dict):
    event_instance: JourneyCanceledEvent = JourneyCanceledEvent.model_validate(
        event)

    db = SessionLocal()
    try:
        result = await run_in_threadpool(
            db.execute, select(Route).where(
                Route.journey_id == event_instance.journey_id)
        )
        route_entry = result.scalar_one_or_none()
        if not route_entry:
            logger.error(
                f"No route found for journey {event_instance.journey_id}")
            return

        route = route_entry.route

        sample_region = route[0]
        result_slot = await run_in_threadpool(
            db.execute, select(Slot).where(
                Slot.region_identifier == sample_region,
                Slot.slot_time == event_instance.scheduled_time
            )
        )
        sample_slot = result_slot.scalar_one_or_none()
        if sample_slot:
            region_type = sample_slot.region_type
        else:
            region_type = RegionType.country

        saga_steps = []
        for region in route:
            step = {"region": region}
            if region_type == RegionType.city:
                step["continent"] = sample_slot.continent if sample_slot else "Unknown"
            saga_steps.append(step)

        released = await run_in_threadpool(
            saga_release_slots, db,
            event_instance.journey_id, saga_steps, region_type, event_instance.scheduled_time
        )
        if released:
            logger.info(
                f"Slots successfully released for canceled journey {event_instance.journey_id}")
            cancelled_event = JourneyCanceledEvent(
                journey_id=event_instance.journey_id,
                user_id=event_instance.user_id,
                scheduled_time=event_instance.scheduled_time,
                timestamp=datetime.now(timezone.utc)
            )
            # await publisher.publish_event(
            #     cancelled_event.model_dump(), routing_key="journey.canceled.v1"
            # )
        else:
            logger.error(
                f"Failed to release slots for canceled journey {event_instance.journey_id}")

    finally:
        await run_in_threadpool(db.close)


async def handle_booking_event(event: dict):
    event_instance: JourneyBookedEvent = JourneyBookedEvent.model_validate(
        event)

    if None in (event_instance.origin_lat, event_instance.origin_lon, event_instance.destination_lat, event_instance.destination_lon):
        logger.error(f"Missing coordinate(s) in journey event: {event}")
        return

    origin_info = coordinates_to_country_info(
        event_instance.origin_lat, event_instance.origin_lon)
    destination_info = coordinates_to_country_info(
        event_instance.destination_lat, event_instance.destination_lon)

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
            await run_in_threadpool(replicate_geo, db, route, list(continents_in_route))

    logger.info(
        f"Route approved for journey {event_instance.journey_id}: {route}")

    saga_steps = []
    for region in route:
        step = {"region": region}
        if region_type == RegionType.city:
            step["continent"] = origin_continent
        saga_steps.append(step)

    confirmed = await run_in_threadpool(saga_reservation, db, event_instance.journey_id, saga_steps, region_type, route, event_instance.scheduled_time)
    current_time = datetime.now(timezone.utc)

    if confirmed:
        logger.info(
            f"Journey {event_instance.journey_id} confirmed and slots reserved.")
        approved_event = JourneyApprovedEvent(
            journey_id=event_instance.journey_id,
            user_id=event_instance.user_id,
            route=route,
            timestamp=current_time,
            scheduled_time=event_instance.scheduled_time
        )
        await publisher.publish_event(approved_event.model_dump(), routing_key="journey.approved.v1")
    else:
        logger.error(
            f"Journey {event_instance.journey_id} reservation failed. Marked as rejected.")
        rejected_event = JourneyRejectedEvent(
            journey_id=event_instance.journey_id,
            user_id=event_instance.user_id,
            timestamp=current_time,
            scheduled_time=event_instance.scheduled_time
        )
        await publisher.publish_event(rejected_event.model_dump(), routing_key="journey.rejected.v1")
    await run_in_threadpool(db.close)

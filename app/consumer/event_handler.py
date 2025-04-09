# ./traffic-service/app/consumer/event_handler.py
import json
from app.domain.route_generator import generate_route, generate_city_route
from app.domain.country_mapper import coordinates_to_country_info
from app.messaging.publisher import publisher
from app.models.slot_model import RegionType
from app.services.slot_service import get_or_create_slot, replicate_geo
from app.db.database import SessionLocal


async def handle_journey_event(event: dict):
    try:
        journey_id = event.get("journey_id")
        origin_lat = event.get("origin_lat")
        origin_lon = event.get("origin_lon")
        destination_lat = event.get("destination_lat")
        destination_lon = event.get("destination_lon")

        if None in (origin_lat, origin_lon, destination_lat, destination_lon):
            print(
                f"[event_handler] Missing coordinate(s) in journey event: {event}")
            return

        origin_info = coordinates_to_country_info(origin_lat, origin_lon)
        destination_info = coordinates_to_country_info(
            destination_lat, destination_lon)

        if origin_info is None or destination_info is None:
            print(
                f"[event_handler] Could not determine location info for journey event: {event}")
            return

        origin_country = origin_info[1]
        destination_country = destination_info[1]
        origin_city = origin_info[3]
        destination_city = destination_info[3]
        origin_continent = origin_info[2]
        destination_continent = destination_info[2]

        db = SessionLocal()

        if origin_country == destination_country:
            print(
                f"[event_handler] Both locations in {origin_country} – using city-to-city routing.")
            route = generate_city_route(origin_city, destination_city)
            for city in route:
                slot = get_or_create_slot(
                    db, RegionType.city, city, continent=origin_continent)
                current_count = 0
                if current_count >= slot.slots:
                    print(
                        f"[event_handler] Route blocked: city '{city}' capacity ({slot.slots}) exceeded.")
                    await publisher.publish_event({
                        "type": "route.rejected",
                        "journey_id": journey_id,
                        "reason": f"City {city} over capacity",
                        "route": route,
                    })
                    db.close()
                    return
        else:
            print(
                f"[event_handler] Different countries ({origin_country} vs {destination_country}) – using country-to-country routing.")
            route = generate_route(origin_country, destination_country)
            for country in route:
                slot = get_or_create_slot(db, RegionType.country, country)
                current_count = 0
                if current_count >= slot.slots:
                    print(
                        f"[event_handler] Route blocked: country '{country}' capacity ({slot.slots}) exceeded.")
                    await publisher.publish_event({
                        "type": "route.rejected",
                        "journey_id": journey_id,
                        "reason": f"Country {country} over capacity",
                        "route": route,
                    })
                    db.close()
                    return

            continents_in_route = {origin_continent, destination_continent}
            if len(continents_in_route) > 1:
                replicate_geo(db, route, list(continents_in_route))

        print(
            f"[event_handler] Route approved for journey {journey_id}: {route}")
        await publisher.publish_event({
            "type": "route.approved",
            "journey_id": journey_id,
            "route": route,
        })
        db.close()
    except Exception as e:
        print(f"[event_handler] Error handling journey event: {e}")

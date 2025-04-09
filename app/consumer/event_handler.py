import json
from app.domain.route_generator import generate_route, generate_city_route
from app.domain.rate_limiter import is_under_limit, is_under_city_limit
from app.messaging.publisher import publisher
from app.domain.country_mapper import coordinates_to_country_info


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
                f"[event_handler] Could not determine location information from coordinates for journey event: {event}")
            return

        origin_country = origin_info[1]
        destination_country = destination_info[1]
        origin_city = origin_info[3]
        destination_city = destination_info[3]

        if origin_country == destination_country:
            print(
                f"[event_handler] Both locations in {origin_country}: Using city-to-city route generation.")
            route = generate_city_route(origin_city, destination_city)
        else:
            print(
                f"[event_handler] Locations in different countries ({origin_country} vs {destination_country}): Using country-to-country routing.")
            route = generate_route(origin_country, destination_country)

        for loc in route:
            current_count = 0
            if origin_country == destination_country:
                if not is_under_city_limit(origin_country, loc, current_count):
                    print(
                        f"[event_handler] Route blocked: city {loc} exceeds limit")
                    await publisher.publish_event({
                        "type": "route.rejected",
                        "journey_id": journey_id,
                        "reason": f"City {loc} over capacity",
                        "route": route,
                    })
                    return
            else:
                if not is_under_limit(loc, current_count):
                    print(
                        f"[event_handler] Route blocked: country {loc} exceeds limit")
                    await publisher.publish_event({
                        "type": "route.rejected",
                        "journey_id": journey_id,
                        "reason": f"Country {loc} over capacity",
                        "route": route,
                    })
                    return

        print(f"[event_handler] Route approved for journey {journey_id}")
        print(
            f"[event_handler] Route: {route}, Origin: {origin_country}, Destination: {destination_country}")
        await publisher.publish_event({
            "type": "route.approved",
            "journey_id": journey_id,
            "route": route,
        })

    except Exception as e:
        print(f"[event_handler] Error handling journey event: {e}")

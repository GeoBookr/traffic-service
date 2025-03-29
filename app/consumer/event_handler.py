import json
from app.domain.route_generator import generate_route
from app.domain.rate_limiter import is_under_limit
from app.messaging.publisher import publisher
from app.domain.country_mapper import city_to_country


async def handle_journey_event(event: dict):
    try:
        journey_id = event.get("journey_id")
        origin = event.get("origin")
        destination = event.get("destination")
        if not origin or not destination:
            print(f"[event_handler] Invalid journey event: {event}")
            return
        try:
            test_origin = city_to_country(origin)
            print(
                f"[event_handler] test_origin: {test_origin}, origin: {origin}")
            test_destination = city_to_country(destination)
            print(
                f"[event_handler] test_destination: {test_destination}, destination: {destination}")
            if test_origin != origin:
                origin = test_origin
            if test_destination != destination:
                destination = test_destination
        except KeyError:
            print(
                f"[event_handler] Invalid city names: {origin}, {destination}")

        print(
            f"[event_handler] Processing journey {journey_id} from {origin} to {destination}"
        )
        route = generate_route(origin, destination)

        for country in route:
            # TODO: Replace with real traffic data
            current_count = 0
            if not is_under_limit(country, current_count):
                print(
                    f"[event_handler] Route blocked: {country} exceeds limit")

                await publisher.publish_event({
                    "type": "route.rejected",
                    "journey_id": journey_id,
                    "reason": f"Country {country} over capacity",
                    "route": route,
                })
                return

        print(f"[event_handler] Route approved for journey {journey_id}")
        await publisher.publish_event({
            "type": "route.approved",
            "journey_id": journey_id,
            "route": route,
        })

    except Exception as e:
        print(f"[event_handler] Error handling journey event: {e}")

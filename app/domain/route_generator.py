import random
from app.core.config import settings


def generate_route(origin: str, destination: str, max_stops: int = 5, seed: int = None) -> list[str]:
    if seed is not None:
        random.seed(seed)
    df = settings.GEO_DF
    continent_map = settings.CONTINENT_MAP
    if origin not in continent_map or destination not in continent_map:
        raise ValueError(f"Unknown country code(s): {origin}, {destination}")
    origin_continent = continent_map.get(origin)
    destination_continent = continent_map.get(destination)

    if not origin_continent or not destination_continent:
        candidates = df["country_code"].unique().tolist()
    else:
        candidates = df[
            (df["continent"] == origin_continent)
            | (df["continent"] == destination_continent)
        ]["country_code"].unique().tolist()

    candidates = [code for code in candidates if code not in (
        origin, destination)]

    random.shuffle(candidates)
    num_stops = random.randint(0, max_stops)
    print(
        f"[route] Generated route from {origin} to {destination}: {candidates[:num_stops]} (max_stops={max_stops})")

    return [origin] + candidates[:num_stops] + [destination]

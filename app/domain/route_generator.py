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
    return [origin] + candidates[:num_stops] + [destination]


def generate_city_route(origin_city: str, destination_city: str, max_stops: int = 3, seed: int = None) -> list[str]:
    if seed is not None:
        random.seed(seed)
    df = settings.GEO_DF
    matches = df[df["city"].str.lower() == origin_city.lower()]
    if matches.empty:
        raise ValueError(f"Unknown city: {origin_city}")
    country_code = matches.iloc[0]["country_code"]
    city_candidates = df[df["country_code"] ==
                         country_code]["city"].unique().tolist()
    city_candidates = [city for city in city_candidates if city.lower() not in (
        origin_city.lower(), destination_city.lower())]
    random.shuffle(city_candidates)
    num_stops = random.randint(0, max_stops)
    return [origin_city] + city_candidates[:num_stops] + [destination_city]

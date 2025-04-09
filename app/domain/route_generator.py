import random
import pycountry
import geonamescache


def generate_route(origin: str, destination: str, max_stops: int = 5, seed: int = None) -> list[str]:
    """
    Generates a country-to-country route using pycountry.
    Both origin and destination should be two-letter country codes (e.g., "US", "MX").
    """
    if seed is not None:
        random.seed(seed)
    all_countries = [country.alpha_2 for country in pycountry.countries]
    candidates = [code for code in all_countries if code not in (
        origin, destination)]
    random.shuffle(candidates)
    num_stops = random.randint(0, max_stops)
    return [origin] + candidates[:num_stops] + [destination]


def generate_city_route(origin_city: str, destination_city: str, max_stops: int = 5, seed: int = None) -> list[str]:
    """
    Generates a city-to-city route using geonamescache.

    It first tries to identify the country code for the origin city.
    If found, it gathers all cities in that country; if not, it falls back on a static list.
    """
    if seed is not None:
        random.seed(seed)
    gc = geonamescache.GeonamesCache()
    cities = gc.get_cities()

    origin_country = None
    for city_info in cities.values():
        if city_info['name'].lower() == origin_city.lower():
            origin_country = city_info['countrycode']
            break

    if origin_country:
        candidates = [city_info['name'] for city_info in cities.values(
        ) if city_info['countrycode'] == origin_country]
    else:
        candidates = ["San Francisco", "San Jose",
                      "Los Angeles", "Sacramento", "Oakland"]

    candidates = [city for city in candidates if city.lower() not in (
        origin_city.lower(), destination_city.lower())]
    random.shuffle(candidates)
    num_stops = random.randint(0, max_stops)
    return [origin_city] + candidates[:num_stops] + [destination_city]

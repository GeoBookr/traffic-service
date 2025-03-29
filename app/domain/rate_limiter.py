from app.core.config import settings


def is_under_limit(country_code: str, current_count: int = 0) -> bool:
    limit = settings.COUNTRY_LIMITS.get(country_code, 2)
    return current_count < limit


def is_under_city_limit(country_code: str, city: str, current_count: int = 0) -> bool:
    limit = settings.CITY_LIMITS.get(country_code, {}).get(city, 2)
    return current_count < limit

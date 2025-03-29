from app.core.config import settings


def city_to_country(city: str) -> str | None:
    df = settings.GEO_DF
    match = df[df["city"].str.lower() == city.lower()]
    if match.empty:
        return None
    return match.iloc[0]["country_code"]

from app.core.config import settings
from geopy.geocoders import Nominatim
import pycountry_convert as pc


def city_to_country(city: str) -> str | None:
    df = settings.GEO_DF
    match = df[df["city"].str.lower() == city.lower()]
    if match.empty:
        return None
    return match.iloc[0]["country_code"]


def coordinates_to_country_info(latitude: float, longitude: float) -> list[str] | None:
    try:
        geolocator = Nominatim(user_agent="traffic-service/1.0 (https://github.com/GeoBookr/traffic-service)")
        location = geolocator.reverse((latitude, longitude), language="en", timeout=10)
        if location:
            address = location.raw.get('address', {})
            country = address.get("country", "Unknown")
            country_code = address.get("country_code", "Unknown").upper()
            continent = "Unknown"
            if country_code != "Unknown":
                continent_code = pc.country_alpha2_to_continent_code(country_code)
                continent = pc.convert_continent_code_to_continent_name(continent_code)
            return [country, country_code, continent]
        else:
            return None

    except Exception as e:
        print(f"Error in geocoding: {e}")
        return None

# Coordinates cannot be randomly generated. They should lie within the territory of a real country.
# If you prefer to return the continent code, replace the `continent` in the returned list with `continent_code`.

# if __name__ == "__main__":
#     countryInfo = coordinates_to_country_info(16.681536,112.676332)
#     print(countryInfo)
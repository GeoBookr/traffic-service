from geopy.geocoders import Nominatim
import pycountry_convert as pc


def city_to_country(city: str) -> str | None:
    try:
        geolocator = Nominatim(user_agent="traffic-service/1.0")
        location = geolocator.geocode(city)
        if location and location.raw.get("address"):
            address = location.raw["address"]
            country_code = address.get("country_code", None)
            if country_code:
                return country_code.upper()
        return None
    except Exception as e:
        print(f"Error geocoding city {city}: {e}")
        return None


def coordinates_to_country_info(latitude: float, longitude: float) -> list[str] | None:
    try:
        geolocator = Nominatim(
            user_agent="traffic-service/1.0 (https://github.com/GeoBookr/traffic-service)"
        )
        location = geolocator.reverse(
            (latitude, longitude), language="en", timeout=10)
        if location:
            address = location.raw.get('address', {})
            country = address.get("country", "Unknown")
            country_code = address.get("country_code", "Unknown").upper()
            continent = "Unknown"
            if country_code != "Unknown":
                try:
                    continent_code = pc.country_alpha2_to_continent_code(
                        country_code)
                    continent = pc.convert_continent_code_to_continent_name(
                        continent_code)
                except Exception as conv_e:
                    print(f"Error converting country code: {conv_e}")
            city = address.get("city") or address.get(
                "town") or address.get("village") or "Unknown"
            return [country, country_code, continent, city]
        else:
            return None
    except Exception as e:
        print(f"Error in geocoding: {e}")
        return None

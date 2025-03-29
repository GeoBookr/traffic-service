import os
import json
from pathlib import Path
from dotenv import load_dotenv
import pandas as pd

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
MOCK_DATA_PATH = BASE_DIR / "data" / "mock_data.json"


class Settings:
    RABBITMQ_URL: str = os.getenv(
        "RABBITMQ_URL", "amqp://guest:guest@localhost/")
    QUEUE_NAME: str = os.getenv("QUEUE_NAME", "traffic_service_queue")
    EXCHANGE_NAME: str = os.getenv("EXCHANGE_NAME", "journey.events")
    ROUTING_KEY: str = os.getenv("ROUTING_KEY", "journey.*")
    SERVICE_NAME: str = os.getenv("SERVICE_NAME", "traffic-service")
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

    COUNTRY_LIMITS: dict = {}
    CITY_LIMITS: dict = {}
    GEO_DF: pd.DataFrame = None
    CONTINENT_MAP: dict = {}

    def __init__(self):
        self._load_limits()

    def _load_limits(self):
        try:
            with open(MOCK_DATA_PATH, "r") as f:
                data = json.load(f)

            df = pd.DataFrame(data)

            self.GEO_DF = df
            self.CONTINENT_MAP = (
                df.groupby("country_code")["continent"].first().to_dict()
            )

            country_limits = {}
            city_limits = {}

            for entry in data:
                country = entry["country_code"]
                city = entry["city"]
                limit = entry["limit"]

                if country not in country_limits:
                    country_limits[country] = limit
                else:
                    country_limits[country] = max(
                        country_limits[country], limit)

                if country not in city_limits:
                    city_limits[country] = {}
                city_limits[country][city] = limit

            self.COUNTRY_LIMITS = country_limits
            self.CITY_LIMITS = city_limits

        except Exception as e:
            print(f"[config] Failed to load mock_data.json: {e}")
            self.COUNTRY_LIMITS = {}
            self.CITY_LIMITS = {}
            self.GEO_DF = pd.DataFrame()
            self.CONTINENT_MAP = {}


settings = Settings()

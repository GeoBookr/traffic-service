import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    RABBITMQ_URL: str = os.getenv(
        "RABBITMQ_URL", "amqp://guest:guest@localhost/")
    DATABASE_URL: str = os.getenv("DATABASE_URL")
    QUEUE_NAME: str = os.getenv("QUEUE_NAME", "traffic_service_queue")
    EXCHANGE_NAME: str = os.getenv("EXCHANGE_NAME", "journey.events")
    ROUTING_KEY: str = os.getenv("ROUTING_KEY", "journey.*")
    SERVICE_NAME: str = os.getenv("SERVICE_NAME", "traffic-service")
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"


settings = Settings()

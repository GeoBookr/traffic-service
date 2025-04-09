import json
import aio_pika
import logging
from app.core.config import settings
from tenacity import retry, wait_exponential, stop_after_attempt

logger = logging.getLogger(__name__)


class EventPublisher:
    def __init__(self):
        self.url = settings.RABBITMQ_URL
        self.connection = None
        self.channel = None
        self.exchange = None
        self.exchange_name = settings.EXCHANGE_NAME

    async def connect(self):
        try:
            logger.info(
                "Attempting to connect to RabbitMQ (Traffic Service)...")
            self.connection = await aio_pika.connect_robust(self.url)
            self.channel = await self.connection.channel()
            self.exchange = await self.channel.declare_exchange(
                self.exchange_name, aio_pika.ExchangeType.TOPIC, durable=True
            )
            logger.info(
                "Traffic Service connected to RabbitMQ and declared exchange.")
        except Exception as e:
            logger.exception(
                f"Traffic Service failed to connect to RabbitMQ: {e}")
            raise

    @retry(wait=wait_exponential(multiplier=1, min=1, max=10), stop=stop_after_attempt(5))
    async def publish_event(self, message: dict, routing_key: str = "route.update"):
        if not self.exchange:
            await self.connect()
        try:
            body = json.dumps(message, default=str).encode()
            await self.exchange.publish(
                aio_pika.Message(body=body),
                routing_key=routing_key
            )
            logger.info(
                f"Traffic Service published event: {message} with key: {routing_key}")
        except Exception as e:
            logger.exception(f"Traffic Service error publishing event: {e}")
            raise

    async def close(self):
        if self.connection:
            await self.connection.close()
            logger.info("Traffic Service RabbitMQ connection closed.")


publisher = EventPublisher()

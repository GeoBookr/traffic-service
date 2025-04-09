import json
import aio_pika
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)


class EventPublisher:
    def __init__(self):
        self.connection = None
        self.channel = None
        self.exchange = None

    async def connect(self):
        try:
            self.connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
            self.channel = await self.connection.channel()
            self.exchange = await self.channel.declare_exchange(
                settings.EXCHANGE_NAME, aio_pika.ExchangeType.TOPIC, durable=True
            )
            logger.info("Connected to RabbitMQ and declared exchange.")
        except Exception as e:
            logger.exception(f"Failed to connect to RabbitMQ: {e}")
            raise

    async def publish_event(self, message: dict, routing_key: str = "route.update"):
        if not self.exchange:
            raise RuntimeError(
                "Publisher not connected. Call connect() first.")
        body = json.dumps(message).encode()
        try:
            await self.exchange.publish(aio_pika.Message(body=body), routing_key=routing_key)
            logger.info(
                f"Published event {message} with routing key {routing_key}")
        except Exception as e:
            logger.exception(f"Error publishing event: {e}")
            raise

    async def close(self):
        if self.connection:
            await self.connection.close()
            logger.info("Closed RabbitMQ connection.")


publisher = EventPublisher()

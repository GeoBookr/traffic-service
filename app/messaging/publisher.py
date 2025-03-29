import json
import aio_pika
from app.core.config import settings


class EventPublisher:
    def __init__(self):
        self.connection = None
        self.channel = None
        self.exchange = None

    async def connect(self):
        self.connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
        self.channel = await self.connection.channel()
        self.exchange = await self.channel.declare_exchange(
            settings.EXCHANGE_NAME, aio_pika.ExchangeType.TOPIC, durable=True
        )

    async def publish_event(self, message: dict, routing_key: str = "route.update"):
        if not self.exchange:
            raise RuntimeError(
                "Publisher not connected. Call connect() first.")

        body = json.dumps(message).encode()
        await self.exchange.publish(
            aio_pika.Message(body=body),
            routing_key=routing_key,
        )

    async def close(self):
        if self.connection:
            await self.connection.close()


publisher = EventPublisher()

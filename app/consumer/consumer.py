import asyncio
import json
from aio_pika import connect_robust, IncomingMessage, ExchangeType
from app.core.config import settings
from app.consumer.event_handler import handle_journey_event


async def on_message(message: IncomingMessage):
    async with message.process():  # auto-ack
        try:
            payload = json.loads(message.body.decode())
            print(f"[consumer] Received message: {payload}")
            await handle_journey_event(payload)  # make this async if needed
        except Exception as e:
            print(f"[consumer] Error handling message: {e}")


async def start_consumer():
    connection = await connect_robust(settings.RABBITMQ_URL)
    channel = await connection.channel()
    await channel.set_qos(prefetch_count=10)

    exchange = await channel.declare_exchange(
        settings.EXCHANGE_NAME,
        ExchangeType.TOPIC,
        durable=True
    )

    queue = await channel.declare_queue(
        settings.QUEUE_NAME,
        durable=True
    )
    await queue.bind(exchange, routing_key=settings.ROUTING_KEY)

    print(f"[consumer] Listening on queue: {settings.QUEUE_NAME}")
    await queue.consume(on_message)

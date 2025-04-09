import asyncio
from app.consumer.consumer import start_consumer
from app.messaging.publisher import publisher
from app.core.config import settings
from app.logging_config import configure_logging

configure_logging()


async def main():
    await publisher.connect()
    await start_consumer()
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())

import asyncio
from app.consumer.consumer import start_consumer
from app.messaging.publisher import publisher


async def main():
    await publisher.connect()
    await start_consumer()

    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())

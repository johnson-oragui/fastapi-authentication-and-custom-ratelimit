import asyncio
import aio_pika
from typing import AsyncGenerator
from contextlib import asynccontextmanager
from decouple import config

RABBITMQ_URL: str = config("RABBITMQ_URL")

@asynccontextmanager
async def get_rabbitmq() -> AsyncGenerator[aio_pika.RobustConnection, None]:
    connection = await aio_pika.connect_robust(RABBITMQ_URL)
    try:
        yield connection
    finally:
        await connection.close()


async def example():
    async with get_rabbitmq() as connection:
        async with connection.channel() as channel:
            # Declare a queue
            await channel.default_exchange.publish(
                aio_pika.Message(body='Hello World!'.encode()),
                routing_key='hello'
            )
            print(" [x] Sent 'Hello World!'")


# Run the async function
if __name__ == "__main__":
    asyncio.run(example())

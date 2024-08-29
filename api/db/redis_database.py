import asyncio
import aioredis
from typing import AsyncGenerator
from contextlib import asynccontextmanager
from decouple import config

REDIS_URL: str = config("REDIS_URL")

@asynccontextmanager
async def get_redis() -> AsyncGenerator[aioredis.Redis, None]:
    """
    Asynchronous context manager to provide a Redis connection.
    Manages setup and teardown of the Redis connection.
    """
    redis = await aioredis.from_url(
        url=REDIS_URL,
        max_connections=10,
        decode_responses=True
    )

    try:
        yield redis
    finally:
        await redis.close()

async def example_redis_operation():
    """
    Example function to demonstrate using Redis connection
    within the context manager.
    """
    async with get_redis() as redis:
        await redis.set("example_key", "example_value")
        value = await redis.get("example_key")
        print(f"Retrieved value from Redis: {value}")


asyncio.run(example_redis_operation())

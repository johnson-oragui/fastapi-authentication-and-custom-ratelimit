import redis
from contextlib import contextmanager
import redis.client

from api.utils.settings import settings


REDIS_URL: str = settings.REDIS_URL


@contextmanager
def get_redis_sync():
    conn = redis.from_url(
        url=REDIS_URL,
        connection_pool_kwargs={'minsize': 1, 'maxsize': 10},
        retry_on_error=True,
        retry_on_timeout=True,
        decode_responses=True
    )
    try:
        yield conn
    except Exception as exc:
        print(f"Redis connection error: {exc}")
        raise

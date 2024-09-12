import redis
from contextlib import contextmanager
from tenacity import retry, wait_fixed, stop_after_attempt

from api.utils.settings import settings


REDIS_URL: str = settings.REDIS_URL


@contextmanager
@retry(wait=wait_fixed(2), stop=stop_after_attempt(5))  # retry after two seconds, upto 5 attempts
def get_redis_sync():
    conn = redis.from_url(
        url=REDIS_URL,
        max_connections=10,
        decode_responses=True,
    )
    try:
        yield conn
    except redis.ConnectionError as exc:
        print(f"Redis connection error: {exc}")
        raise

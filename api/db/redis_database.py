import redis
from contextlib import contextmanager
import redis.client

from api.utils.settings import settings


REDIS_URL: str = settings.REDIS_URL


@contextmanager
def get_redis_sync():
    conn = redis.from_url(
        url=REDIS_URL
    )
    try:
        yield conn
    except Exception as exc:
        print(exc)
        raise

from fastapi import Request, HTTPException, status
from datetime import datetime, timezone, timedelta

from api.db.redis_database import get_redis_sync


def check_rate_limits_sync(request: Request):
    """checks rate limits for all routes
    """
    user_ip: str = request.client.host
    path = request.url.path
    now = datetime.now(timezone.utc) + timedelta(seconds=0)

    with get_redis_sync() as redis:
        # construct the penalty key
        penalty_key: str = f'{user_ip}:penalty_end{path}'
        # use penalty key to get time range for an ip
        penalty_end = redis.get(penalty_key)

        if penalty_end:
            penalty_end_timestamp = datetime.fromtimestamp(
                float(penalty_end),
                tz=timezone.utc
            )
            if penalty_end_timestamp > now:
                wait_time = penalty_end_timestamp - now
                wait_minutes = float(wait_time.total_seconds() / 60)
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f'Too many requests, try again in {wait_minutes:2f} minutes'
                )

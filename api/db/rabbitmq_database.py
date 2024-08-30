import asyncio
from typing import Dict, Any
from datetime import datetime, timezone, timedelta
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

RATE_LIMITS = {
    # max 5 attempts, 5 minutes penalty initially
    'login': {
        'max_attempts': 5,
        'penalty_base': 5
    },
    # 10 requests per minute
    'register': {
        'max_requests':10,
        'interval': 60
    },
    # 50 requests per minute
    'other_route': {
        'max_requests':50,
        'interval': 60
    }
}

PENALTIES: Dict[str, datetime] = {}
# Store user attempts and penalties
USER_ATTEMPTS: Dict[str, Dict[str, Any]] = {}

async def rate_limit_worker(
    channel: aio_pika.RobustConnection,
    method: aio_pika.abc.AbstractIncomingMessage,
    properties: aio_pika.abc.AbstractRobustExchange,
    body: bytes
):
    """sumary_line
    
    Keyword arguments:
    argument -- description
    Return: return_description
    """
    data: str = body.decode()
    user_ip, route = data.split(',')
    now: datetime = datetime.now(timezone.utc)

    if route in RATE_LIMITS:
        rate_limits: dict = RATE_LIMITS[route]

        if route == 'login':
            attempts: dict = USER_ATTEMPTS.get(
                user_ip,
                {
                    'count': 0,
                    'last_attempt': now
                }
            )
            attempts['count'] += 1
            attempts['last_attempt'] = now
            USER_ATTEMPTS[user_ip] = attempts

            if attempts['count'] > rate_limits['max_attempts']:
                penalty_end = PENALTIES.get(
                    user_ip,
                    now - timedelta(minutes=1)
                )
                if now < penalty_end:
                    penalty_end = rate_limits['penalty_base']


# Run the async function
if __name__ == "__main__":
    pass

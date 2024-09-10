#!/usr/bin/env python3
"""
Consumer worker module
"""
import sys
import signal
from datetime import datetime, timezone, timedelta
from redis.lock import Lock
import time
import asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.db.redis_database import get_redis_sync
from api.db.rabbitmq_database import get_rabbitmq_sync
from api.utils.settings import settings
from api.v1.models import User
from api.db.database import get_db
from api.utils.settings import settings

# RabbitMQ configuration constants
EXCHANGE_NAME = 'login_attempt_exchange'
QUEUE_NAME = 'login_attempt_queue'
ROUTING_KEY = 'login_attempt'

INITIAL_LOCKOUT_DURATION = settings.INITIAL_LOCKOUT_DURATION
MAX_PENALTY_DURATION = settings.MAX_PENALTY_DURATION
LOCKOUT_THRESHOLD = settings.LOCKOUT_THRESHOLD


def login_lockout_worker(
    ch,
    method,
    properties,
    body: bytes,
):
    """Handles callback functionality for failed login_attempts
    """
    # decode bytes to string
    user_id: str = body.decode()

    try:
        # set the running event loop
        loop = asyncio.get_event_loop()
        loop.run_until_complete(process_rate_limits(user_id))
        # acknwoledge a proccessed message
        ch.basic_ack(method.delivery_tag)
    except Exception as exc:
        print(f'error occured: {exc}, requeueing...')
        ch.basic_nack(method.delivery_tag, requeue=True)

async def process_rate_limits(user_id: str):
    """
    Async function to process login rate limit and lockout.
    It runs in an async event loop within a sync RabbitMQ worker.
    """
    async for db in get_db():
        # handles lockout mechanism
        await handle_lockout(user_id, db)

async def handle_lockout(user_id: str, db: AsyncSession):
    """handles lockout mechanism
    """
    # pass the user_id to increment login attempts
    increment_failed_attemps(user_id)
    attemtps_count = get_failed_attempts(user_id)

    if attemtps_count >= LOCKOUT_THRESHOLD:
        lockout_expires_at = (datetime.now(timezone.utc)
                               +
                               timedelta(seconds=INITIAL_LOCKOUT_DURATION))
        
        stmt = select(User).where(User.id == user_id).with_for_update()
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if user and not user.is_blocked and not user.lockout_expires_at:
            user.is_blocked = True
            user.lockout_expires_at = lockout_expires_at
            await db.commit()
            return
        elif user and user.is_blocked and user.lockout_expires_at:
            if attemtps_count % 5 == 0:
                penalty_duration = min(INITIAL_LOCKOUT_DURATION * (2 ** (attemtps_count // LOCKOUT_THRESHOLD - 1)), MAX_PENALTY_DURATION)
                await set_new_lockout(user_id, penalty_duration, db)
                reset_failed_attempts(user_id)
                return
        else:
            reset_failed_attempts(user_id)


def increment_failed_attemps(user_id: str):
    """
    Increment failed attempts count
    """
    key = f'login_attempts:{user_id}'
    lock_name = f'Lock_{user_id}'

    with get_redis_sync() as redis:
        lock = Lock(
            redis=redis,
            name=lock_name,
            timeout=5
        )
        with lock:

            failed_attempts = redis.incr(key)

            if failed_attempts == 1:
                redis.expire(key, timedelta(hours=1))


def get_failed_attempts(user_id: str):
    """
    Retrieve the count of failed attempts
    """
    key = f'login_attempts:{user_id}'
    with get_redis_sync() as redis:
        attempts = redis.get(key)
        return int(attempts) if attempts else 0

async def set_new_lockout(user_id: str, penalty_duration: int, db: AsyncSession):
    """
    Set new penalty duration for failed attempts.
    """
    now = datetime.now(timezone.utc)
    stmt = select(User).where(
        User.id == user_id
    ).with_for_update()
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if user:
        user.lockout_expires_at = now + timedelta(minutes=penalty_duration)
        user.is_blocked = True
        await db.commit()

def reset_failed_attempts(user_id: str):
    """
    Reset the failed attempts count.
    """
    key = f'login_attempts:{user_id}'
    with get_redis_sync() as redis:
        redis.delete(key)

def consume_login_attempts_queue():
    """
    Consumes The login attempts messages.
    """
    def handle_signal(sig, frame):
        print('shutting down...')
        sys.exit(0)
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    while True:
        try:
            with get_rabbitmq_sync() as connection:
                channel = connection.channel()
                channel.exchange_declare(
                    exchange=EXCHANGE_NAME,
                    exchange_type='direct',
                    durable=True
                )
                channel.queue_declare(
                    queue=QUEUE_NAME,
                    durable=True
                )

                channel.queue_bind(
                    queue=QUEUE_NAME,
                    exchange=EXCHANGE_NAME,
                    routing_key=ROUTING_KEY
                )

                channel.basic_qos(prefetch_count=1)
                channel.basic_consume(
                    queue=QUEUE_NAME,
                    on_message_callback=login_lockout_worker
                )
                print('waiting for login attempts...')
                channel.start_consuming()
        except Exception as exc:
            print(f'an error occured: {exc}, restarting consumer...')
            time.sleep(5)


# Run the async function
if __name__ == "__main__":
    consume_login_attempts_queue()

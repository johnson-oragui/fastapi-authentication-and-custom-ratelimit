import sys
import signal
from datetime import datetime, timezone, timedelta
import time
import traceback
import pika.exchange_type
from redis.lock import Lock as Lock_sync
import pika

from api.db.redis_database import get_redis_sync
from api.db.rabbitmq_database import get_rabbitmq_sync
from api.utils.settings import settings


RATE_LIMITS = {
    # max 5 attempts, 5 minutes penalty initially
    '/api/v1/auth/login': {
        'max_attempts': (settings.TEST_LOGIN_MAX_ATTEMPTS 
                         if settings.TEST 
                         else settings.LOGIN_MAX_ATTEMPTS),
        'penalty_base': 1
    },
    # 10 requests per minute
    '/api/v1/auth/register': {
        'max_attempts': (settings.TEST_REGISTER_MAX_ATTEMPTS 
                         if settings.TEST 
                         else settings.REGISTER_MAX_ATTEMPTS),
        'penalty_base': 1
    },
    # 50 requests per minute
    'other_route': {
        'max_attempts': (settings.TEST_OTHERS_MAX_ATTEMPTS 
                         if settings.TEST 
                         else settings.OTHERS_MAX_ATTEMPTS),
        'penalty_base': 1
    }
}

def sync_rate_limit_worker(
    ch: pika.BlockingConnection,
    method,
    properties: pika.BasicProperties,
    body: bytes
):
    """
    Worker function to handle rate-limiting with stricter concurrency controls
    """
    global RATE_LIMITS
    # decode bytes to string
    data: str = body.decode()
    # split the data to get user_ip and path
    user_ip, path = data.split(',')
    # set the time of the request
    now: datetime = datetime.now(timezone.utc)

    # Handle unknown paths
    rate_limits = RATE_LIMITS.get(path, RATE_LIMITS['other_route'])

    penalty_base = rate_limits.get('penalty_base')

    attempts_key = f'{user_ip}:{path}_attempts'

    penalty_key = f'{user_ip}:penalty_end{path}'

    lock_key = f'{user_ip}:{path}_lock'

    try:
        # connect to redis
        with get_redis_sync() as redis:
            # attempts: int = int(await redis.get(attempts_key) or 0)
            # attempts += 1
            lock = Lock_sync(
                redis=redis,
                name=lock_key,
                timeout=5
            )
            with lock:
                attempts = redis.incr(attempts_key)
                print('attempts: ', attempts)

                if attempts == rate_limits.get('max_attempts'):
                    penalty_end = redis.get(penalty_key)
                    # Apply penalty if max attempts are exceeded
                    if penalty_end:
                        # Convert penalty_end to datetime and check if penalty is still active
                        penalty_end_timestamp = datetime.fromtimestamp(
                            float(penalty_end),
                            tz=timezone.utc
                        )
                        # check if Penalty is still active.
                        if penalty_end_timestamp > now:
                            # Penalty is still active, no need to set a new penalty
                            pass
                        else:
                            # Penalty expired, apply new penalty
                            penalty_end = now + timedelta(minutes=penalty_base)
                            redis.set(
                                name=penalty_key,
                                value=penalty_end.timestamp()
                            )
                            redis.expire(
                                name=penalty_key,
                                time=60
                            )
                            print('Updated penalty_end:', penalty_end)

                    else:
                        penalty_end = now + timedelta(minutes=penalty_base)
                        redis.set(
                            name=penalty_key,
                            value=penalty_end.timestamp()
                        )
                        redis.expire(
                                name=penalty_key,
                                time=60
                        )
                        print('Initial penalty_end set:', penalty_end)
                else:
                    # Set attempt expiration to reset every minute
                    redis.expire(attempts_key, 60)
    except Exception as exc:
        print(f'error occured: {exc}, requeueing...')
        print(traceback.format_exc())
        ch.basic_nack(method.delivery_tag, requeue=True)
        raise
    if not ch.is_closed:
        print('ackwnowledging ...')
        ch.basic_ack(method.delivery_tag)
    else:
        print("Channel is not open, cannot ack the message.")


def consume_rate_limit_queue_sync():
    """sumary_line
    
    Keyword arguments:
    argument -- description
    Return: return_description
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
                    exchange='rate_limit_exchange',
                    exchange_type='direct',
                    durable=True
                )
                channel.queue_declare(
                    queue='rate_limit_queue',
                    durable=True
                )
                queue_name = channel.queue_bind(
                    exchange='rate_limit_exchange',
                    queue='rate_limit_queue',
                    routing_key='rate_limit'
                )
                channel.basic_qos(prefetch_count=1)
                channel.basic_consume(
                    queue='rate_limit_queue',
                    on_message_callback=sync_rate_limit_worker
                )
                print('Waiting for rate limit messages...')
                channel.start_consuming()
        except Exception as exc:
            print(f'an error occured: {exc}, restarting consumer...')
            time.sleep(5)


# Run the async function
if __name__ == "__main__":
    consume_rate_limit_queue_sync()

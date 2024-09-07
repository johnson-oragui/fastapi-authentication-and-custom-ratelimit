import pika
from contextlib import contextmanager
import pika.exceptions

from api.utils.settings import settings

RABBITMQ_URL: str = settings.RABBITMQ_URL


@contextmanager
def get_rabbitmq_sync():
    """sumary_line
    
    Keyword arguments:
    argument -- description
    Return: return_description
    """
    params = pika.ConnectionParameters('localhost')
    connection = pika.BlockingConnection(params)
    try:
        yield connection
    except pika.exceptions.AMQPConnectionError as exc:
        print(f'error setting up pika sync: {exc}')
        raise


# Run the async function
if __name__ == "__main__":
    pass

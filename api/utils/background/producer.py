from pika import DeliveryMode
import pika

from api.db.rabbitmq_database import get_rabbitmq_sync


def send_to_queue_sync(message_body: str):
    """Publishes a message to the rate_limit_exchange with a routing key.
    
    Args:
        message_body: The message to publish
    Return:
        None
    """
    with get_rabbitmq_sync() as connection:
        channel = connection.channel()
        # Declare the direct exchange
        channel.exchange_declare(
            exchange='rate_limit_exchange',
            exchange_type='direct',
            durable=True
        )
        channel.queue_declare(
            queue='rate_limit_queue',
            durable=True,
        )
        # Publish the message to the exchange with the specified routing key
        channel.basic_publish(
            exchange='rate_limit_exchange',
            routing_key='rate_limit',
            body=message_body.encode(),
            properties=pika.BasicProperties(
                delivery_mode=DeliveryMode.Persistent,  # Persistent
                content_type='text/plain'
            )
        )
    print('message_body: ', message_body)

import logging
import os
import sys
import time

from common import pollRabbitmqReadiness, initRabbitmqConnection

import pika


logging.basicConfig(stream=sys.stderr, level=logging.INFO)

# Read configuration from environment variables
RABBITMQ_HOST = os.environ.get('RABBITMQ_HOST')
RABBITMQ_USER = os.environ.get('RABBITMQ_USER')
RABBITMQ_PASS = os.environ.get('RABBITMQ_PASS')
EXCHANGE = os.environ.get('EXCHANGE')
QUEUE = os.environ.get('QUEUE')
ROUTING_KEY_READ = os.environ.get('ROUTING_KEY_READ')
ROUTING_KEY_WRITE = os.environ.get('ROUTING_KEY_WRITE')


def main():
    # wait until RabbitMQ service is ready, init connection
    pollRabbitmqReadiness(host=RABBITMQ_HOST)
    conn = initRabbitmqConnection(RABBITMQ_HOST, RABBITMQ_USER, RABBITMQ_PASS)
    
    # Setup messaging
    channel = conn.channel()
    channel.exchange_declare(exchange=EXCHANGE, exchange_type="topic")
    channel.queue_declare(queue=QUEUE, exclusive=True)
    channel.queue_bind(queue=QUEUE, exchange=EXCHANGE,routing_key=ROUTING_KEY_READ)
    channel.basic_consume(queue=QUEUE, auto_ack=True, on_message_callback=callback)
    channel.start_consuming()
    
def callback(channel: pika.channel.Channel, method: pika.spec.Basic.Deliver,
        properties: pika.spec.BasicProperties, body: bytes):
    logging.info(f"Received message from {EXCHANGE}.{ROUTING_KEY_READ}")
    bodyAsString = body.decode()
    msg = f"Got {bodyAsString}"
    channel.basic_publish(exchange=EXCHANGE, routing_key=ROUTING_KEY_WRITE, body=msg,
                                properties=pika.BasicProperties(content_type="text/plain"))
    logging.info(f"Published message to {EXCHANGE}.{ROUTING_KEY_WRITE}")
    time.sleep(1)

main()

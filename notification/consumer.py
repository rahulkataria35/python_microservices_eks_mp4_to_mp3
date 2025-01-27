import pika
import sys
import os
import time
from send import email
from dotenv import load_dotenv
from logger import get_logger
# Load environment variables from .env file
load_dotenv()

# Configure logging
logger = get_logger(__name__)


def initialize_rabbitmq_connection(host, user, password, port):
    """
    Establishes a connection to RabbitMQ and returns the channel.
    """
    credentials = pika.PlainCredentials(user, password)
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=host, port=port, credentials=credentials))
    channel = connection.channel()
    return channel



def main():
    # RabbitMQ settings
    rabbitmq_host = os.getenv("RABBITMQ_HOST", "localhost")
    rabbitmq_user = os.getenv("RABBITMQ_USER", "admin")
    rabbitmq_password = os.getenv("RABBITMQ_PASSWORD", "securepassword")
    rabbitmq_port = os.getenv("RABBITMQ_PORT", 5672)
    mp3_queue = os.getenv("MP3_QUEUE", "mp3")

    # Initialize RabbitMQ connection
    logger.info("Connecting to RabbitMQ...")
    channel = initialize_rabbitmq_connection(rabbitmq_host, rabbitmq_user, rabbitmq_password, rabbitmq_port)


    try:
        channel.queue_declare(queue=mp3_queue, durable=True)
        logger.info(f"Connected to RabbitMQ. Waiting for messages on queue: {mp3_queue}")

        def callback(ch, method, properties, body):
            try:
                logger.info(f"Received message: {body}")
                err = email.notification(body)
                if err:
                    logger.error(f"Failed to process message: {err}")
                    ch.basic_nack(delivery_tag=method.delivery_tag)
                else:
                    logger.info("Message processed successfully. Acknowledging message.")
                    ch.basic_ack(delivery_tag=method.delivery_tag)
            except Exception as e:
                logger.error(f"Error in message callback: {e}", exc_info=True)
                ch.basic_nack(delivery_tag=method.delivery_tag)

        channel.basic_consume(queue=mp3_queue, on_message_callback=callback)
        channel.start_consuming()

    except pika.exceptions.AMQPConnectionError as e:
        logger.error(f"RabbitMQ connection error: {e}")
        time.sleep(5)  # Retry delay
        main()  # Retry connection
    except KeyboardInterrupt:
        logger.info("Interrupted by user. Shutting down.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unhandled exception in consumer: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

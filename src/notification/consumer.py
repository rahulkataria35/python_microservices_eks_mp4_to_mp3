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

# RabbitMQ settings
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "admin")
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD", "securepassword")
RABBITMQ_PORT = os.getenv("RABBITMQ_PORT", 5672)
RABBITMQ_RETRY_COUNT = 5
RABBITMQ_RETRY_DELAY = 5  # seconds


# RabbitMQ connection setup with retries
def connect_rabbitmq():
    for attempt in range(1, RABBITMQ_RETRY_COUNT + 1):
        try:
            logger.info(f"Attempting to connect to RabbitMQ (Attempt {attempt}/{RABBITMQ_RETRY_COUNT})")
            credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
            connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST,port=RABBITMQ_PORT, credentials=credentials))
            channel = connection.channel()
            channel.queue_declare(queue='video', durable=True)
            channel.queue_declare(queue='mp3', durable=True)
            logger.info("RabbitMQ connection established successfully")
            return connection, channel
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            if attempt < RABBITMQ_RETRY_COUNT:
                time.sleep(RABBITMQ_RETRY_DELAY)
            else:
                raise Exception("Max retries reached. Could not connect to RabbitMQ.")


def main():
    mp3_queue = os.getenv("MP3_QUEUE", "mp3")

    # Initialize RabbitMQ connection
    logger.info("Connecting to RabbitMQ...")
    connection, channel = connect_rabbitmq()   


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

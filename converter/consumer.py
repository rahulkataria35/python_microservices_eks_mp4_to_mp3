import pika
import sys
import os
import time
from pymongo import MongoClient
import gridfs
from convert import to_mp3
from dotenv import load_dotenv
from logger import get_logger

logger = get_logger(__name__)

# Load environment variables from .env file
load_dotenv()

# RabbitMQ settings
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "admin")
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD", "securepassword")
RABBITMQ_PORT = os.getenv("RABBITMQ_PORT", 5672)
RABBITMQ_RETRY_COUNT = 5
RABBITMQ_RETRY_DELAY = 5  # seconds


def initialize_mongo_client(uri, db_name):
    """
    Initializes a MongoDB client and GridFS for a given database.
    """
    client = MongoClient(uri)
    db = client[db_name]
    fs = gridfs.GridFS(db)
    return db, fs


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
    # MongoDB settings
    mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    upload_folder = os.getenv("UPLOAD_FOLDER", "videos-db")
    download_folder = os.getenv("DOWNLOAD_FOLDER", "mp3-db")

    # Initialize MongoDB and GridFS
    db_videos, fs_videos = initialize_mongo_client(mongo_uri, upload_folder)
    db_mp3s, fs_mp3s = initialize_mongo_client(mongo_uri, download_folder)

    # Initialize RabbitMQ connection
    connection, channel = connect_rabbitmq()    

    def callback(ch, method, properties, body):
        """
        Callback function for processing RabbitMQ messages.
        """
        error = to_mp3.start(body, fs_videos, fs_mp3s, ch)
        if error:
            ch.basic_nack(delivery_tag=method.delivery_tag)
        else:
            ch.basic_ack(delivery_tag=method.delivery_tag)

    # Queue names
    video_queue = os.getenv("VIDEO_QUEUE", "video")
    channel.basic_consume(queue=video_queue, on_message_callback=callback)

    print(f"Waiting for messages on queue '{video_queue}'. To exit press CTRL+C")
    channel.start_consuming()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Interrupted")
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)

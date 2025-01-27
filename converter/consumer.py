import pika
import sys
import os
import time
from pymongo import MongoClient
import gridfs
from convert import to_mp3
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def initialize_mongo_client(uri, db_name):
    """
    Initializes a MongoDB client and GridFS for a given database.
    """
    client = MongoClient(uri)
    db = client[db_name]
    fs = gridfs.GridFS(db)
    return db, fs

def initialize_rabbitmq_connection(host, user, password, port):
    """
    Establishes a connection to RabbitMQ and returns the channel.
    """
    credentials = pika.PlainCredentials(user, password)
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=host, port=port, credentials=credentials))
    channel = connection.channel()
    return channel

def main():
    # MongoDB settings
    mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    upload_folder = os.getenv("UPLOAD_FOLDER", "videos-db")
    download_folder = os.getenv("DOWNLOAD_FOLDER", "mp3-db")

    # Initialize MongoDB and GridFS
    db_videos, fs_videos = initialize_mongo_client(mongo_uri, upload_folder)
    db_mp3s, fs_mp3s = initialize_mongo_client(mongo_uri, download_folder)

    # RabbitMQ settings
    rabbitmq_host = os.getenv("RABBITMQ_HOST", "localhost")
    rabbitmq_user = os.getenv("RABBITMQ_USER", "admin")
    rabbitmq_password = os.getenv("RABBITMQ_PASSWORD", "securepassword")
    rabbitmq_port = os.getenv("RABBITMQ_PORT", 5672)

    # Initialize RabbitMQ connection
    channel = initialize_rabbitmq_connection(rabbitmq_host, rabbitmq_user, rabbitmq_password, rabbitmq_port)

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

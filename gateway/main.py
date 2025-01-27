import json
import os
import time
import gridfs  # For handling large files in MongoDB
import pika  # For RabbitMQ communication
from flask import Flask, request, send_file, jsonify
from flask_pymongo import PyMongo  # For integrating MongoDB with Flask
from bson.objectid import ObjectId  # For working with MongoDB ObjectIDs
from auth_validate import validate
from auth_svc import access
from storage import util
from logger import get_logger

# Initialize Flask app
app = Flask(__name__)  # Flask application instance
logger = get_logger(__name__)

# MongoDB settings
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
UPLOAD_FOLDER = "videos-db"
DOWNLOAD_FOLDER = "mp3-db"

# RabbitMQ settings
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "admin")
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD", "securepassword")
RABBITMQ_PORT = os.getenv("RABBITMQ_PORT", 5672)
RABBITMQ_RETRY_COUNT = 5
RABBITMQ_RETRY_DELAY = 5  # seconds

# Initialize MongoDB connections
logger.info("Initializing MongoDB connections")
mongo_videos = PyMongo(app, uri=f"{MONGO_URI}/{UPLOAD_FOLDER}")
mongo_mp3s = PyMongo(app, uri=f"{MONGO_URI}/{DOWNLOAD_FOLDER}")

# Initialize GridFS instances
logger.info("Setting up GridFS for videos and mp3s")
fs_videos = gridfs.GridFS(mongo_videos.db)
fs_mp3s = gridfs.GridFS(mongo_mp3s.db)

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

connection, channel = connect_rabbitmq()

# Routes
@app.route('/readiness', methods=["GET"])
def readiness():
    return jsonify({"status": "ready"})

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})

@app.route("/login", methods=["POST"])
def login():
    logger.info("Processing login request")
    token, err = access.login(request)

    if err:
        logger.warning(f"Login failed: {err}")
        return err, 400
    logger.info("Login successful")
    return token, 200

@app.route("/upload", methods=["POST"])
def upload():
    logger.info("Processing upload request")
    token, err = validate.token(request)

    if err:
        logger.warning(f"Token validation failed: {err}")
        return err, 400

    data = json.loads(token)
    if data["user"].get('username') and data["user"].get("email"):
        if len(request.files) != 1:
            logger.warning("Upload failed: Exactly one file required")
            return "Exactly one file required", 400

        try:
            file = next(iter(request.files.values()))
            logger.info(f"Uploading file: {file.filename}")
            response = util.upload_file_to_storage_and_queue(file, fs_videos, channel, data["user"])
            return jsonify(response)
        except Exception as e:
            logger.exception("Error during file upload")
            return jsonify({"status": False, "error": str(e)}), 500
    else:
        logger.warning("Unauthorized upload attempt")
        return jsonify({"status": False, "error": "Unauthorized"}), 401

@app.route("/download", methods=["POST"])
def download():
    logger.info("Processing download request")
    token, err = validate.token(request)

    if err:
        logger.warning(f"Token validation failed: {err}")
        return err, 400

    data = json.loads(token)
    logger.info(f"user is {data['user']}")
    if data["user"].get("username"):
        fid = request.args.get("fid")
        if not fid:
            logger.warning("Download failed: No fid provided")
            return "No fid provided", 400

        try:
            logger.info(f"Fetching file with id: {fid}")
            file = fs_mp3s.get(ObjectId(fid))
            return send_file(file, download_name=f"{fid}_converted.mp3")
        except Exception as e:
            logger.exception(f"Error during file download for id {fid}")
            return str(e), 400
    else:
        logger.warning("Unauthorized download attempt")
        return "You are not allowed to download", 401

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8086)
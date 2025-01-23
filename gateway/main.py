import json  
import os
import gridfs  # For handling large files in MongoDB
import pika  # For RabbitMQ communication
from flask import Flask, request, send_file
from flask_pymongo import PyMongo  # For integrating MongoDB with Flask
from bson.objectid import ObjectId  # For working with MongoDB ObjectIDs
from auth_validate import validate
from auth_svc import access
from storage import util
from logger import get_logger


# Initialize Flask app
app = Flask(__name__)  # Flask application instance
# Get logger instance
logger = get_logger(__name__)

###############################  MongoDB ####################################
# MONGO_URI = "mongodb://host.minikube.internal:27017"  # MongoDB connection URI
MONGO_URI = "mongodb://localhost:27017"
UPLOAD_FOLDER = "videos"
DOWNLOAD_FOLDER = "mp3s"

# Initialize MongoDB connections
logger.info("Initializing MongoDB connections")
mongo_videos = PyMongo(app, uri=f"{MONGO_URI}/{UPLOAD_FOLDER}")
mongo_mp3s = PyMongo(app, uri=f"{MONGO_URI}/{DOWNLOAD_FOLDER}")

# Initialize GridFS instances
logger.info("Setting up GridFS for videos and mp3s")
fs_videos = gridfs.GridFS(mongo_videos.db)
fs_mp3s = gridfs.GridFS(mongo_mp3s.db)

######################## Initialize RabbitMQ ##############################
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "admin")
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD", "securepassword")

try:
    logger.info("Connecting to RabbitMQ")
    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST, credentials=credentials))
    channel = connection.channel()
    channel.queue_declare(queue='video', durable=True)
    channel.queue_declare(queue='mp3', durable=True)
    logger.info("RabbitMQ connection established successfully")
except Exception as e:
    logger.error(f"Failed to connect to RabbitMQ: {str(e)}")
    raise

# Routes
@app.route("/login", methods=["POST"])
def login():
    """
    Login route to authenticate a user.
    """
    logger.info("Processing login request")
    token, err = access.login(request)

    if err:
        logger.warning(f"Login failed: {err}")
        return err, 400
    logger.info("Login successful")
    return token, 200

@app.route("/upload", methods=["POST"])
def upload():
    """
    Route to upload a video file.
    """
    logger.info("Processing upload request")
    token, err = validate.token(request)

    if err:
        logger.warning(f"Token validation failed: {err}")
        return err, 400

    access = json.loads(token)
    logger.info(f"access is {access}")
    if access.get('username') == "rahul":
        if len(request.files) != 1:
            logger.warning("Upload failed: Exactly one file required")
            return "Exactly one file required", 400

        try:
            file = next(iter(request.files.values()))
            logger.info(f"Uploading file: {file.filename}")
            status, err = util.upload(file, fs_videos, channel, access)
            if err:
                logger.exception(f"File upload failed: {err}")
                return err, 400
            logger.info(f"File uploaded successfully: {file.filename}")
            # return response in json
            return {"status": "success"}, 200

        except Exception as e:
            logger.exception("Error during file upload")
            return str(e), 400
    else:
        logger.warning("Unauthorized upload attempt")
        return "You are not allowed to upload", 401

@app.route("/download", methods=["POST"])
def download():
    """
    Route to download a converted MP3 file.
    """
    logger.info("Processing download request")
    token, err = validate.token(request)

    if err:
        logger.warning(f"Token validation failed: {err}")
        return err, 400

    access = json.loads(token)
    if access.get('admin'):
        fid = request.args.get("fid")
        if not fid:
            logger.warning("Download failed: No fid provided")
            return "No fid provided", 400

        try:
            logger.info(f"Fetching file with id: {fid}")
            file = fs_mp3s.get(ObjectId(fid))
            logger.info(f"File fetched successfully: {fid}")
            return send_file(file, download_name=f"{fid}_converted.mp3")
        except Exception as e:
            logger.exception(f"Error during file download for id {fid}")
            return str(e), 400
    else:
        logger.warning("Unauthorized download attempt")
        return "You are not allowed to download", 401

if __name__ == "__main__":
    logger.info("Starting the Flask application")
    app.run(host="0.0.0.0", port=8086)

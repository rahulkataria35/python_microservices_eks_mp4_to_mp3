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
UPLOAD_FOLDER = "videos"  # MongoDB database name for uploaded videos
DOWNLOAD_FOLDER = "mp3s"  # MongoDB database name for converted files

# Initialize MongoDB connections
mongo_videos = PyMongo(app, uri=f"{MONGO_URI}/{UPLOAD_FOLDER}")  # Connect to 'videos' database
mongo_mp3s = PyMongo(app, uri=f"{MONGO_URI}/{DOWNLOAD_FOLDER}")  # Connect to 'mp3s' database

# Initialize GridFS instances
fs_videos = gridfs.GridFS(mongo_videos.db)  # For storing and retrieving video files
fs_mp3s = gridfs.GridFS(mongo_mp3s.db)  # For storing and retrieving converted MP3 files

######################## Initialize RabbitMQ connection and channel ##########################
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "admin")
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD", "securepassword")
# Setting up authentication
credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST, credentials=credentials))
channel = connection.channel() # Create a channel
channel.queue_declare(queue='video', durable=True)
channel.queue_declare(queue='mp3', durable=True)

# Routes
@app.route("/login", methods=["POST"])
def login():
    """
    Login route to authenticate a user.
    """
    token, err = access.login(request)  # Authenticate user using a custom module

    if err:
        return err, 400  # Return error if login fails
    return token, 200  # Return authentication token if login succeeds

@app.route("/upload", methods=["POST"])
def upload():
    """
    Route to upload a video file.
    """
    token, err = validate.token(request)  # Validate the provided token

    if err:
        return err, 400  # Return error if token is invalid

    access = json.loads(token)  # Parse the token for access rights

    if access.get('admin'):  # Check if the user has admin access
        if len(request.files) != 1:  # Ensure exactly one file is uploaded
            return "Exactly one file required", 400

        try:
            file = next(iter(request.files.values()))  # Get the uploaded file
            err = util.upload(file, fs_videos, channel, access)  # Process the file upload
            if err:
                return err, 400  # Return error if upload fails
            return "Success", 200  # Return success message
        except Exception as e:
            return str(e), 400  # Handle and return exceptions
    else:
        return "You are not allowed to upload", 401  # Unauthorized access

@app.route("/download", methods=["POST"])
def download():
    """
    Route to download a converted MP3 file.
    """
    token, err = validate.token(request)  # Validate the provided token

    if err:
        return err, 400  # Return error if token is invalid

    access = json.loads(token)  # Parse the token for access rights

    if access.get('admin'):  # Check if the user has admin access
        fid = request.args.get("fid")  # Retrieve the file ID from the request

        if not fid:  # Ensure file ID is provided
            return "No fid provided", 400

        try:
            file = fs_mp3s.get(ObjectId(fid))  # Retrieve the file using its ID
            return send_file(file, download_name=f"{fid}_converted.mp3")  # Send the file for download
        except Exception as e:
            return str(e), 400  # Handle and return exceptions
    else:
        return "You are not allowed to download", 401  # Unauthorized access

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8086)  # Run the Flask app on port 8080

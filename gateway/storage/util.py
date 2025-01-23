import pika  # For RabbitMQ communication
import json  # For working with JSON data
from ..logger import get_logger  # Custom logger for logging messages and errors

# Get logger instance
logger = get_logger(__name__)  # Initialize logger for the current module

def upload(f, fs, channel, access):
    """
    Uploads a video file to a storage system and sends a message to a RabbitMQ queue.

    Parameters:
    f (file): The video file to be uploaded.
    fs (object): An object representing the storage system. It should have a method `put` to upload the file.
    channel (pika.channel): A RabbitMQ channel object to publish the message.
    access (dict): A dictionary containing the user's access information. It should have a key 'username'.

    Returns:
    tuple: A tuple containing a status message and HTTP status code:
        - ("Success", 200): If the upload and message publishing are successful.
        - ("Internal Server error", 500): If an error occurs during the upload or message publishing.
    """
    try:
        # Upload the video file to the storage system and get its unique file ID (fid)
        fid = fs.put(f)
    except Exception as err:
        # Log and handle errors during file upload
        logger.error(f"File upload failed: {err}")
        return "Internal Server error", 500

    # Prepare the message to be sent to the RabbitMQ queue
    message = {
        "video_fid": str(fid),  # File ID of the uploaded video
        "mp3_fid": None,  # Placeholder for the converted MP3 file ID
        "username": access["username"],  # Username from the access dictionary
    }

    try:
        # Publish the message to the RabbitMQ queue named 'video'
        channel.basic_publish(
            exchange='',  # Default exchange
            routing_key='video',  # Queue name
            body=json.dumps(message),  # Message payload in JSON format
            properties=pika.BasicProperties(
                delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE  # Ensure message persistence
            )
        )
    except Exception as err:
        # Log and handle errors during message publishing
        logger.error(f"Message publishing failed: {err}")
        
        # Delete the uploaded file to maintain consistency if publishing fails
        fs.delete(fid)
        return "Internal Server error", 500

    # Return success response if upload and message publishing succeed
    return "Success", 200

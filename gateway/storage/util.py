import pika  # For RabbitMQ communication
import json
from logger import get_logger

# Initialize logger for the current module
logger = get_logger(__name__)

def upload_file_to_storage_and_queue(file_obj, storage_system, rabbitmq_channel, user_access):
    """
    Uploads a video file to a storage system and publishes a message to a RabbitMQ queue.

    Parameters:
    file_obj (file): The video file to be uploaded.
    storage_system (object): The storage system instance. It should provide methods `put` to upload and `delete` to remove a file.
    rabbitmq_channel (pika.channel): A RabbitMQ channel instance to publish messages.
    user_access (dict): Dictionary containing user access information. Must include 'username' and 'email' keys.

    Returns:
    dict: A dictionary containing the result status, message, and optional details.
    """
    try:
        # Upload the file to the storage system
        file_id = storage_system.put(file_obj)
        logger.info(f"File uploaded successfully with ID: {file_id}")
    except Exception as upload_error:
        # Log upload failure and return an error response
        logger.exception(f"File upload failed: {upload_error}")
        return {
            "status": False,
            "error": "File upload failed",
            "details": str(upload_error)
        }

    # Prepare the message for the RabbitMQ queue
    message_payload = {
        "video_file_id": str(file_id),
        "audio_file_id": None,  # Placeholder for audio file ID after conversion
        "username": user_access.get("username"),
        "email": user_access.get("email")
    }

    try:
        # Publish the message to the RabbitMQ 'video' queue
        rabbitmq_channel.basic_publish(
            exchange='',  # Default exchange
            routing_key='video',  # Target queue name
            body=json.dumps(message_payload),  # Serialize message as JSON
            properties=pika.BasicProperties(
                delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE  # Ensure message persistence
            )
        )
        logger.info(f"Message published to RabbitMQ queue 'video': {message_payload}")
    except Exception as publish_error:
        # Log publishing failure, clean up the uploaded file, and return an error response
        logger.exception(f"Failed to publish message to RabbitMQ: {publish_error}")
        try:
            storage_system.delete(file_id)
            logger.info(f"Rolled back uploaded file with ID: {file_id} due to publishing failure.")
        except Exception as rollback_error:
            logger.exception(f"Failed to delete file during rollback: {rollback_error}")
            return {
                "status": False,
                "error": "Failed to publish message and rollback file",
                "details": {
                    "publish_error": str(publish_error),
                    "rollback_error": str(rollback_error)
                }
            }
        return {
            "status": False,
            "error": "Failed to publish message to RabbitMQ",
            "details": str(publish_error)
        }

    # Return success response if all operations succeed
    return {
        "status": True,
        "message": "File uploaded and message published successfully",
        "details": {
            "file_id": str(file_id),
            "queue": "video"
        }
    }

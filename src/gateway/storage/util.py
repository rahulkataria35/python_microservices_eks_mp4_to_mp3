import pika  # For RabbitMQ communication
import json
import time
from logger import get_logger

logger = get_logger(__name__)

def upload_file_to_storage_and_queue(file_obj, storage_system, rabbitmq_channel, user_access):
    try:
        file_id = storage_system.put(file_obj)
        logger.info(f"File uploaded successfully with ID: {file_id}")
    except Exception as upload_error:
        logger.exception(f"File upload failed: {upload_error}")
        return {
            "status": False,
            "message": "File upload failed",
            "details": str(upload_error)
        }

    message_payload = {
        "video_file_id": str(file_id),
        "audio_file_id": None,
        "username": user_access.get("username"),
        "email": user_access.get("email")
    }

    try:
        rabbitmq_channel.basic_publish(
            exchange='',
            routing_key='video',
            body=json.dumps(message_payload),
            properties=pika.BasicProperties(delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE)
        )
        logger.info(f"Message published to RabbitMQ queue 'video': {message_payload}")
    except Exception as publish_error:
        logger.exception(f"Failed to publish message to RabbitMQ: {publish_error}")
        try:
            storage_system.delete(file_id)
            logger.info(f"Rolled back uploaded file with ID: {file_id} due to publishing failure.")
        except Exception as rollback_error:
            logger.exception(f"Failed to delete file during rollback: {rollback_error}")
            return {
                "status": False,
                "message": "Failed to publish message and rollback file",
                "details": {
                    "publish_error": str(publish_error),
                    "rollback_error": str(rollback_error)
                }
            }
        return {
            "status": False,
            "message": "Failed to publish message to RabbitMQ",
            "details": str(publish_error)
        }

    return {
        "status": True,
        "message": "File uploaded and message published successfully",
        "details": {
            "file_id": str(file_id),
            "queue": "video"
        }
    }
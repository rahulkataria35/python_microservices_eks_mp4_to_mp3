import json
import tempfile
import os
import pika
from bson.objectid import ObjectId
import moviepy.editor
from logger import get_logger

# Initialize logger for the current module
logger = get_logger(__name__)

def start(message, fs_videos, fs_mp3s, channel):
    """
    Converts a video file to MP3 format, stores the audio in MongoDB, and publishes a message to RabbitMQ.

    Parameters:
    - message (bytes): JSON-encoded message from RabbitMQ.
    - fs_videos (gridfs.GridFS): GridFS instance for accessing video files.
    - fs_mp3s (gridfs.GridFS): GridFS instance for storing MP3 files.
    - channel (pika.channel.Channel): RabbitMQ channel for publishing messages.

    Returns:
    - dict: Response containing status, message, and details.
    """
    temp_video_path = None
    temp_audio_path = None
    mp3_fid = None

    try:
        # Parse the message
        message = json.loads(message)
        logger.info(f"Received and parsed message: {message}")

        video_fid = message.get("video_file_id")
        if not video_fid:
            error_msg = "Missing 'video_file_id' in the message."
            logger.error(error_msg)
            return {"status": False, "message": error_msg}

        # Fetch video file and save it to a temporary file
        with tempfile.NamedTemporaryFile(delete=False) as temp_video:
            video_file = fs_videos.get(ObjectId(video_fid))
            temp_video.write(video_file.read())
            temp_video_path = temp_video.name
            logger.info(f"Video file saved temporarily at: {temp_video_path}")

        # Convert video to audio (MP3 format)
        temp_audio_path = os.path.join(tempfile.gettempdir(), f"{video_fid}.mp3")
        logger.info(f"Starting video-to-audio conversion for video ID: {video_fid}")
        video_clip = moviepy.editor.VideoFileClip(temp_video_path)
        video_clip.audio.write_audiofile(temp_audio_path, logger=None)
        video_clip.close()
        logger.info(f"Audio conversion successful. Temporary MP3 path: {temp_audio_path}")

        # Store the MP3 file in GridFS
        with open(temp_audio_path, "rb") as audio_file:
            mp3_fid = fs_mp3s.put(audio_file.read())
        logger.info(f"MP3 file stored in MongoDB with ID: {mp3_fid}")

        # Add MP3 file ID to the message
        message["audio_file_id"] = str(mp3_fid)

        # Publish the updated message to RabbitMQ
        channel.basic_publish(
            exchange="",
            routing_key=os.environ.get("MP3_QUEUE", "mp3"),
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE
            ),
        )
        logger.info("Message successfully published to RabbitMQ.")

        # return {"status": True, "message": "Video processed successfully", "details": message}

    except Exception as err:
        logger.error(f"Error occurred: {str(err)}", exc_info=True)

        # Rollback MP3 file if already stored
        if mp3_fid:
            fs_mp3s.delete(mp3_fid)
            logger.warning(f"Rolled back MP3 file with ID: {mp3_fid}")

        return {"status": False, "message": str(err)}

    finally:
        # Cleanup temporary files
        if temp_video_path and os.path.exists(temp_video_path):
            os.remove(temp_video_path)
            logger.info(f"Cleaned up temporary video file: {temp_video_path}")
        if temp_audio_path and os.path.exists(temp_audio_path):
            os.remove(temp_audio_path)
            logger.info(f"Cleaned up temporary audio file: {temp_audio_path}")

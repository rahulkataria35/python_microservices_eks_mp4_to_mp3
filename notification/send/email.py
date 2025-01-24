import smtplib
import os
import json
from email.message import EmailMessage
from dotenv import load_dotenv
from logger import get_logger

# Load environment variables from .env file
load_dotenv()

# Configure logging
logger = get_logger(__name__)

def notification(message):
    try:
        message = json.loads(message)
        mp3_fid = message["audio_file_id"]  # Fixed key
        username = message["username"]
        email_address = message["email"]

        sender_address = os.getenv("GMAIL_ADDRESS")
        sender_password = os.getenv("GMAIL_PASSWORD")

        if not sender_address or not sender_password:
            logger.error("GMAIL_ADDRESS or GMAIL_PASSWORD not set in .env file.")
            return "Email credentials not configured."

        msg = EmailMessage()
        msg.set_content(f"MP3 file with ID:  {mp3_fid}")
        msg["Subject"] = "MP3 File Ready for Download"
        msg["From"] = sender_address
        msg["To"] = email_address

        logger.info(f"Preparing to send email to {email_address}...")
        with smtplib.SMTP("smtp.gmail.com", 587) as session:
            session.starttls()
            session.login(sender_address, sender_password)
            session.send_message(msg)
            logger.info("Email sent successfully.")
        return None  # Indicate success

    except json.JSONDecodeError:
        logger.error(f"Failed to decode message as JSON: {message}")
        return "Invalid message format."
    except smtplib.SMTPException as e:
        logger.error(f"SMTP error occurred: {e}", exc_info=True)
        return str(e)
    except Exception as e:
        logger.error(f"Unhandled exception in email notification: {e}", exc_info=True)
        return str(e)

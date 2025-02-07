import os
import time
import psycopg2
from psycopg2 import sql, OperationalError
from logger import get_logger
from contextlib import closing

# Get logger instance
logger = get_logger(__name__)

MAX_RETRIES = 5  # Maximum number of retries
INITIAL_DELAY = 2  # Initial delay in seconds

def get_db_connection():
    retries = 0
    delay = INITIAL_DELAY

    while retries < MAX_RETRIES:
        try:
            connection = psycopg2.connect(
                host=os.environ.get("POSTGRES_HOST", "localhost"),
                user=os.environ.get("POSTGRES_USER", "postgres"),
                password=os.environ.get("POSTGRES_PASSWORD", "password"),
                dbname=os.environ.get("POSTGRES_DB", "auth_db"),
                port=int(os.environ.get("POSTGRES_PORT", 5432))
            )
            logger.info("Database connection established.")
            return connection
        except OperationalError as e:
            logger.error(f"Database connection failed (attempt {retries + 1}): {e}")
            retries += 1
            if retries < MAX_RETRIES:
                logger.info(f"Retrying in {delay} seconds...")
                time.sleep(delay)
                delay *= 2  # Exponential backoff
            else:
                logger.exception("Max retries reached. Could not connect to the database.")
                raise

def check_database_connection():
    try:
        connection = get_db_connection()
        if connection is None:
            logger.error("Failed to obtain database connection.")
            return False
        
        with closing(connection.cursor()) as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        
        connection.close()
        logger.info("Database connection verified successfully.")
        return True
    except (OperationalError, InterfaceError) as e:
        logger.error(f"Database connection failed: {e}", exc_info=True)
        return False
    

def create_db_and_tables():
    """
    Create the database and tables if they don't exist.
    """
    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        # Create the 'users' table if it doesn't exist
        create_table_query = """
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(120) UNIQUE NOT NULL,
            password VARCHAR(120) NOT NULL,
            email VARCHAR(120) UNIQUE NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
        cursor.execute(create_table_query)
        connection.commit()

        cursor.close()
        connection.close()
        logger.info("Database and tables created successfully.")
    except OperationalError as e:
        logger.exception(f"Error connecting to the database: {e}")
    except Exception as e:
        logger.exception(f"Error creating database and tables: {e}")

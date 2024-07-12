from mysql.connector import Error
import os
import mysql.connector

def get_db_connection():
    return mysql.connector.connect(
        host=os.environ.get("MYSQL_HOST"),
        user=os.environ.get("MYSQL_USER"),
        password=os.environ.get("MYSQL_PASSWORD"),
        database=os.environ.get("MYSQL_DB"),
        port=int(os.environ.get("MYSQL_PORT"))
    )

def check_database_connection():
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone() # Fetch the result to clear the buffer
        cursor.close()
        connection.close()
        return True
    except Error as e:
        print(f"Database connection failed: {e}")
        return False


# Function to create the database and tables
def create_db_and_tables():
    try:
        connection = get_db_connection()
        print("Creating database...", connection)
        cursor = connection.cursor()
        # cursor.execute("CREATE DATABASE IF NOT EXISTS auth")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(120) UNIQUE NOT NULL,
                password VARCHAR(120) NOT NULL
            )
        """)
        connection.commit()
        cursor.close()
        connection.close()
        print("Database and tables created successfully!")
    except Error as e:
        print(f"Error creating database and tables: {e}")
import os
import jwt
from flask import Flask, request, jsonify
import utils
from db import create_db_and_tables, check_database_connection, get_db_connection
from utils import createJWT
from logger import get_logger

# Initialize Flask app
app = Flask(__name__)

# Get logger instance
logger = get_logger(__name__)

JWT_SECRET = os.environ.get("JWT_SECRET", "mysecret")

# Check readiness
@app.route('/readiness', methods=["GET"])
def readiness():
    if check_database_connection():
        logger.info("Database Connection is OK...")
        return jsonify(status="yes"), 200
    else:
        logger.error("Database connection failed.")
        return jsonify(status="error", message="Database connection failed"), 503


# Check health
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


# Create user
@app.route("/create", methods=["POST"])
def create_user():
    auth = request.get_json()
    logger.info(f"Received auth: {auth}")
    if not auth or not auth["username"] or not auth["password"] or not auth["email"]:
        return jsonify({"msg": "missing credentials",
                        "required_fields": {"username": "", "password": "", "email": ""}
                        }), 401

    hashed_password = utils.hash_password(auth["password"])
    logger.info(f"Hashed password: {hashed_password}")
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        # check for username is exists or not
        cursor.execute("SELECT username FROM users WHERE username = %s", (auth["username"],))
        existing_user = cursor.fetchone()

        if existing_user:
            logger.warning(f"User with username {auth['username']} already exists")
            return jsonify({"msg": "User already exists"}), 406
        
        # now check email is exist or not
        cursor.execute("SELECT email FROM users WHERE email = %s", (auth["email"],))
        existing_email = cursor.fetchone()
        if existing_email:
            logger.warning(f"Email {auth['email']} already exists")
            return jsonify({"msg": "Email already exists"}), 406

        logger.info("Creating user...")
        cursor.execute("INSERT INTO users (username, password, email) VALUES (%s, %s, %s)", (auth["username"], hashed_password, auth["email"]))
        connection.commit()
        logger.info(f"User {auth['username']} created successfully")
        return jsonify({"msg": "User created successfully"}), 201
    
    except Exception as e:
        connection.rollback()
        logger.exception(f"Error creating user: {e}")
        return jsonify({"msg": "Internal Server Error"}), 500
    
    finally:
        cursor.close()
        connection.close()


# Login
@app.route("/login", methods=["POST"])
def login():
    auth = request.get_json()
    if not auth or not auth["username"] or not auth["password"]:
        logger.error("Missing credentials")
        return jsonify({"msg": "missing credentials"}), 401

    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT username, password, email FROM users WHERE username = %s", (auth["username"],))
    user = cursor.fetchone()

    cursor.close()
    connection.close()

    if user:
        logger.info(f"User {auth['username']} found")
        username, password, email = user
        
        if auth["username"] != username or not utils.verify_password(auth["password"], password):
            logger.error(f"Invalid credentials for user {auth['username']}")
            return jsonify({"msg": "bad username or password"}), 401
        logger.info(f"User {auth['username']} logged in successfully")
        data = {"username": username, "email": email}
        return jsonify({"token": createJWT(data, JWT_SECRET, True)})
    else:
        logger.error(f"User {auth['username']} not found")
        return jsonify({"msg": "Invalid Credentials"}), 401


# Validate JWT
@app.route("/validate", methods=["POST"])
def validate():
    encoded_jwt = request.headers.get("Authorization")
    
    if not encoded_jwt:
        logger.error("Missing token")
        return jsonify({"msg": "missing token"}), 401

    encoded_jwt = encoded_jwt.split(" ")[1]

    try:
        logger.info(f"Validating token: {encoded_jwt}")
        decoded = jwt.decode(encoded_jwt, JWT_SECRET, algorithms=["HS256"])
        logger.info("Token is valid")
    except jwt.ExpiredSignatureError:
        logger.error("Token expired")
        return jsonify({"msg": "Token has expired"}), 403
    except jwt.InvalidTokenError:
        logger.error("Invalid token")
        return jsonify({"msg": "Invalid token"}), 403

    return jsonify(decoded), 200


if __name__ == "__main__":
    create_db_and_tables()
    app.run(host="0.0.0.0", port=5000)

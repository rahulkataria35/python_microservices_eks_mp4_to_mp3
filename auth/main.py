import os
import jwt
from flask import Flask, request, jsonify
from mysql.connector import Error
import utils
from db import create_db_and_tables, check_database_connection, get_db_connection
from utils import createJWT

app = Flask(__name__)

JWT_SECRET = os.environ.get("JWT_SECRET", "mysecret")

@app.route('/readiness', methods=["GET", "POST"])
def readiness():
    if check_database_connection():
        return jsonify(status="yes"), 200
    else:
        return jsonify(status="error", message="Database connection failed"), 503

@app.route("/health", methods=["GET", "POST"])
def health():
    return jsonify({"status": "ok"})

@app.route("/create", methods=["POST"])
def create_user():
    auth = request.authorization
    print("--------------------------------",auth.password)
    if not auth or not auth.username or not auth.password:
        return jsonify({"msg": "missing credentials"}), 401
    
    hashed_password = utils.hash_password(str(auth.password))
    print("Hashed password----------------",hashed_password)
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("SELECT username FROM user WHERE username = %s", (auth.username,))
        existing_user = cursor.fetchone()

        if existing_user:
            cursor.close()
            connection.close()
            return jsonify({"msg": "User already exists"}), 406

        cursor.execute("INSERT INTO user (username, password) VALUES (%s, %s)", (auth.username, hashed_password))
        connection.commit()
        cursor.close()
        connection.close()
        return jsonify({"msg": "User created successfully"}), 201
    except Error as e:
        connection.rollback()
        cursor.close()
        connection.close()
        app.logger.error(f"Failed to create user: {e}")
        return jsonify({"msg": "Internal Server Error"}), 500

@app.route("/login", methods=["POST"])
def login():
    auth = request.authorization
    if not auth or not auth.username or not auth.password:
        return jsonify({"msg": "missing credentials"}), 401
    
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT username, password FROM user WHERE username = %s", (auth.username,))
    user = cursor.fetchone()
    cursor.close()
    connection.close()

    if user:
        username, password = user
        if auth.username != username or not utils.verify_password(auth.password, password):
            return jsonify({"msg": "bad username or password"}), 401
        else:
            return jsonify({"token": createJWT(auth.username, JWT_SECRET, True)})
    else:
        return jsonify("Invalid Credentials"), 401

@app.route("/validate", methods=["POST"])
def validate():
    encoded_jwt = request.headers.get("Authorization")
    if not encoded_jwt:
        return jsonify({"msg": "missing token"}), 401
    
    encoded_jwt = encoded_jwt.split(" ")[1]

    try:
        decoded = jwt.decode(
            encoded_jwt, JWT_SECRET, algorithms=["HS256"]
        )
    except jwt.ExpiredSignatureError:
        return jsonify("Token has expired"), 403
    except jwt.InvalidTokenError:
        return jsonify("Invalid token"), 403
    
    return decoded, 200 

if __name__ == "__main__":
    create_db_and_tables()
    app.run(host="0.0.0.0", port=5000, debug=True)

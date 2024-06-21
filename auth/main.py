import jwt
import datetime
import os
from flask import Flask, request, jsonify
from flask_mysqldb import MySQL


app = Flask(__name__)
mysql = MySQL(app)

# config
app.config['MYSQL_HOST'] = os.environ.get("MYSQL_HOST")
app.config['MYSQL_USER'] = os.environ.get("MYSQL_USER")
app.config['MYSQL_PASSWORD'] = os.environ.get("MYSQL_PASSWORD")
app.config['MYSQL_DB'] = os.environ.get("MYSQL_DB")
app.config['MYSQL_PORT'] = int(os.environ.get("MYSQL_PORT"))


@app.route("/login", methods=["POST"])
def login():
    auth = request.authorization
    if not auth or not auth.username or not auth.password:
        return jsonify({"msg": "missing credentials"}), 401
    
    # check database for username and password
    cur = mysql.connection.cursor()
    res = cur.execute(
        f"SELECT email, password FROM user WHERE email={(auth.username,)}"
    )
    if res > 0:
        user = cur.fetchone()
        email = user[0]
        password = user[1]

        if auth.username != email or auth.password != password:
            return jsonify({"msg": "bad username or password"}), 401
        else:
            return createJWT(auth.username, os.environ.get("JWT_SECRET"), True)
    else:
        return jsonify("Invalid Credentials"), 401

@app.route("/validate", methods=["POST"])
def validate():
    encoded_jwt = request.headers["Authorization"]
    if not encoded_jwt:
        return jsonify({"msg": "missing token"}), 401
    
    encoded_jwt = encoded_jwt.split(" ")[1]

    try:
        decoded = jwt.decode(
            encoded_jwt, os.environ.get("JWT_SECRET"), algorithms=["HS256"]
        )
    except:
        return jsonify("Not Authorized"), 403
    
    return decoded, 200 


def createJWT(username, secret, authz):
    return jwt.encode(
        {
            "username": username,
            "exp": datetime.datetime.now(tz=datetime.timezone.utc) + datetime.timedelta(days=1),
            "iat": datetime.datetime.now(tz=datetime.timezone.utc),
            "authz": authz
        },
        secret,
        algorithm="HS256"
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)


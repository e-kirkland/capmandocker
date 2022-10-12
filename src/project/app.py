import os, sys

# Appending directory to path for local imports
append_path = os.path.join(os.getcwd(), "project")
print("APPENDING PATH: ", append_path)
sys.path.append(append_path)

from werkzeug.utils import secure_filename
from flask import Flask, jsonify, send_from_directory, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

from models.base import db
from models.Settings import Settings
from models.Players import Players
from models.Rosters import Rosters

from config import Config

app = Flask(__name__)

# Establish config variables
config = Config()
app.config.from_object(config)

# Initialize database
print("DB_URI: ", app.config["SQLALCHEMY_DATABASE_URI"])
db.init_app(app)

# Check slack credentials
bot_token = app.config["BOT_TOKEN"]
user_token = app.config["USER_TOKEN"]
secret = app.config["SECRET"]
alert_channel = app.config["ALERT_CHANNEL"]
print("TOKENS: ", bot_token, user_token, secret, alert_channel)


@app.route("/")
def hello_world():
    return jsonify(hello="world")


@app.route("/initialize/", methods=["GET"])
def init_db():
    db.drop_all()
    db.create_all()
    db.session.commit()
    return jsonify(msg="Successfully initialized database")


@app.route("/static/<path:filename>")
def staticfiles(filename):
    return send_from_directory(app.config["STATIC_FOLDER"], filename)


@app.route("/media/<path:filename>")
def mediafiles(filename):
    return send_from_directory(app.config["MEDIA_FOLDER"], filename)


@app.route("/upload", methods=["GET", "POST"])
def upload_file():
    if request.method == "POST":
        file = request.files["file"]
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config["MEDIA_FOLDER"], filename))

    return """
    <!doctype html>
    <title>upload new File</title>
    <form action="" method=post enctype=multipart/form-data>
        <p><input type=file name=file><input type=submit value=Upload>
    </form>
    """


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)

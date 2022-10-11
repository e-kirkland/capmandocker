import os

from werkzeug.utils import secure_filename
from flask import Flask, jsonify, send_from_directory, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import slack
from slackeventsapi import SlackEventAdapter

from project.config import Config
from project.models.base import db
from project.models.Settings import Settings
from project.models.Players import Players
from project.models.Rosters import Rosters

# Instantiate app
app = Flask(__name__)
config_obj = Config()
app.config.from_object(config_obj)
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_STRING")
print("DATABASE URL: ", app.config["SQLALCHEMY_DATABASE_URI"])
db.init_app(app)
# Enable CORS
cors = CORS(app)

# Getting tokens from env
bot_token = app.config["SLACK_BOT_TOKEN"]
user_token = app.config["SLACK_USER_TOKEN"]
secret = app.config["SLACK_SECRET"]
alert_channel = app.config["ALERT_CHANNEL"]

print("TOKENS: ", bot_token, user_token, secret)

# Instantiating slackbot
slack_event_adapter = SlackEventAdapter(secret, "/slack/events", app)
client = slack.WebClient(token=bot_token)
BOT_ID = client.api_call("auth.test")["user_id"]


@app.route("/")
def hello_world():
    return jsonify(hello="world")


# Route for returning static file from directory
@app.route("/static/<path:filename>")
def staticfiles(filename):
    return send_from_directory(app.config["STATIC_FOLDER"], filename)


# Route for downloading media file from directory
@app.route("/media/<path:filename>")
def mediafiles(filename):
    return send_from_directory(app.config["MEDIA_FOLDER"], filename)


# Route for uploading media file to directory
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

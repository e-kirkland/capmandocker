import os, sys

# Appending directory to path for local imports
append_path = os.path.join(os.getcwd(), "project")
print("APPENDING PATH: ", append_path)
sys.path.append(append_path)

from werkzeug.utils import secure_filename
from flask import Flask, jsonify, send_from_directory, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from slackeventsapi import SlackEventAdapter

from models.base import db
from models.Settings import Settings
from models.Players import Players
from models.Rosters import Rosters
from views.api import api
from views.players import players
from views.rosters import rosters
from views.settings import settings
from views.slack import slack, file_upload, slack_message
from slackbot import Slack
from core import create_response


from config import Config

app = Flask(__name__)

# Publishing app context
with app.app_context():
    # Register blueprints
    DEFAULT_BLUEPRINTS = {api, players, rosters, settings, slack}
    for blueprint in DEFAULT_BLUEPRINTS:
        app.register_blueprint(blueprint)

    # Establish config variables
    config = Config()
    app.config.from_object(config)

    # Initialize database
    print("DB_URI: ", app.config["SQLALCHEMY_DATABASE_URI"])
    db.init_app(app)

    print("ROSTER DATA: ", app.config["ROSTER_DATA"])

    # Instantiating slackbot
    slackbot = Slack(app)
    slack_event_adapter = SlackEventAdapter(slackbot.secret, "/events", app)


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


# Slack event adapter for messages
@slack_event_adapter.on("message")
def handle_message(payload):
    print("MESSAGE RECIEVED: ", payload, flush=True)

    status, msg = slack_message(payload)

    return create_response(status=status, message=msg)


# Slack event adapter for file upload
@slack_event_adapter.on("file_shared")
def file_shared(payload):
    print("FILE FOUND", flush=True)

    status, msg = file_upload(payload)

    return create_response(status=status, message=msg)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)

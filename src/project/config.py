import os
import json

from dotenv import load_dotenv


basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    load_dotenv()
    if os.getenv("FLASK_ENV") == "production":
        # Adding extrac characters for new version of sqlalchemy
        SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite://").replace(
            "://", "ql://", 1
        )
    else:
        SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite://")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    STATIC_FOLDER = f"{os.getenv('APP_FOLDER')}/project/static"
    MEDIA_FOLDER = f"{os.getenv('APP_FOLDER')}/project/media"

    # Load slack variables
    BOT_TOKEN = f"{os.getenv('SLACK_BOT_TOKEN')}"
    USER_TOKEN = f"{os.getenv('SLACK_USER_TOKEN')}"
    SECRET = f"{os.getenv('SLACK_SECRET')}"
    ALERT_CHANNEL = f"{os.getenv('ALERT_CHANNEL')}"

    # Load json file
    ROSTER_FILE = f"{os.getenv('ROSTER_FILE')}"
    ROSTER_FILEPATH = MEDIA_FOLDER + "/" + ROSTER_FILE
    print("ROSTER FULL FILEPATH: ", ROSTER_FILEPATH, flush=True)
    try:
        with open(ROSTER_FILEPATH) as f:
            ROSTER_DATA = json.load(f)
    except Exception as e:
        ROSTER_DATA = {}

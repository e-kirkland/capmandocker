import os

from dotenv import load_dotenv


basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    load_dotenv()
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite://")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    STATIC_FOLDER = f"{os.getenv('APP_FOLDER')}/project/static"
    MEDIA_FOLDER = f"{os.getenv('APP_FOLDER')}/project/media"
    SLACK_BOT_TOKEN = f"{os.getenv('SLACK_BOT_TOKEN')}"
    SLACK_USER_TOKEN = f"{os.getenv('SLACK_USER_TOKEN')}"
    SLACK_SECRET = f"{os.getenv('SLACK_SECRET')}"
    ALERT_CHANNEL = f"{os.getenv('ALERT_CHANNEL')}"
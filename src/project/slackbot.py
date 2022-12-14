import os, sys
import json

import slack
from slackeventsapi import SlackEventAdapter
from dotenv import load_dotenv
import pandas as pd


class Slack:
    def __init__(self, app):
        load_dotenv()

        # Import slack credentials
        self.bot_token = f"{os.getenv('SLACK_BOT_TOKEN')}"
        self.user_token = f"{os.getenv('SLACK_USER_TOKEN')}"
        self.secret = f"{os.getenv('SLACK_SECRET')}"
        self.alert_channel = f"{os.getenv('ALERT_CHANNEL')}"

        # Instantiate slack client
        # self.slack_event_adapter = SlackEventAdapter(self.secret, "/slack/events", app)
        self.client = slack.WebClient(token=self.bot_token)

        # Check slack credentials
        self.BOT_ID = self.client.api_call("auth.test")["user_id"]

        # Load json file
        ROSTER_FILE = f"{os.getenv('ROSTER_FILE')}"
        MEDIA_FOLDER = f"{os.getenv('APP_FOLDER')}/project/media"
        ROSTER_FILEPATH = MEDIA_FOLDER + "/" + ROSTER_FILE
        try:
            with open(ROSTER_FILEPATH) as f:
                ROSTER_DATA = json.load(f)
        except Exception as e:
            ROSTER_DATA = {}

        # Get roster names/info
        self.roster_filepath = ROSTER_FILEPATH
        self.roster_data = ROSTER_DATA

        # Save media filepath
        self.media_folder = MEDIA_FOLDER

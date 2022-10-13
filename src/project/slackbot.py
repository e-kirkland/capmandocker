import os, sys

import slack
from slackeventsapi import SlackEventAdapter


class Slack:
    def __init__(self, app):
        # Check slack credentials
        self.bot_token = app.config["BOT_TOKEN"]
        self.user_token = app.config["USER_TOKEN"]
        self.secret = app.config["SECRET"]
        self.alert_channel = app.config["ALERT_CHANNEL"]
        print("TOKENS: ", self.bot_token)
        print("USER TOKEN: ", self.user_token)
        print("SECRET: ", self.secret)
        print("ALERT_CHANNEL: ", self.alert_channel)

        self.slack_event_adapter = SlackEventAdapter(self.secret, "/slack/events", app)
        self.client = slack.WebClient(token=self.bot_token)
        self.BOT_ID = self.client.api_call("auth.test")["user_id"]

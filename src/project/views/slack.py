from flask import Blueprint, request, jsonify
from flask import current_app as app
from slackeventsapi import SlackEventAdapter
from dotenv import load_dotenv

from slackbot import Slack
from core import create_response
from scripts import utils

slack = Blueprint("slack", __name__, url_prefix="/slack")

# Instantiating slackbot
slackbot = Slack(app)


@slack.route("/roster", methods=["GET", "POST"])
def get_roster():

    # Get data from request
    data = request.form
    print("DATA FROM FORM: ", data, flush=True)

    try:
        data.get("")
        print("DATA: ", data, flush=True)
    except AttributeError as e:
        return create_response(status=400, message="Must include form payload")

    if data.get("channel_id") is not None:
        channel_id = data.get("channel_id")
    else:
        return create_response(status=400, message="Form data must include channel_id")

    if data.get("user_id") is not None:
        user_id = data.get("user_id")
    else:
        return create_response(status=400, message="Form data must include user_id")

    if data.get("text") is not None:
        text = data.get("text")
    else:
        return create_response(status=400, message="Form data must include 'text' item")

    if slackbot.roster_data.get("lookupdict") is not None:
        lookupdict = slackbot.roster_data.get("lookupdict")
    else:
        return create_response(
            status=400,
            message="""No 'lookupdict' key/value in the league_users.json file.\n
                   Upload file at http://capman.fly.dev/upload""",
        )

    # If text is supplied, search for roster_id and supply information
    if len(text) != 0:
        roster_id = utils.get_roster_id(text, lookupdict)

    # If no text is supplied, search for username using user_id
    else:
        if slackbot.roster_data.get("rosters") is not None:
            roster_info = slackbot.roster_data.get("rosters")
        else:
            return create_response(
                status=400,
                message="""No 'rosters' key/value in the league_users.json file.\n
                    Upload file at http://capman.fly.dev/upload""",
            )

        team_info = roster_info[user_id]
        roster_id = team_info["roster_id"]

    slackbot.client.chat_postMessage(
        channel=channel_id, text=f"Retrieving the roster, just a moment..."
    )

    roster = utils.get_my_roster(roster_id)

    slackbot.client.chat_postMessage(
        channel=channel_id,
        text="",
        blocks=[{"type": "section", "text": {"type": "mrkdwn", "text": roster}}],
    )

    slackbot.client.chat_postMessage(
        channel=channel_id,
        text="",
        blocks=[
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"View all rosters here: <https://capmanbot.herokuapp.com/>",
                },
            }
        ],
    )

    return create_response(status=200)

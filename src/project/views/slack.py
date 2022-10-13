from flask import Blueprint, request, jsonify
from flask import current_app as app
from slackeventsapi import SlackEventAdapter
from dotenv import load_dotenv

from slackbot import Slack
from core import create_response
from scripts import utils
from scripts.league import init_league
from models.Settings import Settings

slack = Blueprint("slack", __name__, url_prefix="/slack")

# Instantiating slackbot
slackbot = Slack(app)


def parse_slack_payload(request, slackbot):

    # Get data from request
    data = request.form

    try:
        data.get("")
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

    if slackbot.roster_data.get("league_id") is not None:
        league_id = slackbot.roster_data.get("league_id")
    else:
        return create_response(
            status=400,
            message="""No 'league_id' key/value in the league_users.json file.\n
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

    return roster_id, channel_id, text, league_id


@slack.route("/roster", methods=["GET", "POST"])
def get_roster():

    # Parse info from slack payload
    roster_id, channel_id, _, _ = parse_slack_payload(request, slackbot)
    print("ROSTER_ID: ", roster_id, flush=True)
    print("CHANNEL_ID: ", channel_id, flush=True)

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


@slack.route("/cap", methods=["POST"])
def get_cap():

    # Parse info from slack payload
    roster_id, channel_id, _, _ = parse_slack_payload(request, slackbot)

    # Get cap info
    returnstring = utils.get_my_cap(roster_id, slackbot)

    slackbot.client.chat_postMessage(
        channel=channel_id,
        text="",
        blocks=[
            {"type": "section", "text": {"type": "mrkdwn", "text": str(returnstring)}}
        ],
    )
    slackbot.client.chat_postMessage(
        channel=channel_id,
        text="",
        blocks=[
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"View all cap spending here: <https://capmanbod.herokuapp.com/>",
                },
            }
        ],
    )

    return create_response(status=200)


@slack.route("/initialize", methods=["POST"])
def initialize_league():

    # Parse info from slack payload
    _, channel_id, text, _ = parse_slack_payload(request, slackbot)

    # Pull leagueID, salaryCap, rosterMin, rosterMax from text
    text_list = text.split(" ")
    leagueID = text_list[0]
    salaryCap = text_list[1]
    rosterMin = text_list[2]
    rosterMax = text_list[3]

    # Setting up league
    slackbot.client.chat_postMessage(
        channel=channel_id,
        text=f"Let's do this. Setting up your league with id {leagueID}...",
    )

    try:
        msg = init_league(leagueID, salaryCap, rosterMin, rosterMax)

        # Confirming league setup
        slackbot.client.chat_postMessage(
            channel=channel_id,
            text=f"Your league is set up. Now it's time to fill in salary info.",
        )

        return create_response(status=200, message="League successfully initialized!")

    except Exception as e:
        print("EXCEPTION: ", e, flush=True)

        return create_response(status=500, message=e)


@slack.route("/settings", methods=["POST"])
def update_settings():

    # Parse info from slack payload
    _, channel_id, text, league_id = parse_slack_payload(request, slackbot)

    # Pull salaryCap, rosterMin, rosterMax from text
    text_list = text.split(" ")
    salaryCap = text_list[0]
    rosterMin = text_list[1]
    rosterMax = text_list[2]

    # Check for league_id
    if not league_id:
        return create_response(status=400, message="Must include league_id as a param")

    # Pull setting and check if existing
    _settings = Settings.get_by_league_id(str(league_id))
    if not _settings:
        return create_response(
            status=400, message="league_id not found in settings table"
        )

    # Store new values
    if salaryCap is not None:
        _settings.salary_cap = int(salaryCap)
    if rosterMin is not None:
        _settings.roster_min = int(rosterMin)
    if rosterMax is not None:
        _settings.roster_max = int(rosterMax)

    # Upsert settings
    Settings.upsert_settings(_settings)

    msg = f"Successfully updated settings with league_id: {_settings.league_id}"
    settings_dict = _settings.to_dict()
    return create_response(status=200, message=msg, data=settings_dict)


@slack.route("/salary-reset", methods=["POST"])
def reset_salaries():

    # Parse info from slack payload
    _, channel_id, text, league_id = parse_slack_payload(request, slackbot)

    slackbot.client.chat_postMessage(
        channel=channel_id,
        text="Looks like you want to revise the league salaries. \nRetrieving league data for you to update, just a moment...",
    )

    salary_csv_filename = utils.get_salary_csv(slackbot)
    print("SALARY CSV FILENAME: ", salary_csv_filename, flush=True)

    response = slackbot.client.files_upload(
        channels=channel_id, file=salary_csv_filename, title="Current League Status"
    )
    print("RESPONSE: ", response, flush=True)

    slackbot.client.chat_postMessage(
        channel=channel_id,
        text="Here are the current player/roster/salary standings. Edit them and repost here to update the league.",
    )

    return create_response(status=200, message="Salaries pulled successfully.")

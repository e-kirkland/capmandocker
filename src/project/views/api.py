from flask import Blueprint, request, jsonify
from sqlalchemy import create_engine

from models.base import db
from models.Settings import Settings
from scripts.league import init_league
from scripts.sleeper import check_transaction
from core import create_response
from views.slack import get_league_id, slackbot
from scripts.utils import check_league_compliance

api = Blueprint("api", __name__, url_prefix="/api")


@api.route("/", methods=["GET"])
def test_api():
    return jsonify(msg="api is working")


@api.route("/setupLeague", methods=["GET", "POST"])
def setup_league():

    print("SETTING UP LEAGUE", flush=True)

    # Retrieving arguments, ensuring all are passed properly
    if request.args.get("leagueID") is not None:
        leagueID = request.args.get("leagueID")
    else:
        return create_response(status=400, message="Must include leagueID as a param")

    if request.args.get("salaryCap") is not None:
        salaryCap = request.args.get("salaryCap")
    else:
        return create_response(status=400, message="Must include leagueID as a param")

    if request.args.get("rosterMin") is not None:
        rosterMin = request.args.get("rosterMin")
    else:
        return create_response(status=400, message="Must include rosterMin as a param")

    if request.args.get("rosterMax") is not None:
        rosterMax = request.args.get("rosterMax")
    else:
        return create_response(status=400, message="Must include rosterMax as a param")

    print(f"SETTING LEAGUE ID AS {leagueID}", flush=True)

    msg = init_league(leagueID, salaryCap, rosterMin, rosterMax)

    return create_response(status=200, message="League successfully initialized!")


@api.route("/checkTransactions", methods=["GET"])
def check_transactions():
    print("Checking transactions!", flush=True)

    # Retrieving arguments, ensuring all are passed properly
    if request.args.get("leagueID") is not None:
        leagueID = request.args.get("leagueID")
    else:
        return create_response(status=400, message="Must include leagueID as a param")

    try:
        msg = check_transaction(leagueID)
        return create_response(status=200, message=msg)

    except Exception as e:
        print(f"CHECK TRANSACTION EXCEPTION: {e}", flush=True)
        return create_response(status=500, message=str(e))


@api.route("/checkCompliance", methods=["GET"])
def check_compliance():

    # Get settings from table
    league_id = get_league_id()
    if not league_id:
        return create_response(
            status=500, message="Could not parse league_id from league_users.json file"
        )
    _settings = Settings.get_by_league_id(league_id)
    cap = _settings.salary_cap
    rosterMin = _settings.roster_min
    rosterMax = _settings.roster_max

    # Update transactions
    result = check_transaction(league_id)

    # Check compliance
    compliance_result = check_league_compliance(cap, rosterMin, rosterMax)

    if compliance_result:
        for result in compliance_result:
            team_name = result[0]
            salary = result[1]
            count = result[2]
            slackbot.client.chat_postMessage(
                channel=slackbot.alert_channel,
                text=f"Team {team_name} is out of compliance!\nSalary: ${salary}\nRoster count: {count}",
            )

        return create_response(status=200, message="TEAMS NOTIFIED")
    else:
        return create_response(status=200, message="ALL TEAMS IN COMPLIANCE")

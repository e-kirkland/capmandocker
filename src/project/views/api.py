from flask import Blueprint, request, jsonify
from sqlalchemy import create_engine

from models.base import db
from scripts.league import init_league
from core import create_response

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
